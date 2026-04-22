import os
import json
import uuid
import base64
import time
from langchain_chroma import Chroma
from langchain_groq import ChatGroq
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document
from dotenv import load_dotenv
from Bio import Entrez

load_dotenv() # Load env variables

# 30+ curated medical facts to pre-seed the knowledge base
SEED_MEDICAL_FACTS = [
    ("Aspirin inhibits COX-1 and COX-2 enzymes, reducing prostaglandin synthesis. It is used as an antiplatelet agent to prevent myocardial infarction and stroke.", "pharmacology"),
    ("Normal adult blood pressure is below 120/80 mmHg. Hypertension is diagnosed when systolic BP ≥ 130 mmHg or diastolic BP ≥ 80 mmHg on multiple readings.", "cardiology"),
    ("Insulin is produced by beta cells of the islets of Langerhans in the pancreas. Type 1 diabetes involves autoimmune destruction of these beta cells.", "endocrinology"),
    ("Penicillin works by inhibiting bacterial cell wall synthesis by binding to PBPs (penicillin-binding proteins), causing bacterial lysis.", "microbiology"),
    ("The normal adult resting heart rate is 60-100 beats per minute. A heart rate below 60 is called bradycardia; above 100 is tachycardia.", "cardiology"),
    ("Statins (e.g., atorvastatin, rosuvastatin) lower LDL cholesterol by inhibiting HMG-CoA reductase, the rate-limiting enzyme in cholesterol synthesis.", "pharmacology"),
    ("Normal fasting blood glucose is 70-99 mg/dL. Prediabetes is 100-125 mg/dL. Diabetes mellitus is diagnosed at ≥ 126 mg/dL on two fasting tests.", "endocrinology"),
    ("Metformin is the first-line drug for Type 2 Diabetes. It works by reducing hepatic glucose production and improving insulin sensitivity.", "pharmacology"),
    ("COVID-19 is caused by SARS-CoV-2, a beta-coronavirus. It primarily infects the respiratory tract via ACE2 receptor binding.", "infectious_disease"),
    ("The mRNA COVID-19 vaccines (Pfizer-BioNTech, Moderna) contain lipid nanoparticles encapsulating mRNA encoding the spike protein. They do NOT alter human DNA.", "immunology"),
    ("Antibiotics are ineffective against viral infections. Viral diseases like the common cold, influenza, and COVID-19 require antiviral treatments, not antibiotics.", "pharmacology"),
    ("Acetaminophen (paracetamol) is metabolized in the liver. Overdose causes acute hepatic necrosis due to accumulation of the toxic metabolite NAPQI.", "pharmacology"),
    ("The human immune system has two branches: innate immunity (non-specific, fast) and adaptive immunity (specific, slower, involves T and B lymphocytes).", "immunology"),
    ("Body Mass Index (BMI) is calculated as weight (kg) / height (m²). BMI 18.5-24.9 is normal; 25-29.9 is overweight; ≥30 is obese.", "nutrition"),
    ("Myocardial infarction (heart attack) occurs when coronary artery blood flow is blocked, usually by plaque rupture and thrombus formation.", "cardiology"),
    ("The brain consumes approximately 20% of the body's oxygen and glucose despite being only 2% of body weight.", "neurology"),
    ("Cancer is caused by uncontrolled cell division due to mutations in proto-oncogenes (gain of function) and tumor suppressor genes (loss of function).", "oncology"),
    ("Alzheimer's disease is characterized by amyloid-beta plaques and neurofibrillary tangles (tau protein). It is the most common form of dementia.", "neurology"),
    ("Depression involves dysregulation of serotonin, norepinephrine, and dopamine neurotransmitters. SSRIs are the first-line pharmacological treatment.", "psychiatry"),
    ("Sleep requirement for adults is 7-9 hours per night. Chronic sleep deprivation increases risk of obesity, diabetes, cardiovascular disease, and impaired immunity.", "general_medicine"),
    ("Vitamin D is synthesized in the skin upon exposure to UVB radiation. Deficiency causes rickets in children and osteomalacia in adults.", "nutrition"),
    ("Anemia is defined as hemoglobin < 12 g/dL in women and < 13 g/dL in men. Iron deficiency anemia is the most common type worldwide.", "hematology"),
    ("MRSA (Methicillin-resistant Staphylococcus aureus) is resistant to beta-lactam antibiotics due to altered penicillin-binding proteins (PBP2a).", "microbiology"),
    ("Stroke is either ischemic (87%, due to blood clot) or hemorrhagic (13%, due to bleeding). Time-critical treatment: tPA within 4.5 hours for ischemic stroke.", "neurology"),
    ("The MMR vaccine (Measles, Mumps, Rubella) is a live attenuated vaccine. It does NOT cause autism — this claim was based on a fraudulent, retracted study.", "immunology"),
    ("Normal SpO2 (blood oxygen saturation) is 95-100%. Levels below 90% indicate hypoxemia and may require supplemental oxygen.", "pulmonology"),
    ("Asthma is a chronic inflammatory airway disease causing reversible bronchoconstriction. Beta-2 agonists (e.g., salbutamol) are bronchodilator treatments.", "pulmonology"),
    ("The hepatitis B vaccine is the first anti-cancer vaccine — hepatitis B is a major cause of hepatocellular carcinoma.", "oncology"),
    ("Opioids (morphine, codeine, fentanyl) act on mu, delta, and kappa opioid receptors in the CNS to produce analgesia. They are highly addictive.", "pharmacology"),
    ("Ibuprofen is an NSAID that inhibits both COX-1 and COX-2. Contraindicated in patients with peptic ulcers, renal disease, and third-trimester pregnancy.", "pharmacology"),
    ("The World Health Organization defines health as 'a state of complete physical, mental and social well-being, not merely the absence of disease.'", "general_medicine"),
    ("Sepsis is a life-threatening organ dysfunction caused by dysregulated host response to infection. Septic shock has mortality > 40%.", "infectious_disease"),
    ("Cholesterol is not inherently bad — it is essential for cell membrane structure, bile acid synthesis, and steroid hormone production.", "nutrition"),
    ("ECG (electrocardiogram) measures the electrical activity of the heart. A normal PR interval is 120-200 ms; QRS duration < 120 ms.", "cardiology"),
]


