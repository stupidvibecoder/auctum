import streamlit as st
import os
import tempfile
import numpy as np
from openai import OpenAI
import logging

# Page config
st.set_page_config(
    page_title="Auctum - CIM Analyzer",
    page_icon="📊",
    layout="wide"
)

# Initialize session state
if 'cim_data' not in st.session_state:
    st.session_state.cim_data = None
if 'analyzer' not in st.session_state:
    st.session_state.analyzer = None

class Document:
    """Simple document class"""
    def __init__(self, page_content, metadata=None):
        self.page_content = page_content
        self.metadata = metadata or {}

class SmartCIMAnalyzer:
    """Smart CIM analyzer with vector search - no LangChain dependencies"""
    
    def __init__(self, document_chunks):
        self.document_chunks = document_chunks
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        
        # Try to setup vector search, fallback to keyword search
        try:
            self.setup_vector_search()
            self.has_vector_search = True
            st.success("🧠 Smart vector search enabled - analyzing entire document")
        except Exception as e:
            self.has_vector_search = False
            st.info("📖 Using keyword search - still analyzes full document")
            logging.warning(f"Vector search setup failed: {e}")
    
    def setup_vector_search(self):
        """Setup FAISS vector search with sentence transformers"""
        try:
            from sentence_transformers import SentenceTransformer
            import faiss
            
            # Load embedding model
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Create embeddings for all chunks
            texts = [chunk.page_content for chunk in self.document_chunks]
            embeddings = self.embedding_model.encode(texts)
            
            # Create FAISS index
            dimension = embeddings.shape[1]
            self.index = faiss.IndexFlatIP(dimension)  # Inner product for similarity
            
            # Normalize embeddings for cosine similarity
            faiss.normalize_L2(embeddings)
            self.index.add(embeddings.astype('float32'))
            
            st.success(f"🔍 Indexed {len(texts)} document segments for intelligent search")
            
        except Exception as e:
            logging.error(f"Vector search setup failed: {e}")
            raise
    
    def get_relevant_content(self, query, max_chunks=8):
        """Get relevant content using vector search or keyword fallback"""
        if self.has_vector_search:
            try:
                # Vector search
                query_embedding = self.embedding_model.encode([query])
                faiss.normalize_L2(query_embedding)
                
                # Search for similar chunks
                scores, indices = self.index.search(query_embedding.astype('float32'), max_chunks)
                
                # Return relevant chunks
                relevant_chunks = []
                for idx in indices[0]:
                    if idx < len(self.document_chunks):
                        relevant_chunks.append(self.document_chunks[idx].page_content)
                
                return relevant_chunks
                
            except Exception as e:
                logging.error(f"Vector search failed: {e}")
        
        # Fallback: keyword search
        return self.keyword_search(query, max_chunks)
    
    def keyword_search(self, query, max_chunks=8):
        """Keyword-based search fallback"""
        keywords = query.lower().split()
        scored_chunks = []
        
        for chunk in self.document_chunks:
            content_lower = chunk.page_content.lower()
            score = sum(content_lower.count(keyword) for keyword in keywords)
            if score > 0:
                scored_chunks.append((score, chunk.page_content))
        
        # Sort by relevance and return top chunks
        scored_chunks.sort(reverse=True, key=lambda x: x[0])
        return [content for _, content in scored_chunks[:max_chunks]]
    
    def analyze_with_context(self, analysis_type, custom_question=None):
        """Analyze with relevant context from entire document"""
        
        # Define search queries for different analysis types
        search_queries = {
            "summary": [
                "executive summary company overview business model",
                "revenue financial performance investment highlights", 
                "market position competitive advantages"
            ],
            "financial": [
                "revenue sales financial performance EBITDA profit",
                "growth rate margin cash flow",
                "valuation enterprise value financial metrics"
            ],
            "risks": [
                "risks challenges threats competition regulatory",
                "market risks operational risks financial risks",
                "compliance legal regulatory challenges"
            ],
            "custom": [custom_question or "company business model financial performance"]
        }
        
        # Get relevant content using smart search
        all_relevant_content = []
        queries = search_queries.get(analysis_type, search_queries["custom"])
        
        for query in queries:
            relevant_chunks = self.get_relevant_content(query, max_chunks=4)
            all_relevant_content.extend(relevant_chunks)
        
        # Remove duplicates while preserving order
        unique_content = []
        seen = set()
        for content in all_relevant_content:
            content_key = content[:100]  # Use first 100 chars as key
            if content_key not in seen:
                unique_content.append(content)
                seen.add(content_key)
        
        # Combine top relevant content
        context = "\n\n".join(unique_content[:10])
        
        # Truncate if too long for OpenAI
        max_chars = 15000
        if len(context) > max_chars:
            context = context[:max_chars] + "\n\n[Content truncated for analysis...]"
        
        return self.generate_analysis(analysis_type, context, custom_question)
    
    def generate_analysis(self, analysis_type, context, custom_question=None):
        """Generate analysis using OpenAI"""
        
        prompts = {
            "summary": """Based on this CIM content, provide a comprehensive executive summary:

1. **Company Overview**: What does the company do? What industry/sector?
2. **Business Model**: How does the company make money?
3. **Key Financial Metrics**: Revenue, EBITDA, growth rates (include specific numbers)
4. **Investment Highlights**: Main selling points and competitive advantages
5. **Market Position**: Industry position and growth strategy

Be specific and use actual data from the document where available.""",

            "financial": """Extract and analyze key financial metrics from this CIM:

- **Revenue**: Historical figures, projections, and growth trends
- **Profitability**: EBITDA, margins, profit trends with specific numbers
- **Growth**: Year-over-year growth rates and key drivers
- **Cash Flow**: Operating and free cash flow figures
- **Valuation**: Multiples, enterprise value, pricing metrics
- **Key Ratios**: Important financial ratios and benchmarks

Present specific numbers, percentages, and trends where available.""",

            "risks": """Identify and categorize risks mentioned in this CIM:

- **Market Risks**: Industry trends, competition, market conditions
- **Operational Risks**: Management, operations, execution challenges  
- **Financial Risks**: Cash flow, debt, capital requirements
- **Regulatory Risks**: Compliance, legal, regulatory changes
- **Strategic Risks**: Technology, customer concentration, competition

For each category, provide specific examples and details from the document.""",

            "custom": custom_question or "Provide a comprehensive analysis of this document."
        }
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an expert financial analyst with deep experience in CIM analysis and investment evaluation. Provide detailed, specific analysis based on the document content. Include actual numbers, percentages, and specific details where available."
                    },
                    {
                        "role": "user", 
                        "content": f"{prompts[analysis_type]}\n\nRelevant Document Content:\n{context}"
                    }
                ],
                temperature=0.1,
                max_tokens=2000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Analysis error: {str(e)}"

