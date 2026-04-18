import os
import json
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv

load_dotenv()

class MedicalRAGEngine:
    def __init__(self, persist_directory="./chroma_db"):
        self.persist_directory = persist_directory
        # Use sentence-transformers for local, fast clinical text embeddings if possible, or standard MiniLM
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.init_vectorstore()
        
        # Initialize Groq LLM
        # Defaulting to llama-3.1-8b-instant or mixtral
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key or api_key == "your_groq_api_key_here":
            print("WARNING: GROQ_API_KEY not found in .env!")
            self.llm = None
        else:
            self.llm = ChatGroq(temperature=0, model_name="llama-3.1-8b-instant", api_key=api_key)

        self.setup_prompt()

    def init_vectorstore(self):
        # Create a Chroma vector store. If semantic data already exists in the persist_dir, it loads it.
        self.vectorstore = Chroma(
            collection_name="medical_knowledge",
            embedding_function=self.embeddings,
            persist_directory=self.persist_directory
        )

    def setup_prompt(self):
        template = """
You are a strict, expert medical fact-checker. You will be provided with a medical CLAIM and context from trusted medical documents.
Your job is to evaluate if the claim is TRUE, FALSE, or UNVERIFIED based ONLY on the provided context.

Context from trusted medical documents:
{context}

Claim to verify:
{claim}

You MUST return your answer in valid JSON format ONLY, with exactly these four keys:
"status": The verdict, which MUST be exactly one of: "TRUE", "FALSE", or "UNVERIFIED".
"confidence": A number from 0 to 100 representing your confidence based on how well the context covers the claim.
"explanation": A concise, formal medical explanation of why this verdict was reached based on the text.
"sources": A short list of the specific points or document snippets you used from the context.

Do NOT include markdown formatting like ```json or anything else. Output RAW JSON ONLY.
"""
        self.prompt = PromptTemplate(
            template=template,
            input_variables=["context", "claim"]
        )

    def process_document(self, file_path):
        """Loads a Medical PDF, splits it, and adds it to the vector database."""
        loader = PyPDFLoader(file_path)
        documents = loader.load()
        
        # Split documents into smaller manageable chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, 
            chunk_overlap=150
        )
        splits = text_splitter.split_documents(documents)
        
        # Add to vector store and persist
        self.vectorstore.add_documents(splits)
        return len(splits)

    def verify_claim(self, claim):
        """Searches vector DB and fact-checks the claim."""
        if not self.llm:
            return {"error": "Groq API key is not configured. Please set GROQ_API_KEY in backend/.env"}

        # 1. Retrieve similar documents
        results = self.vectorstore.similarity_search(claim, k=4)
        
        if not results:
            return {
                "status": "UNVERIFIED",
                "confidence": 0,
                "explanation": "No relevant medical documents found in the knowledge base to verify this claim.",
                "sources": []
            }
            
        context_text = "\n\n".join([f"Source Snippet:\n{doc.page_content}" for doc in results])
        
        # 2. Fact Check using LLM
        chain = self.prompt | self.llm
        response = chain.invoke({"context": context_text, "claim": claim})
        
        # 3. Parse JSON Output
        try:
            # We strip in case the LLM returned some whitespace or markdown backticks
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:-3]
            elif content.startswith("```"):
                content = content[3:-3]
            
            result = json.loads(content)
            
            # Auto-populate the exact file sources if the LLM didn't attach metadata
            sources_metadata = list(set([doc.metadata.get("source", "Unknown Document").split("/")[-1] for doc in results]))
            result["documents_referenced"] = sources_metadata
            return result
        except Exception as e:
            print("Failed to parse LLM output:", response.content)
            return {
                "error": "Failed to parse fact-check result. The LLM may have produced invalid formatting.",
                "raw_response": response.content
            }