class MedicalRAGEngine:
    def __init__(self, persist_directory="./chroma_db"):
        self.persist_directory = persist_directory
        self.model_name = "llama-3.1-8b-instant"

        # FastEmbed: ONNX-optimized embeddings, ~90MB RAM (vs ~400MB for sentence-transformers)
        self.embeddings = FastEmbedEmbeddings(model_name="BAAI/bge-small-en-v1.5")
        self.init_vectorstore()

        # Seed KB if empty
        self._seed_knowledge_base_if_empty()

        # Initialize Groq LLM for text analysis
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key or api_key == "your_groq_api_key_here":
            print("WARNING: GROQ_API_KEY not found in .env!")
            self.llm = None
        else:
            self.llm = ChatGroq(temperature=0, model_name=self.model_name, api_key=api_key)

        # Configure Entrez for PubMed
        Entrez.email = os.getenv("PUBMED_EMAIL", "example@example.com")

        self.setup_prompts()

    def init_vectorstore(self):
        self.vectorstore = Chroma(
            collection_name="medical_knowledge",
            embedding_function=self.embeddings,
            persist_directory=self.persist_directory
        )
        # Separate collection used exclusively for the claim similarity cache
        self.claim_cache = Chroma(
            collection_name="claim_cache",
            embedding_function=self.embeddings,
            persist_directory=self.persist_directory
        )

    def _seed_knowledge_base_if_empty(self):
        """Pre-seed the vector DB with curated medical facts if the collection is empty."""
        try:
            count = self.vectorstore._collection.count()
            if count == 0:
                print("Seeding knowledge base with curated medical facts...")
                docs = []
                for fact_text, topic in SEED_MEDICAL_FACTS:
                    docs.append(Document(
                        page_content=fact_text,
                        metadata={"source": "Medical Knowledge Base", "topic": topic, "type": "seed"}
                    ))
                splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
                splits = splitter.split_documents(docs)
                self.vectorstore.add_documents(splits)
                print(f"Knowledge base seeded with {len(splits)} chunks from {len(SEED_MEDICAL_FACTS)} medical facts.")
            else:
                print(f"Knowledge base loaded: {count} chunks already indexed.")
        except Exception as e:
            print(f"Seeding error: {e}")

    def get_kb_stats(self):
        """Returns vector store statistics."""
        try:
            count = self.vectorstore._collection.count()
            # Get topic distribution
            results = self.vectorstore._collection.get(include=["metadatas"])
            topics = {}
            sources = set()
            for meta in results.get("metadatas", []):
                if meta:
                    topic = meta.get("topic", "general")
                    topics[topic] = topics.get(topic, 0) + 1
                    src = meta.get("source", "Unknown")
                    sources.add(src)
            return {
                "total_chunks": count,
                "total_documents": len(sources),
                "topic_distribution": topics,
                "sources": list(sources)[:10]
            }
        except Exception as e:
            return {"total_chunks": 0, "total_documents": 0, "topic_distribution": {}, "sources": [], "error": str(e)}

    def setup_prompts(self):
        template = """\
You are Aegis, an expert medical fact-checker AI trained on clinical literature. \
You receive either a CLAIM to verify OR a QUESTION about medicine.

Document Context (from curated medical knowledge base):
{doc_context}

PubMed Live Evidence:
{live_context}

Input: {claim}

INSTRUCTIONS:
1. If the input is a CLAIM (e.g. "Aspirin reduces fever"), verify it rigorously.
2. If the input is a QUESTION or topic (e.g. "tell me about aspirin"), set status UNVERIFIED and explain comprehensively.
3. ALWAYS respond with ONLY a valid JSON object. No markdown, no code fences, no preamble.

CONFIDENCE CALIBRATION RULES (follow strictly):
- 90-100: Multiple strong sources confirm the claim. Well-established medical consensus.
- 75-89:  Good evidence from at least one source. Mainstream medical position.
- 60-74:  Some supporting evidence but with caveats or nuance required.
- 40-59:  Insufficient or conflicting evidence. Cannot confirm or deny clearly.
- 0-39:   Evidence contradicts the claim or claim is clearly false/misleading.

Required JSON keys:
- "status": "TRUE", "FALSE", or "UNVERIFIED"
- "confidence": integer 0-100 (calibrate per rules above, do NOT default to 50)
- "explanation": 3-5 sentences — be specific, cite mechanisms, mention key studies if available
- "sources": [list of short reference strings, include PubMed IDs if found]
- "glossary": {{"term": "plain-english definition"}} (include 2-4 key medical terms)
- "consensus_match": true if your verdict aligns with mainstream medical consensus, else false
- "medical_category": e.g. "Pharmacology", "Cardiology", "Immunology"
- "precautions": [list of 2-4 important clinical caveats or warnings related to the claim]
"""
        self.fact_check_prompt = PromptTemplate(
            template=template,
            input_variables=["doc_context", "live_context", "claim"]
        )

    def search_pubmed(self, query):
        """Fetches top 2 PubMed abstracts to provide richer evidence context."""
        try:
            handle = Entrez.esearch(db="pubmed", term=query, retmax=2)
            record = Entrez.read(handle)
            handle.close()
            ids = record["IdList"]
            if not ids:
                return "No recent publications found."
            combined = []
            for pmid in ids[:2]:
                handle = Entrez.efetch(db="pubmed", id=pmid, rettype="abstract", retmode="text")
                abstract = handle.read()
                handle.close()
                combined.append(abstract[:600])  # 600 chars each → 1200 max, safe for Groq free tier
            return "\n---\n".join(combined)
        except Exception as e:
            return f"PubMed error: {str(e)[:100]}"

    def analyze_medical_image(self, file_path, user_query=None):
        """Analyzes medical images or PDF reports using Groq models."""
        user_q = user_query.strip() if user_query else None

        # Build a query-aware prompt that directly answers what the user asked
        if user_q:
            query_instruction = f"""
            The user specifically asked: "{user_q}"
            Make sure your 'analysis' field DIRECTLY and FULLY answers this question using the report data.
            If the user asked for food recommendations, list specific foods.
            If the user asked for remedies/medications, list them with dosages if available.
            If the user asked for lifestyle advice, provide detailed actionable steps.
            """
        else:
            query_instruction = "Provide a comprehensive general analysis of the findings."

        prompt = f"""
        You are an expert clinical AI assistant. Analyze the medical document provided.

        Your tasks:
        1. Identify the document type (e.g., Lab Report, Radiology, Consultation Note).
        2. Extract ALL abnormal values, symptoms, and clinical findings.
        3. {query_instruction}
        4. List actionable PRECAUTIONS and recommended next steps.
        5. Provide a confidence score (integer 0-100) reflecting how certain you are.

        Respond ONLY with a valid JSON object using EXACTLY these keys:
        {{
          "analysis": "<direct, detailed answer to the user query based on the report>",
          "symptoms_detected": ["<symptom 1>", "<symptom 2>"],
          "precautions": ["<step 1>", "<step 2>"],
          "confidence": <integer 0-100>,
          "glossary": {{"<medical_term>": "<plain English meaning>"}}
        }}
        """

        ext = os.path.splitext(file_path)[1].lower()

        # Branch 1: PDF Report Analysis (Uses Groq Text Model)
        if ext == '.pdf':
            if not self.llm:
                return {"error": "Groq API key is not configured for PDF analysis."}
            try:
                from langchain_community.document_loaders import PyPDFLoader
                loader = PyPDFLoader(file_path)
                docs = loader.load()
                report_text = "\n".join([d.page_content for d in docs])[:6000]

                from langchain_core.prompts import PromptTemplate
                pdf_prompt = PromptTemplate(
                    template="""You are a clinical AI assistant. Here is a medical report:

{text}

{instructions}""",
                    input_variables=["text", "instructions"]
                )

                pdf_chain = pdf_prompt | self.llm
                response = pdf_chain.invoke({"text": report_text, "instructions": prompt})
                content = response.content.strip()
                print(f"PDF LLM raw response (first 400 chars): {content[:400]}")

                # Robust JSON extraction
                if "```json" in content:
                    content = content.split("```json")[-1].split("```")[0].strip()
                elif "```" in content:
                    parts = content.split("```")
                    for part in parts:
                        if part.strip().startswith("{"):
                            content = part.strip()
                            break
                if "{" in content and "}" in content:
                    content = content[content.find("{"):content.rfind("}") + 1]

                res = json.loads(content)

                # Normalize confidence: if 0-1 float, convert to 0-100 int
                raw_conf = res.get('confidence', 75)
                if isinstance(raw_conf, float) and raw_conf <= 1.0:
                    res['confidence'] = int(raw_conf * 100)
                else:
                    res['confidence'] = int(raw_conf)

                # Flatten nested analysis dict if needed
                if isinstance(res.get('analysis'), dict):
                    flat_analysis = []
                    for k, v in res['analysis'].items():
                        if isinstance(v, list): v = ", ".join(str(i) for i in v)
                        flat_analysis.append(f"{k.replace('_', ' ').title()}: {v}")
                    res['analysis'] = "\n".join(flat_analysis)

                return res
            except Exception as e:
                raw = locals().get('content', '')
                return {"analysis": raw if raw else f"Failed to parse PDF: {str(e)}", "confidence": 0, "symptoms_detected": [], "precautions": [], "glossary": {}}

        # Branch 2: Image Analysis (Uses Groq Vision)
        if not self.llm:
            return {"error": "Groq API key is not configured for image analysis."}

        try:
            from langchain_core.messages import HumanMessage
            from langchain_groq import ChatGroq
            import base64

            with open(file_path, "rb") as f:
                raw_bytes = f.read()
            base64_image = base64.b64encode(raw_bytes).decode('utf-8')

            # Detect correct MIME type from file extension
            mime_map = {'.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png',
                        '.gif': 'image/gif', '.webp': 'image/webp'}
            mime_type = mime_map.get(ext, 'image/jpeg')

            api_key = os.getenv("GROQ_API_KEY")
            vision_llm = ChatGroq(
                temperature=0,
                model_name="meta-llama/llama-4-scout-17b-16e-instruct",
                api_key=api_key
            )
            message = HumanMessage(content=[
                {"type": "text", "text": prompt + "\nRespond with ONLY a valid JSON object. No markdown, no explanations, no code fences."},
                {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{base64_image}"}},
            ])
            response = vision_llm.invoke([message])
            content = response.content.strip()
            raw_content = content  # Keep original for fallback

            print(f"Vision LLM raw response (first 300 chars): {content[:300]}")

            # Robust JSON extraction
            def extract_json(text):
                """Try multiple strategies to extract a JSON object from text."""
                if not text:
                    return None
                # Strategy 1: ```json ... ``` fence
                if "```json" in text:
                    text = text.split("```json")[-1].split("```")[0].strip()
                # Strategy 2: plain ``` fence
                elif "```" in text:
                    parts = text.split("```")
                    # Find the part that looks like JSON
                    for part in parts:
                        part = part.strip()
                        if part.startswith("{"):
                            text = part
                            break
                # Strategy 3: extract from first { to last }
                if "{" in text and "}" in text:
                    text = text[text.find("{"):text.rfind("}") + 1]
                try:
                    return json.loads(text)
                except (json.JSONDecodeError, ValueError):
                    return None

            res = extract_json(content)

            if res is None:
                # JSON parsing failed — return the raw LLM text as a
                # human-readable analysis instead of an error
                print("Vision model returned non-JSON response — using raw text as analysis.")
                return {
                    "analysis": raw_content if raw_content else "The vision model returned an empty response. Please try again.",
                    "confidence": 50,
                    "symptoms_detected": [],
                    "precautions": ["Consult a medical professional for a formal analysis."],
                    "glossary": {}
                }

            # Flatten nested analysis dict if model returned one
            if isinstance(res.get('analysis'), dict):
                flat_analysis = []
                for k, v in res['analysis'].items():
                    if isinstance(v, list): v = ", ".join(str(i) for i in v)
                    flat_analysis.append(f"{k.replace('_', ' ').title()}: {v}")
                res['analysis'] = "\n".join(flat_analysis)

            # Normalize confidence: if 0-1 float, convert to 0-100 int
            raw_conf = res.get('confidence', 75)
            if isinstance(raw_conf, float) and raw_conf <= 1.0:
                res['confidence'] = int(raw_conf * 100)
            else:
                res['confidence'] = int(raw_conf)

            return res

        except Exception as e:
            err_str = str(e)
            print(f"Groq Vision Error: {err_str}")

            if "429" in err_str or "rate_limit" in err_str.lower():
                return {"analysis": "⚠️ Groq API Rate Limit reached.\nPlease wait a moment and try again.", "confidence": 0, "symptoms_detected": [], "precautions": [], "glossary": {}}

            if "invalid_api_key" in err_str.lower() or "authentication" in err_str.lower():
                return {"analysis": "⚠️ Invalid Groq API Key. Please check your .env file.", "confidence": 0, "symptoms_detected": [], "precautions": [], "glossary": {}}

            return {
                "analysis": f"Image analysis failed. Please ensure the image is a valid medical scan (JPG/PNG) and try again.\n\nTechnical detail: {err_str[:300]}",
                "confidence": 0,
                "symptoms_detected": [],
                "precautions": [],
                "glossary": {}
            }

    def process_document(self, file_path, user_id=None):
        """Index a PDF into the vector store, tagging each chunk with the uploader's user_id."""
        loader = PyPDFLoader(file_path)
        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
        splits = text_splitter.split_documents(documents)
        # Stamp every chunk with user_id so searches can be scoped per user
        if user_id:
            for doc in splits:
                doc.metadata["user_id"] = str(user_id)
        self.vectorstore.add_documents(splits)
        return len(splits)

    def _cache_lookup(self, claim, threshold=0.95):
        """Return a cached result if a near-identical claim exists (similarity >= threshold)."""
        try:
            count = self.claim_cache._collection.count()
            if count == 0:
                return None
            hits = self.claim_cache.similarity_search_with_score(claim, k=1)
            if not hits:
                return None
            doc, score = hits[0]
            similarity = max(0.0, 1.0 - score / 2.0)
            if similarity >= threshold:
                cached = json.loads(doc.page_content)
                cached["from_cache"] = True
                cached["cache_similarity"] = round(similarity, 3)
                cached["processing_time_ms"] = 0
                print(f"Cache HIT ({similarity:.1%}) for: '{claim[:60]}'")
                return cached
        except Exception as e:
            print(f"Cache lookup error: {e}")
        return None

    def _cache_store(self, claim, result):
        """Persist a successful verification result into the claim cache collection."""
        try:
            payload = json.dumps(result, default=str)
            self.claim_cache.add_documents([Document(
                page_content=payload,
                metadata={"claim": claim[:500]}
            )])
        except Exception as e:
            print(f"Cache store error: {e}")

    def verify_claim(self, claim, user_id=None):
        """
        Full RAG pipeline: Claim Cache → Vector Search → PubMed → LLM Synthesis.
        Returns result enriched with similarity scores, processing time, and model metadata.
        Supports user-scoped vector search when user_id is provided.
        """
        if not self.llm:
            return {"error": "Groq API key is not configured."}

        # ── Feature 1: Claim Similarity Cache ─────────────────────────────────
        cached = self._cache_lookup(claim)
        if cached:
            return cached

        t_start = time.time()

        # ── Feature 2: Personal KB – filter by user_id if provided ────────────
        # Step 1: Vector Search – k=5 for richer context (snippets capped at 300 chars each)
        if user_id:
            try:
                user_results  = self.vectorstore.similarity_search_with_score(
                    claim, k=3, filter={"user_id": str(user_id)}
                )
                seed_results  = self.vectorstore.similarity_search_with_score(
                    claim, k=3, filter={"type": "seed"}
                )
                seen  = set()
                vector_results = []
                for item in user_results + seed_results:
                    key = item[0].page_content[:100]
                    if key not in seen:
                        seen.add(key)
                        vector_results.append(item)
                vector_results = vector_results[:5]
            except Exception:
                vector_results = self.vectorstore.similarity_search_with_score(claim, k=5)
        else:
            vector_results = self.vectorstore.similarity_search_with_score(claim, k=5)

        doc_context_parts = []
        sources_metadata  = []
        similarity_scores = []

        for doc, score in vector_results:
            similarity = round(max(0.0, 1.0 - score / 2.0), 3)
            similarity_scores.append(similarity)
            snippet = doc.page_content[:300]
            doc_context_parts.append(
                f"[{doc.metadata.get('topic', 'general')} | {similarity:.0%}]: {snippet}"
            )
            sources_metadata.append({
                "file":       doc.metadata.get("source", "Unknown").split("/")[-1],
                "page":       doc.metadata.get("page", 0) + 1,
                "topic":      doc.metadata.get("topic", "general"),
                "similarity": similarity,
                "snippet":    snippet + "..."
            })

        doc_context = "\n\n".join(doc_context_parts)
        t_vector = time.time()

        # Step 2: PubMed Live Consensus
        live_context = self.search_pubmed(claim)
        t_pubmed = time.time()

        # Step 3: LLM Synthesis
        chain = self.fact_check_prompt | self.llm
        response = chain.invoke({
            "doc_context": doc_context,
            "live_context": live_context,
            "claim": claim
        })
        t_llm = time.time()

        total_ms  = round((t_llm - t_start)    * 1000)
        vector_ms = round((t_vector - t_start)  * 1000)
        pubmed_ms = round((t_pubmed - t_vector)  * 1000)
        llm_ms    = round((t_llm - t_pubmed)     * 1000)

        try:
            content = response.content.strip()
            if "```json" in content:
                content = content.split("```json")[-1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].strip()
            if "{" in content and "}" in content:
                content = content[content.find("{"):content.rfind("}") + 1]
            result = json.loads(content)

        except (json.JSONDecodeError, ValueError):
            raw_text = response.content.strip()
            print(f"[verify_claim] JSON parse failed - fallback. First 200 chars: {raw_text[:200]}")
            result = {
                "status":           "UNVERIFIED",
                "confidence":       50,
                "explanation":      raw_text[:1500] if raw_text else "Unexpected response. Try rephrasing as a direct medical claim.",
                "sources":          [],
                "glossary":         {},
                "consensus_match":  False,
                "medical_category": "General Medicine",
            }

        except Exception as e:
            return {
                "error":               "Parsing failed",
                "raw":                 response.content,
                "processing_time_ms": total_ms
            }

        # ── Post-processing: Confidence Calibration ───────────────────────────
        raw_confidence  = int(result.get("confidence", 50))
        avg_similarity  = round(sum(similarity_scores) / len(similarity_scores), 3) if similarity_scores else 0
        has_pubmed      = "No recent" not in live_context and "PubMed error" not in live_context
        has_explanation = len(result.get("explanation", "")) > 80
        status          = result.get("status", "UNVERIFIED")

        boost = 0
        if avg_similarity >= 0.75:    boost += 12   # Strong vector match from KB
        elif avg_similarity >= 0.55:  boost += 8    # Moderate vector match
        elif avg_similarity >= 0.35:  boost += 4    # Weak but relevant match
        if has_pubmed:                boost += 10   # PubMed evidence present
        if len(similarity_scores) >= 4: boost += 5  # Multiple corroborating sources

        # Apply boost with sensible minimums based on status + evidence quality
        if status == "TRUE":
            # TRUE claims: always at least 75% when PubMed agrees, 70% otherwise
            floor = 78 if has_pubmed else 70
            calibrated = min(97, max(raw_confidence + boost, floor))

        elif status == "FALSE":
            # FALSE claims: always at least 70% when evidence refutes
            floor = 72 if has_pubmed else 65
            calibrated = min(95, max(raw_confidence + boost, floor))

        else:  # UNVERIFIED (includes open questions like "what is X")
            # Questions/topics: if we gave a good explanation with evidence, show at least 55%
            if has_explanation and has_pubmed:
                floor = 58   # We answered well with real PubMed data
            elif has_explanation and avg_similarity >= 0.40:
                floor = 52   # We answered well using KB data
            else:
                floor = 45   # Minimal data, some uncertainty is honest
            calibrated = min(85, max(raw_confidence + boost, floor))

        result["confidence"]      = calibrated
        result["confidence_raw"]  = raw_confidence   # keep original for transparency
        result["avg_similarity"]  = avg_similarity
        result["pubmed_found"]    = has_pubmed
        # ── End calibration ───────────────────────────────────────────────────

        # Shared enrichment block - runs for both JSON success and fallback
        result["detailed_sources"]   = sources_metadata
        result["similarity_scores"]  = similarity_scores
        result["vector_hits"]        = len(vector_results)
        result["model_used"]         = self.model_name
        result["processing_time_ms"] = total_ms
        result["from_cache"]         = False
        result["pipeline_breakdown"] = {
            "vector_search_ms": vector_ms,
            "pubmed_ms":        pubmed_ms,
            "llm_synthesis_ms": llm_ms
        }
        self._cache_store(claim, result)
        return result

    def batch_verify(self, claims):
        """
        Automatically verify a list of claims sequentially.
        Returns a list of results aligned by index.
        """
        results = []
        for i, claim in enumerate(claims):
            claim = claim.strip()
            if not claim:
                continue
            result = self.verify_claim(claim)
            result["claim"] = claim
            result["index"] = i
            results.append(result)
        return results