def extract_pdf_text(uploaded_file):
    """Extract text from PDF and create document chunks"""
    try:
        from pypdf import PdfReader
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name
        
        # Extract text page by page
        reader = PdfReader(tmp_path)
        documents = []
        
        for page_num, page in enumerate(reader.pages):
            text = page.extract_text()
            if text and text.strip():
                # Create document chunks (by page initially)
                doc = Document(
                    page_content=text,
                    metadata={"source": uploaded_file.name, "page": page_num + 1}
                )
                documents.append(doc)
        
        # Split large pages into smaller chunks for better search
        chunks = split_documents(documents)
        
        # Clean up
        os.unlink(tmp_path)
        
        return chunks, len(reader.pages)
        
    except Exception as e:
        st.error(f"Error extracting PDF: {e}")
        return None, 0

def split_documents(documents, chunk_size=1500, chunk_overlap=200):
    """Split documents into smaller chunks for better analysis"""
    chunks = []
    
    for doc in documents:
        text = doc.page_content
        
        # Simple text splitting with overlap
        if len(text) <= chunk_size:
            chunks.append(doc)
        else:
            # Split into overlapping chunks
            for i in range(0, len(text), chunk_size - chunk_overlap):
                chunk_text = text[i:i + chunk_size]
                if chunk_text.strip():
                    chunk = Document(
                        page_content=chunk_text,
                        metadata=doc.metadata
                    )
                    chunks.append(chunk)
    
    return chunks

