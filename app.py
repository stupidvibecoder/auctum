import streamlit as st
import PyPDF2
import numpy as np
import openai
from sentence_transformers import SentenceTransformer
import faiss
import tempfile
import os
from typing import List, Dict
import json

# Page config
st.set_page_config(
    page_title="Auctum - CIM Analyzer",
    page_icon="📊",
    layout="wide"
)

class SmartCIMAnalyzer:
    def __init__(self, api_key: str):
        """Initialize with OpenAI API key and load embedding model"""
        self.client = openai.OpenAI(api_key=api_key)
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.chunks = []
        self.embeddings = None
        self.index = None
        
    def extract_text_from_pdf(self, pdf_file) -> List[str]:
        """Extract text from PDF and split into chunks"""
        try:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            # Extract all text
            full_text = ""
            for page in pdf_reader.pages:
                text = page.extract_text()
                if text.strip():
                    full_text += text + "\n\n"
            
            # Split into chunks (1000 characters with 200 overlap)
            chunks = []
            chunk_size = 1000
            overlap = 200
            
            for i in range(0, len(full_text), chunk_size - overlap):
                chunk = full_text[i:i + chunk_size]
                if chunk.strip():
                    chunks.append(chunk.strip())
            
            self.chunks = chunks
            return chunks
            
        except Exception as e:
            st.error(f"Error extracting PDF: {str(e)}")
            return []
    
    def create_vector_index(self):
        """Create FAISS vector index from document chunks"""
        if not self.chunks:
            return False
            
        try:
            # Generate embeddings for all chunks
            with st.spinner("🧠 Creating vector index..."):
                embeddings = self.embedding_model.encode(self.chunks)
                self.embeddings = embeddings
                
                # Create FAISS index
                dimension = embeddings.shape[1]
                self.index = faiss.IndexFlatIP(dimension)  # Inner product for similarity
                
                # Normalize embeddings for cosine similarity
                faiss.normalize_L2(embeddings)
                self.index.add(embeddings)
                
            return True
            
        except Exception as e:
            st.error(f"Error creating vector index: {str(e)}")
            return False
    
    def search_relevant_chunks(self, query: str, k: int = 6) -> List[str]:
        """Search for most relevant chunks using vector similarity"""
        if not self.index:
            return []
            
        try:
            # Embed the query
            query_embedding = self.embedding_model.encode([query])
            faiss.normalize_L2(query_embedding)
            
            # Search for similar chunks
            scores, indices = self.index.search(query_embedding, k)
            
            # Return relevant chunks
            relevant_chunks = [self.chunks[i] for i in indices[0] if i < len(self.chunks)]
            return relevant_chunks
            
        except Exception as e:
            st.error(f"Error searching chunks: {str(e)}")
            return []
    
    def answer_question(self, question: str) -> str:
        """Answer question using relevant document chunks"""
        # Search for relevant content
        relevant_chunks = self.search_relevant_chunks(question, k=8)
        
        if not relevant_chunks:
            return "I couldn't find relevant information to answer your question."
        
        # Combine relevant chunks
        context = "\n\n".join(relevant_chunks[:6])  # Limit context size
        
        # Create prompt
        prompt = f"""Based on the following document content, answer this question: {question}

Document content:
{context}

Please provide a comprehensive answer based only on the information provided. If you can't find the specific information, say so."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert financial analyst helping analyze CIM documents."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error generating response: {str(e)}"
    
    def generate_summary(self) -> str:
        """Generate executive summary using multiple targeted searches"""
        summary_queries = [
            "executive summary company overview",
            "business model revenue stream",
            "financial performance metrics revenue EBITDA",
            "investment highlights value proposition",
            "market position competitive advantage"
        ]
        
        # Gather comprehensive context
        all_relevant_chunks = []
        for query in summary_queries:
            chunks = self.search_relevant_chunks(query, k=4)
            all_relevant_chunks.extend(chunks)
        
        # Remove duplicates and limit
        unique_chunks = list(dict.fromkeys(all_relevant_chunks))[:12]
        context = "\n\n".join(unique_chunks)
        
        prompt = f"""Based on this CIM document, provide a comprehensive executive summary with these sections:

1. **Company Overview**: Business description and industry
2. **Business Model**: How the company generates revenue
3. **Key Financial Metrics**: Revenue, EBITDA, growth rates
4. **Investment Highlights**: Main selling points
5. **Market Position**: Competitive advantages

Document content:
{context}

Format with clear headers and bullet points where appropriate."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert investment analyst creating executive summaries."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error generating summary: {str(e)}"
    
    def extract_financial_metrics(self) -> str:
        """Extract key financial metrics"""
        financial_queries = [
            "revenue sales income financial performance",
            "EBITDA profit margin earnings",
            "growth rate year over year",
            "cash flow financial statements",
            "valuation multiple enterprise value"
        ]
        
        # Gather financial content
        all_relevant_chunks = []
        for query in financial_queries:
            chunks = self.search_relevant_chunks(query, k=4)
            all_relevant_chunks.extend(chunks)
        
        unique_chunks = list(dict.fromkeys(all_relevant_chunks))[:10]
        context = "\n\n".join(unique_chunks)
        
        prompt = f"""Extract and organize key financial metrics from this document:

**Look for:**
- Revenue (historical and projected)
- EBITDA and margins
- Growth rates
- Valuation metrics
- Cash flow information
- Profitability metrics

**Format clearly with specific numbers where available.**

Document content:
{context}"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a financial analyst extracting key metrics from investment documents."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error extracting metrics: {str(e)}"
    
    def analyze_risks(self) -> str:
        """Analyze potential risks"""
        risk_queries = [
            "risks challenges threats",
            "competition competitive market risks",
            "financial risks debt liquidity",
            "operational risks management",
            "regulatory compliance legal"
        ]
        
        # Gather risk content
        all_relevant_chunks = []
        for query in risk_queries:
            chunks = self.search_relevant_chunks(query, k=3)
            all_relevant_chunks.extend(chunks)
        
        unique_chunks = list(dict.fromkeys(all_relevant_chunks))[:10]
        context = "\n\n".join(unique_chunks)
        
        prompt = f"""Analyze and categorize risks mentioned in this document:

