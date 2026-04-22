from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import (
    JWTManager, create_access_token,
    verify_jwt_in_request, get_jwt_identity, decode_token
)
from werkzeug.security import generate_password_hash, check_password_hash
from fpdf import FPDF
# NOTE: MedicalRAGEngine is NOT imported here — it is lazy-loaded on first request
# so gunicorn can bind to $PORT before any heavy ML work begins.

# ── App setup ────────────────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

app.config['SECRET_KEY']                     = os.getenv("SECRET_KEY", "super-secret-key")
app.config['SQLALCHEMY_DATABASE_URI']        = 'sqlite:///medical_fact_checker.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY']                 = os.getenv("JWT_SECRET_KEY", "jwt-secret-key")

db  = SQLAlchemy(app)
jwt = JWTManager(app)

# ── Database models ───────────────────────────────────────────────────────────
class User(db.Model):
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    history       = db.relationship('FactCheckHistory', backref='user', lazy=True)

class FactCheckHistory(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    claim       = db.Column(db.Text, nullable=False)
    verdict     = db.Column(db.String(20), nullable=False)
    confidence  = db.Column(db.Integer)
    explanation = db.Column(db.Text)
    timestamp   = db.Column(db.DateTime, default=datetime.utcnow)
    report_path = db.Column(db.String(255))
    feedback    = db.Column(db.String(10), nullable=True)   # 'up' or 'down'

with app.app_context():
    db.create_all()
    # Auto-migrate: add feedback column for older databases
    with db.engine.connect() as conn:
        from sqlalchemy import text, inspect
        inspector = inspect(db.engine)
        existing_cols = [c['name'] for c in inspector.get_columns('fact_check_history')]
        if 'feedback' not in existing_cols:
            conn.execute(text("ALTER TABLE fact_check_history ADD COLUMN feedback VARCHAR(10)"))
            conn.commit()
            print("Migration: added 'feedback' column to fact_check_history.")

# ── Upload / report folders ───────────────────────────────────────────────────
UPLOAD_FOLDER = './uploads'
REPORT_FOLDER = './reports'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(REPORT_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['REPORT_FOLDER'] = REPORT_FOLDER

# ── Lazy RAG engine ───────────────────────────────────────────────────────────
_rag_engine = None

def get_rag_engine():
    """
    Return the shared MedicalRAGEngine, creating it only on the first call.
    Deferring the import means gunicorn binds $PORT before any heavy ML
    libraries (langchain, chromadb, fastembed) are loaded into RAM.
    """
    global _rag_engine
    if _rag_engine is None:
        from rag_engine import MedicalRAGEngine   # heavy import lives here
        _rag_engine = MedicalRAGEngine()
    return _rag_engine

# ── Auth helper ───────────────────────────────────────────────────────────────
def _optional_user_id():
    """Extract user_id from a JWT Bearer token; return None if absent/invalid."""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None
    try:
        token   = auth_header.split(' ', 1)[1]
        decoded = decode_token(token)
        return decoded.get('sub')
    except Exception:
        return None

# ── Lightweight health-check (no RAG engine involved) ────────────────────────
@app.route('/api/ping', methods=['GET'])
def ping():
    return jsonify({"status": "ok"}), 200

# ── Auth routes ───────────────────────────────────────────────────────────────
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    if User.query.filter_by(username=data['username']).first():
        return jsonify({"error": "User already exists"}), 400
    new_user = User(
        username      = data['username'],
        password_hash = generate_password_hash(data['password'], method='pbkdf2:sha256')
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "User registered successfully"}), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()
    if user and check_password_hash(user.password_hash, data['password']):
        access_token = create_access_token(identity=str(user.id))
        return jsonify(access_token=access_token, username=user.username), 200
    return jsonify({"error": "Invalid credentials"}), 401

# ── Feature routes ────────────────────────────────────────────────────────────
@app.route('/api/upload-document', methods=['POST'])
def upload_document():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and file.filename.endswith('.pdf'):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        user_id          = _optional_user_id()   # fixed: was undefined in old code
        chunks_processed = get_rag_engine().process_document(filepath, user_id=user_id)
        return jsonify({"message": "Document indexed", "chunks": chunks_processed, "filename": filename})
    return jsonify({"error": "Only PDFs allowed"}), 400


@app.route('/api/fact-check', methods=['POST'])
def fact_check():
    data    = request.get_json()
    claim   = data.get('claim')
    user_id = _optional_user_id()

    result = get_rag_engine().verify_claim(claim, user_id=user_id)

    if "error" not in result:
        history_entry = FactCheckHistory(
            user_id     = user_id,
            claim       = claim,
            verdict     = result.get('status'),
            confidence  = result.get('confidence'),
            explanation = result.get('explanation')
        )
        db.session.add(history_entry)
        db.session.commit()
        result['id'] = history_entry.id

    return jsonify(result)


@app.route('/api/analyze-image', methods=['POST'])
def analyze_image():
    if 'image' not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    image    = request.files['image']
    query    = request.form.get('query', 'Analyze this medical report.')
    filename = secure_filename(f"{uuid.uuid4()}_{image.filename}")
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    image.save(filepath)

    result = get_rag_engine().analyze_medical_image(filepath, query)
    return jsonify(result)


@app.route('/api/batch-check', methods=['POST'])
def batch_check():
    data   = request.get_json()
    claims = data.get('claims', [])
    if not claims:
        return jsonify({"error": "No claims provided"}), 400
    results = get_rag_engine().batch_verify(claims)
    return jsonify({"results": results})


@app.route('/api/stats', methods=['GET'])
def get_stats():
    from sqlalchemy.sql import func
    total_checks     = FactCheckHistory.query.count()
    true_count       = FactCheckHistory.query.filter_by(verdict='TRUE').count()
    false_count      = FactCheckHistory.query.filter_by(verdict='FALSE').count()
    unverified_count = FactCheckHistory.query.filter_by(verdict='UNVERIFIED').count()
    avg_conf_result  = db.session.query(
        func.avg(FactCheckHistory.confidence).label('average')
    ).first()
    avg_conf  = round(avg_conf_result.average, 1) if avg_conf_result.average is not None else 0
    kb_stats  = get_rag_engine().get_kb_stats()

    return jsonify({
        "total_checks":    total_checks,
        "true_count":      true_count,
        "false_count":     false_count,
        "unverified_count": unverified_count,
        "avg_confidence":  avg_conf,
        "kb_size":         kb_stats.get('total_chunks', 0)
    })


@app.route('/api/kb-status', methods=['GET'])
def kb_status():
    return jsonify(get_rag_engine().get_kb_stats())


@app.route('/api/history', methods=['GET'])
def get_history():
    try:
        verify_jwt_in_request()
        user_id = get_jwt_identity()
    except Exception:
        return jsonify([]), 200

    history = (FactCheckHistory.query
               .filter_by(user_id=user_id)
               .order_by(FactCheckHistory.timestamp.desc())
               .limit(10).all())
    return jsonify([{
        "id":         h.id,
        "claim":      h.claim,
        "verdict":    h.verdict,
        "confidence": h.confidence,
        "timestamp":  h.timestamp.isoformat()
    } for h in history])


@app.route('/api/download-report/<int:check_id>', methods=['GET'])
def download_report(check_id):
    entry = db.session.get(FactCheckHistory, check_id)
    if entry is None:
        return jsonify({"error": "Report not found"}), 404

    from fpdf import FPDF, XPos, YPos
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", 'B', 16)
    pdf.cell(200, 10, text="Medical Fact-Check Report",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.set_font("Helvetica", size=12)
    pdf.ln(10)
    pdf.cell(200, 10, text=f"Claim: {entry.claim}",            new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(200, 10, text=f"Verdict: {entry.verdict}",        new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(200, 10, text=f"Confidence: {entry.confidence}%", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(5)
    pdf.multi_cell(0, 10, text=f"Explanation: {entry.explanation or 'N/A'}")
    pdf.ln(5)
    pdf.cell(200, 10, text=f"Generated on: {entry.timestamp}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    report_filename = f"report_{check_id}.pdf"
    report_path     = os.path.join(app.config['REPORT_FOLDER'], report_filename)
    pdf.output(report_path)
    return send_file(report_path, as_attachment=True)


@app.route('/api/feedback/<int:check_id>', methods=['POST'])
def submit_feedback(check_id):
    data   = request.get_json()
    rating = data.get('rating')
    if rating not in ('up', 'down'):
        return jsonify({"error": "rating must be 'up' or 'down'"}), 400

    entry = db.session.get(FactCheckHistory, check_id)
    if entry is None:
        return jsonify({"error": "Entry not found"}), 404

    entry.feedback = rating
    db.session.commit()
    return jsonify({"message": f"Feedback '{rating}' recorded for entry {check_id}."})


@app.route('/api/health-feed', methods=['GET'])
def health_feed():
    """WHO/CDC live feed — returns latest public health advisories via RSS."""
    import feedparser
    import socket
    socket.setdefaulttimeout(5)   # 5 s cap per feed so we don't hang
    feeds = [
        ("CDC", "https://tools.cdc.gov/api/v2/resources/media/316422.rss"),
        ("WHO", "https://www.who.int/rss-feeds/news-releases.xml"),
    ]
    articles = []
    for source, url in feeds:
        try:
            feed = feedparser.parse(url)
            for item in feed.entries[:4]:
                articles.append({
                    "source":    source,
                    "title":     item.get("title", ""),
                    "link":      item.get("link",  ""),
                    "published": item.get("published", ""),
                    "summary":   item.get("summary", "")[:200]
                })
        except Exception as e:
            print(f"Feed error ({source}): {e}")
    return jsonify({"articles": articles[:8]})


if __name__ == '__main__':
    app.run(debug=True, port=5001)
