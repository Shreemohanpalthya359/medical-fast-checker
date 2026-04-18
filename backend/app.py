from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename
from rag_engine import MedicalRAGEngine

app = Flask(__name__)
# Enable CORS for the frontend React app running on port 5173
CORS(app, resources={r"/api/*": {"origins": "*"}})

UPLOAD_FOLDER = './uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initialize the RAG engine
# It will load the Chroma database if it already exists, or create an empty one
print("Initializing RAG Engine...")
rag_engine = MedicalRAGEngine()
print("RAG Engine initialized.")

@app.route('/api/status', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "message": "Medical Fact-Checker API is running."})

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
        
        try:
            chunks_processed = rag_engine.process_document(filepath)
            return jsonify({
                "message": "Document successfully vectorized and added to the medical knowledge base.",
                "chunks_added": chunks_processed,
                "filename": filename
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "Only PDF files are supported."}), 400

@app.route('/api/fact-check', methods=['POST'])
def fact_check():
    data = request.get_json()
    if not data or 'claim' not in data:
        return jsonify({"error": "Missing 'claim' in request body"}), 400
    
    claim = data['claim']
    try:
        result = rag_engine.verify_claim(claim)
        # Check if the result has an error (like missing API key)
        if "error" in result:
            return jsonify(result), 500
            
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
