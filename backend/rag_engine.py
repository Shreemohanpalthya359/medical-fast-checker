import os
import json
import uuid
import base64
import time
from langchain_chroma import Chroma
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain.prompts import PromptTemplate
from langchain.schema import Document
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

        # Sentence-transformers for local, fast clinical text embeddings
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
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
You are a strict, expert medical fact-checker AI. Evaluate the provided CLAIM against \
trusted medical document context AND live scientific research (PubMed abstracts).

Context from Vector Search (Medical Documents):
{doc_context}

Live Scientific Consensus (PubMed):
{live_context}

Medical Claim to Verify:
{claim}

Return ONLY a valid JSON object with exactly these keys:
- "status": "TRUE", "FALSE", or "UNVERIFIED"
- "confidence": integer 0-100 (Truth Meter score)
- "explanation": concise medical explanation (2-4 sentences)
- "sources": list of reference snippets used
- "glossary": dict of complex medical terms and their plain-English definitions
- "consensus_match": boolean, whether claim aligns with current scientific consensus
- "medical_category": the medical specialty this claim belongs to (e.g., "Cardiology", "Pharmacology")

Output RAW JSON ONLY. No markdown. No code fences.
"""
        self.fact_check_prompt = PromptTemplate(
            template=template,
            input_variables=["doc_context", "live_context", "claim"]
        )

    def search_pubmed(self, query):
        """Fetches top abstracts from PubMed for live consensus."""
        try:
            handle = Entrez.esearch(db="pubmed", term=query, retmax=3)
            record = Entrez.read(handle)
            handle.close()
            ids = record["IdList"]
            if not ids:
                return "No recent scientific publications found for this query."
            handle = Entrez.efetch(db="pubmed", id=",".join(ids), rettype="abstract", retmode="text")
            abstracts = handle.read()
            handle.close()
            return abstracts
        except Exception as e:
            return f"PubMed Search Error: {str(e)}"

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

                from langchain.prompts import PromptTemplate
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

    def process_document(self, file_path):
        """Index a PDF document into the vector store."""
        loader = PyPDFLoader(file_path)
        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
        splits = text_splitter.split_documents(documents)
        self.vectorstore.add_documents(splits)
        return len(splits)

    def verify_claim(self, claim):
        """
        Full RAG pipeline: Vector Search → PubMed → LLM Synthesis.
        Returns result enriched with similarity scores, processing time, and model metadata.
        """
        if not self.llm:
            return {"error": "Groq API key is not configured."}

        t_start = time.time()

        # Step 1: Vector Search with similarity scores
        vector_results = self.vectorstore.similarity_search_with_score(claim, k=4)
        doc_context_parts = []
        sources_metadata = []
        similarity_scores = []

        for doc, score in vector_results:
            # Chroma returns L2 distance; convert to 0-1 similarity
            similarity = round(max(0.0, 1.0 - score / 2.0), 3)
            similarity_scores.append(similarity)
            doc_context_parts.append(
                f"Source ({doc.metadata.get('source', 'unknown')} | Topic: {doc.metadata.get('topic', 'general')} | Similarity: {similarity:.0%}):\n{doc.page_content}"
            )
            sources_metadata.append({
                "file": doc.metadata.get("source", "Unknown").split("/")[-1],
                "page": doc.metadata.get("page", 0) + 1,
                "topic": doc.metadata.get("topic", "general"),
                "similarity": similarity,
                "snippet": doc.page_content[:200] + "..."
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

        total_ms = round((t_llm - t_start) * 1000)
        vector_ms = round((t_vector - t_start) * 1000)
        pubmed_ms = round((t_pubmed - t_vector) * 1000)
        llm_ms = round((t_llm - t_pubmed) * 1000)

        try:
            content = response.content.strip()
            if "```json" in content:
                content = content.split("```json")[-1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].strip()
            if "{" in content and "}" in content:
                content = content[content.find("{"):content.rfind("}") + 1]
            result = json.loads(content)

            # Enrich with pipeline metadata
            result["detailed_sources"] = sources_metadata
            result["similarity_scores"] = similarity_scores
            result["vector_hits"] = len(vector_results)
            result["model_used"] = self.model_name
            result["processing_time_ms"] = total_ms
            result["pipeline_breakdown"] = {
                "vector_search_ms": vector_ms,
                "pubmed_ms": pubmed_ms,
                "llm_synthesis_ms": llm_ms
            }
            return result
        except Exception as e:
            return {
                "error": "Parsing failed",
                "raw": response.content,
                "processing_time_ms": total_ms
            }

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