def main():
    st.title("🏢 Auctum - CIM Intelligence Platform")
    st.subheader("Upload your Confidential Information Memorandum and get AI-powered insights")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # API Key
        api_key = st.text_input("OpenAI API Key", type="password")
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
            st.success("✅ API key configured")
        else:
            st.warning("⚠️ Enter OpenAI API key to continue")
        
        st.divider()
        
        # File upload
        st.header("📄 Upload CIM")
        uploaded_file = st.file_uploader("Choose PDF file", type=['pdf'])
        
        if uploaded_file and api_key:
            if st.button("🔍 Process CIM", type="primary"):
                with st.spinner("🔄 Processing CIM and setting up intelligent analysis..."):
                    try:
                        # Extract and chunk the document
                        st.info("📖 Extracting text from PDF...")
                        chunks, num_pages = extract_pdf_text(uploaded_file)
                        
                        if chunks:
                            # Initialize smart analyzer
                            st.info("🧠 Setting up intelligent document search...")
                            analyzer = SmartCIMAnalyzer(chunks)
                            
                            # Store in session state
                            st.session_state.cim_data = {
                                'chunks': chunks,
                                'num_pages': num_pages,
                                'total_chunks': len(chunks)
                            }
                            st.session_state.analyzer = analyzer
                            
                            st.success(f"✅ CIM processed successfully!")
                            st.info(f"📄 Analyzed {num_pages} pages, {len(chunks)} text segments")
                            st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Error processing CIM: {str(e)}")
    
    # Main content
    if st.session_state.cim_data and st.session_state.analyzer:
        show_analysis_interface()
    else:
        show_welcome_screen()

def show_analysis_interface():
    """Show the smart analysis interface"""
    
    data = st.session_state.cim_data
    analyzer = st.session_state.analyzer
    
    st.success(f"📊 Document loaded: {data['num_pages']} pages, {data['total_chunks']} segments")
    
    # Analysis buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Executive Summary", type="primary"):
            with st.spinner("🔍 Analyzing entire document for executive summary..."):
                summary = analyzer.analyze_with_context("summary")
                st.markdown("### Executive Summary")
                st.markdown(summary)
    
    with col2:
        if st.button("💰 Financial Analysis"):
            with st.spinner("🔍 Searching document for financial metrics..."):
                metrics = analyzer.analyze_with_context("financial")
                st.markdown("### Financial Analysis")
                st.markdown(metrics)
    
    with col3:
        if st.button("⚠️ Risk Assessment"):
            with st.spinner("🔍 Analyzing risks across full document..."):
                risks = analyzer.analyze_with_context("risks")
                st.markdown("### Risk Assessment")
                st.markdown(risks)
    
    st.divider()
    
    # Smart Q&A Section
    st.header("💬 Smart Q&A - Ask About Anything in the Document")
    question = st.text_input("Ask a detailed question about this CIM...")
    
    if question:
        with st.spinner("🔍 Searching entire document for relevant information..."):
            answer = analyzer.analyze_with_context("custom", question)
            st.markdown("### Answer")
            st.markdown(answer)
    
    # Document stats
    with st.expander("📊 Document Analysis Stats"):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Pages", data['num_pages'])
        with col2:
            st.metric("Text Segments", data['total_chunks'])
        with col3:
            total_chars = sum(len(chunk.page_content) for chunk in data['chunks'])
            st.metric("Total Characters", f"{total_chars:,}")

def show_welcome_screen():
    """Show welcome screen"""
    st.markdown("""
    ### 🚀 Welcome to Auctum MVP - Smart Document Analysis
    
    **🧠 Intelligent Features:**
    - **Vector Search**: AI-powered search across your entire 100+ page document
    - **Smart Analysis**: Finds relevant information from anywhere in the CIM
    - **Comprehensive Coverage**: Analyzes full document, not just first few pages
    - **Intelligent Q&A**: Ask questions about any part of the document
    
    **🔍 Analysis Types:**
    - 📊 **Executive Summary**: Business model, financials, investment highlights
    - 💰 **Financial Analysis**: Revenue, EBITDA, growth, cash flow with specific numbers
    - ⚠️ **Risk Assessment**: Market, operational, financial, regulatory risks
    - 💬 **Custom Q&A**: Ask anything about the investment opportunity
    
    **Get started:**
    1. Enter your OpenAI API key in the sidebar
    2. Upload a CIM PDF file  
    3. Click "Process CIM" to analyze the entire document
    4. Use analysis buttons or ask specific questions
    
    **This version intelligently searches your ENTIRE document!**
    """)

if __name__ == "__main__":
    main()