**Categories to identify:**
- Market Risks (competition, industry trends)
- Operational Risks (management, operations)
- Financial Risks (debt, cash flow)
- Regulatory Risks (compliance, legal)
- Other Notable Risks

**Provide specific examples from the document.**

Document content:
{context}"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a risk analyst evaluating investment opportunities."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error analyzing risks: {str(e)}"

# Initialize session state
if 'analyzer' not in st.session_state:
    st.session_state.analyzer = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'document_stats' not in st.session_state:
    st.session_state.document_stats = None

def main():
    st.title("🏢 Auctum - CIM Intelligence Platform")
    st.subheader("Smart AI-powered analysis of Confidential Information Memorandums")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # API Key
        api_key = st.text_input(
            "OpenAI API Key", 
            type="password",
            help="Enter your OpenAI API key"
        )
        
        if api_key:
            st.success("API key configured ✅")
        else:
            st.warning("Please enter your OpenAI API key")
        
        st.divider()
        
        # File upload
        st.header("📄 Upload CIM")
        uploaded_file = st.file_uploader(
            "Choose a PDF file",
            type=['pdf'],
            help="Upload your CIM in PDF format"
        )
        
        if uploaded_file and api_key:
            if st.button("🔍 Process CIM", type="primary"):
                process_cim(uploaded_file, api_key)
    
    # Main content
    if st.session_state.analyzer is None:
        # Welcome screen
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("""
            ### 🚀 Smart CIM Analysis Platform
            
            **Enhanced Features:**
            - 📤 **Full Document Analysis** - Processes entire PDF
            - 🔍 **Vector Search** - Finds relevant content intelligently  
            - 🤖 **AI-Powered Insights** - GPT-3.5 analysis
            - 📊 **Comprehensive Reports** - Executive summaries & metrics
            - 💬 **Smart Q&A** - Ask questions about any part of the document
            
            **How it works:**
            1. Enter your OpenAI API key
            2. Upload a CIM PDF file  
            3. Our AI creates a searchable index of the entire document
            4. Ask questions and get insights from across all pages
            """)
    else:
        show_analysis_interface()

def process_cim(uploaded_file, api_key):
    """Process the uploaded CIM file"""
    with st.spinner("🔄 Processing CIM document..."):
        try:
            # Initialize analyzer
            analyzer = SmartCIMAnalyzer(api_key)
            
            # Extract text
            st.info("📖 Extracting text from PDF...")
            chunks = analyzer.extract_text_from_pdf(uploaded_file)
            
            if not chunks:
                st.error("No text extracted from PDF")
                return
            
            # Create vector index
            st.info("🧠 Creating smart search index...")
            if not analyzer.create_vector_index():
                st.error("Failed to create search index")
                return
            
            # Store in session
            st.session_state.analyzer = analyzer
            st.session_state.document_stats = {
                'filename': uploaded_file.name,
                'chunks': len(chunks),
                'total_chars': sum(len(chunk) for chunk in chunks)
            }
            
            st.success("✅ CIM processed successfully!")
            st.info(f"📊 Indexed {len(chunks)} text chunks ({sum(len(chunk) for chunk in chunks):,} characters)")
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Error processing CIM: {str(e)}")

def show_analysis_interface():
    """Show analysis interface after CIM is processed"""
    
    # Document stats
    if st.session_state.document_stats:
        stats = st.session_state.document_stats
        st.info(f"📄 **{stats['filename']}** - {stats['chunks']} chunks, {stats['total_chars']:,} characters indexed")
    
    # Analysis sections
    with st.expander("📋 Executive Summary", expanded=True):
        if st.button("📊 Generate Smart Summary"):
            with st.spinner("Analyzing entire document..."):
                try:
                    summary = st.session_state.analyzer.generate_summary()
                    st.markdown(summary)
                except Exception as e:
                    st.error(f"Error: {e}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("💰 Extract Financial Metrics"):
            with st.spinner("Searching for financial data..."):
                try:
                    metrics = st.session_state.analyzer.extract_financial_metrics()
                    st.markdown(metrics)
                except Exception as e:
                    st.error(f"Error: {e}")
    
    with col2:
        if st.button("⚠️ Risk Analysis"):
            with st.spinner("Analyzing risks..."):
                try:
                    risks = st.session_state.analyzer.analyze_risks()
                    st.markdown(risks)
                except Exception as e:
                    st.error(f"Error: {e}")
    
    st.divider()
    
    # Smart Q&A
    st.header("💬 Smart Q&A - Ask About Any Part of the Document")
    
    # Chat history
    for question, answer in st.session_state.chat_history:
        with st.chat_message("user"):
            st.write(question)
        with st.chat_message("assistant"):
            st.write(answer)
    
    # Chat input
    if prompt := st.chat_input("Ask any question about this CIM..."):
        st.session_state.chat_history.append((prompt, ""))
        
        with st.chat_message("user"):
            st.write(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("Searching document and analyzing..."):
                try:
                    response = st.session_state.analyzer.answer_question(prompt)
                    st.write(response)
                    st.session_state.chat_history[-1] = (prompt, response)
                except Exception as e:
                    error_msg = f"Error: {e}"
                    st.error(error_msg)
                    st.session_state.chat_history[-1] = (prompt, error_msg)

if __name__ == "__main__":
    main()
