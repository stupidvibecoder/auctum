import streamlit as st
import PyPDF2
import openai
import tempfile
import os
import json
import re
import pandas as pd
import sqlite3
import hashlib
from datetime import datetime, timedelta
import base64
import numpy as np

# Semantic search dependencies
try:
    from sentence_transformers import SentenceTransformer
    import faiss
    SEMANTIC_SEARCH_AVAILABLE = True
except ImportError:
    SEMANTIC_SEARCH_AVAILABLE = False

# PDF viewer dependency
try:
    from streamlit_pdf_viewer import pdf_viewer
    PDF_VIEWER_AVAILABLE = True
except ImportError:
    PDF_VIEWER_AVAILABLE = False

# Page config
st.set_page_config(
    page_title="Auctum Enterprise", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Simplified CSS
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #0f1419 0%, #1a1f2e 50%, #2d3748 100%);
        color: #ffffff;
    }
    
    .main-title {
        font-size: 4rem;
        font-weight: 700;
        text-align: center;
        background: linear-gradient(135deg, #ffffff 0%, #e2e8f0 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 1rem;
        letter-spacing: -2px;
    }
    
    .main .block-container {
        background: rgba(15, 20, 25, 0.6);
        border-radius: 16px;
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 2rem;
        margin-top: 1rem;
        position: relative;
        z-index: 1;
    }
    
    .privacy-note {
        background: rgba(16, 185, 129, 0.1);
        border: 1px solid rgba(16, 185, 129, 0.3);
        border-radius: 12px;
        padding: 1rem;
        margin: 1rem 0;
        backdrop-filter: blur(10px);
        color: #ffffff;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: all 0.2s;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(99, 102, 241, 0.4);
    }
    
    .stMarkdown, .stText, h1, h2, h3, h4, h5, h6, p, div {
        color: #ffffff !important;
    }
    
    .stTextInput > div > div > input, .stTextArea > div > div > textarea {
        background: rgba(30, 41, 59, 0.8);
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: #ffffff;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'cim_text' not in st.session_state:
    st.session_state.cim_text = None
if 'current_user' not in st.session_state:
    st.session_state.current_user = "demo_user"
if 'current_cim_id' not in st.session_state:
    st.session_state.current_cim_id = None
if 'pdf_file_data' not in st.session_state:
    st.session_state.pdf_file_data = None
if 'pdf_file_name' not in st.session_state:
    st.session_state.pdf_file_name = None
if 'current_page' not in st.session_state:
    st.session_state.current_page = 1
if 'pdf_reader' not in st.session_state:
    st.session_state.pdf_reader = None

# Semantic search state
if 'text_chunks' not in st.session_state:
    st.session_state.text_chunks = []
if 'semantic_index' not in st.session_state:
    st.session_state.semantic_index = None
if 'chunk_embeddings' not in st.session_state:
    st.session_state.chunk_embeddings = None
if 'chunk_page_mapping' not in st.session_state:
    st.session_state.chunk_page_mapping = []
if 'embed_model' not in st.session_state:
    st.session_state.embed_model = None
if 'search_highlights' not in st.session_state:
    st.session_state.search_highlights = []
if 'selected_result' not in st.session_state:
    st.session_state.selected_result = None
if 'last_search_results' not in st.session_state:
    st.session_state.last_search_results = []

@st.cache_resource
def load_embedding_model():
    """Load and cache the embedding model - use a smaller, faster model"""
    if not SEMANTIC_SEARCH_AVAILABLE:
        return None
    try:
        # Use a much smaller and faster model
        model = SentenceTransformer('all-MiniLM-L6-v2')
        return model
    except Exception as e:
        st.error(f"Error loading embedding model: {e}")
        return None

def chunk_text(text, chunk_size=500, overlap=100, fast_mode=True):
    """Split text into smaller, faster-to-process chunks"""
    chunks = []
    
    if fast_mode:
        # Super fast chunking - just split by paragraphs
        paragraphs = text.split('\n\n')
        # Take every other paragraph and limit to 20 chunks
        chunks = [p.strip() for i, p in enumerate(paragraphs) if i % 2 == 0 and p.strip()][:20]
    else:
        # More thorough chunking
        sentences = text.split('. ')
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) < chunk_size:
                current_chunk += sentence + ". "
            else:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        # Limit chunks for faster processing
        chunks = chunks[:50]
    
    return chunks, []

def extract_search_terms_from_results(results, query):
    """Extract key terms from search results for highlighting"""
    terms = set()
    
    # Add query words
    query_words = re.findall(r'\b\w+\b', query.lower())
    terms.update([word for word in query_words if len(word) > 3])
    
    # Extract key phrases from top results
    for result in results[:3]:  # Top 3 results
        chunk_text = result['chunk'].lower()
        
        # Find phrases that appear in both query and chunk
        for word in query_words:
            if word in chunk_text and len(word) > 3:
                terms.add(word)
    
    return list(terms)[:10]  # Limit to 10 terms

def create_better_annotations(results, search_query):
    """Create better annotations from search results"""
    annotations = []
    
    if not results:
        return annotations
    
    # Extract terms from query and results
    search_terms = set()
    query_words = re.findall(r'\b\w{3,}\b', search_query.lower())
    search_terms.update(query_words)
    
    # Get key terms from top results
    for result in results[:3]:
        chunk_words = re.findall(r'\b\w{4,}\b', result['chunk'].lower())
        # Add words that appear in both query and chunk
        common_words = set(query_words) & set(chunk_words)
        search_terms.update(list(common_words)[:5])
    
    # Create annotations for each result page
    for i, result in enumerate(results[:5]):
        page_num = result['page']
        
        # Create multiple annotations for this page
        for j, term in enumerate(list(search_terms)[:8]):
            annotations.append({
                "page": page_num,
                "type": "highlight", 
                "text": term,
                "color": "#FFFF00" if i == 0 else "#FFE066",  # Brighter for top result
                "opacity": 0.4 if i == 0 else 0.25
            })
    
    return annotations

def map_chunks_to_pages(chunks, pdf_reader):
    """Simplified page mapping for speed"""
    # Simple approximation - assume even distribution
    total_pages = len(pdf_reader.pages)
    chunks_per_page = max(1, len(chunks) // total_pages)
    
    page_mapping = []
    for i, chunk in enumerate(chunks):
        page_num = min(total_pages, (i // chunks_per_page) + 1)
        page_mapping.append(page_num)
    
    return page_mapping

def create_semantic_index(chunks):
    """Create FAISS index with optimizations for speed"""
    if not SEMANTIC_SEARCH_AVAILABLE or not st.session_state.embed_model:
        return None, None
    
    try:
        # Limit chunks for faster processing
        limited_chunks = chunks[:30]  # Process max 30 chunks for speed
        
        # Generate embeddings with smaller batch size
        with st.spinner("🧠 Creating search index..."):
            embeddings = st.session_state.embed_model.encode(
                limited_chunks, 
                show_progress_bar=False,
                batch_size=8,  # Smaller batch for speed
                convert_to_numpy=True
            )
        
        # Create FAISS index
        dim = embeddings.shape[1]
        index = faiss.IndexFlatL2(dim)
        index.add(embeddings)
        
        return index, embeddings
    except Exception as e:
        st.error(f"Error creating semantic index: {e}")
        return None, None

def semantic_search(query, chunks, index, top_k=5):
    """Perform semantic search on chunks"""
    if not SEMANTIC_SEARCH_AVAILABLE or not st.session_state.embed_model or index is None:
        return []
    
    try:
        # Encode query
        query_embedding = st.session_state.embed_model.encode([query])
        
        # Search
        distances, indices = index.search(np.array(query_embedding), min(top_k, len(chunks)))
        
        # Return results with scores
        results = []
        for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
            if idx < len(chunks):
                similarity_score = 1 / (1 + distance)  # Convert distance to similarity
                results.append({
                    'chunk': chunks[idx],
                    'index': idx,
                    'similarity': similarity_score,
                    'page': st.session_state.chunk_page_mapping[idx] if idx < len(st.session_state.chunk_page_mapping) else 1
                })
        
        return results
    except Exception as e:
        st.error(f"Error in semantic search: {e}")
        return []

def extract_text_from_pdf(pdf_file):
    """Extract text from PDF using PyPDF2"""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n\n"
        return text, pdf_reader
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return None, None

def show_semantic_search():
    """Semantic Search interface with PDF viewer"""
    
    # Create two columns: search controls and PDF viewer
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("🔍 Semantic Search")
        st.caption("Search and highlight in PDF")
        
        # Check if semantic search is available
        if not SEMANTIC_SEARCH_AVAILABLE:
            st.error("❌ Semantic search requires additional packages.")
            return
        
        if st.session_state.semantic_index is None:
            st.warning("⚠️ Please upload and process a CIM document first.")
            return
        
        # Search input
        search_query = st.text_input(
            "Search your document:",
            placeholder="e.g., revenue streams, financial performance..."
        )
        
        search_button = st.button("🔍 Search", type="primary", use_container_width=True)
        
        # Quick search examples
        st.markdown("**Quick Examples:**")
        if st.button("💰 Revenue", use_container_width=True):
            search_query = "revenue model business"
            search_button = True
        
        if st.button("📊 Financials", use_container_width=True):
            search_query = "financial performance EBITDA"
            search_button = True
        
        if st.button("⚠️ Risks", use_container_width=True):
            search_query = "risks challenges threats"
            search_button = True
        
        # Perform search
        if search_query and search_button:
            with st.spinner("🔍 Searching..."):
                results = semantic_search(search_query, st.session_state.text_chunks, st.session_state.semantic_index, top_k=5)
            
            # Store results for PDF viewer
            st.session_state.last_search_results = results
            st.session_state.last_search = search_query
            
            if results:
                st.success(f"Found {len(results)} relevant sections")
                
                # Extract terms for highlighting
                search_terms = extract_search_terms_from_results(results, search_query)
                st.session_state.search_highlights = search_terms
                
                # Show results summary
                st.markdown("**📋 Search Results:**")
                for i, result in enumerate(results[:5]):  # Show top 5
                    similarity_percentage = result['similarity'] * 100
                    
                    # Create clickable result button
                    result_key = f"result_btn_{i}"
                    button_text = f"📄 Page {result['page']} ({similarity_percentage:.0f}% match)"
                    
                    if st.button(button_text, key=result_key, use_container_width=True):
                        # Set the selected result and page
                        st.session_state.selected_result = result
                        st.session_state.current_page = result['page']
                        st.rerun()
                    
                    # Show preview with highlighting
                    with st.expander(f"Preview", expanded=i==0):
                        preview_text = result['chunk'][:300] + "..." if len(result['chunk']) > 300 else result['chunk']
                        
                        # Highlight search terms in preview
                        highlighted_preview = preview_text
                        for term in search_terms[:5]:
                            if term in highlighted_preview.lower():
                                # Simple text highlighting for preview
                                pattern = re.compile(re.escape(term), re.IGNORECASE)
                                highlighted_preview = pattern.sub(f"**{term}**", highlighted_preview)
                        
                        st.markdown(highlighted_preview)
                        
                        # Show full content option
                        if st.button(f"📖 Show Full Content", key=f"full_content_{i}"):
                            st.text_area("Full Content:", result['chunk'], height=200, key=f"content_area_{i}")
                
                # Show current highlighting info
                if search_terms:
                    st.markdown("**🎯 Highlighting:**")
                    highlighted_terms = ", ".join(list(search_terms)[:8])
                    st.caption(f"Terms: {highlighted_terms}")
                    
                    if st.session_state.selected_result:
                        st.success(f"📍 Viewing: Page {st.session_state.current_page}")
            else:
                st.info("🔍 No results found. Try different search terms.")
        
        # Document statistics
        if st.session_state.text_chunks:
            st.divider()
            st.markdown("**📊 Document Stats**")
            st.metric("Pages", len(set(st.session_state.chunk_page_mapping)))
            st.metric("Chunks", len(st.session_state.text_chunks))
            st.metric("Words", len(st.session_state.cim_text.split()))
    
    with col2:
        st.subheader("📄 PDF Viewer")
        
        # Show current page info
        if st.session_state.current_page > 1:
            st.info(f"📍 Viewing Page {st.session_state.current_page}")
        
        # Show PDF viewer
        if st.session_state.pdf_file_data and PDF_VIEWER_AVAILABLE:
            try:
                # Create annotations based on search results
                annotations = []
                
                if st.session_state.search_highlights and hasattr(st.session_state, 'last_search_results'):
                    # Create better annotations from current search
                    annotations = create_better_annotations(
                        st.session_state.last_search_results, 
                        st.session_state.get('last_search', '')
                    )
                
                # Display PDF with viewer - force page update
                pdf_viewer(
                    st.session_state.pdf_file_data,
                    annotations=annotations,
                    pages_to_render=list(range(1, min(len(st.session_state.pdf_reader.pages) + 1, 21))),  # Render first 20 pages
                    width=700,
                    height=800,
                    key=f"pdf_viewer_{st.session_state.current_page}_{len(annotations)}",  # Force refresh when page/annotations change
                    render_text=True,
                    pages_vertical_spacing=2
                )
                
                # Page navigation controls
                st.markdown("### 📖 Navigation")
                nav_col1, nav_col2, nav_col3 = st.columns(3)
                
                total_pages = len(st.session_state.pdf_reader.pages) if st.session_state.pdf_reader else 1
                
                with nav_col1:
                    if st.button("⬅️ Previous", disabled=st.session_state.current_page <= 1):
                        st.session_state.current_page = max(1, st.session_state.current_page - 1)
                        st.rerun()
                
                with nav_col2:
                    # Page selector
                    new_page = st.selectbox(
                        "Go to page:",
                        range(1, total_pages + 1),
                        index=st.session_state.current_page - 1,
                        key="page_selector"
                    )
                    if new_page != st.session_state.current_page:
                        st.session_state.current_page = new_page
                        st.rerun()
                
                with nav_col3:
                    if st.button("➡️ Next", disabled=st.session_state.current_page >= total_pages):
                        st.session_state.current_page = min(total_pages, st.session_state.current_page + 1)
                        st.rerun()
                
                # Show annotations info
                if annotations:
                    st.caption(f"🎯 {len(annotations)} highlights on {len(set(a['page'] for a in annotations))} pages")
                
            except Exception as e:
                st.error(f"Error displaying PDF: {e}")
                st.info("Showing basic PDF info instead")
                st.write(f"📄 **File:** {st.session_state.pdf_file_name}")
                st.write(f"📝 **Content:** {len(st.session_state.cim_text):,} characters")
                st.write(f"📖 **Pages:** {len(st.session_state.pdf_reader.pages) if st.session_state.pdf_reader else 'Unknown'}")
        
        elif not PDF_VIEWER_AVAILABLE:
            st.error("❌ PDF viewer requires: `pip install streamlit-pdf-viewer`")
            
            # Fallback: show basic document info
            if st.session_state.pdf_file_name:
                st.info("📄 PDF uploaded but viewer unavailable")
                st.write(f"**File:** {st.session_state.pdf_file_name}")
                st.write(f"**Content:** {len(st.session_state.cim_text):,} characters")
                
                # Show text-based search results
                if st.session_state.search_highlights:
                    st.markdown("### 📝 Text Results")
                    if hasattr(st.session_state, 'last_search_results'):
                        for i, result in enumerate(st.session_state.last_search_results[:3]):
                            st.markdown(f"**Page {result['page']}:**")
                            st.text_area(f"Content {i+1}", result['chunk'][:500], height=100, key=f"text_result_{i}")
        
        else:
            st.info("📄 Upload a PDF to view it here")
            
            # Show placeholder
            st.markdown("""
            <div style="border: 2px dashed #666; border-radius: 10px; padding: 50px; text-align: center; background: rgba(30, 41, 59, 0.3);">
                <h3>📄 PDF Viewer</h3>
                <p>Upload and process a PDF to view it here with search highlighting</p>
                <p><strong>Features:</strong></p>
                <p>• Click search results to jump to pages</p>
                <p>• Automatic highlighting of search terms</p>
                <p>• Interactive page navigation</p>
            </div>
            """, unsafe_allow_html=True)

def main():
    # Main title
    st.markdown('<h1 class="main-title">Auctum Enterprise</h1>', unsafe_allow_html=True)

    # Privacy note
    st.markdown("""
    <div class="privacy-note">
        <strong>🔐 Privacy & Security</strong><br>
        Your documents are processed securely and never stored on external servers. All analysis uses enterprise-grade AI with full compliance.
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # User info
        st.markdown(f"**User:** {st.session_state.current_user}")
        
        st.divider()
        
        # OpenAI API Key (optional for now)
        api_key = st.text_input(
            "OpenAI API Key (Optional)", 
            type="password",
            help="Enter your OpenAI API key for advanced features"
        )
        
        st.divider()
        
        # Performance settings
        st.header("⚡ Performance")
        fast_mode = st.toggle("🚀 Fast Mode", value=True, help="Faster processing with fewer chunks")
        
        if fast_mode:
            st.caption("✅ Optimized for speed")
        else:
            st.caption("🐌 Full processing (slower)")
        
        st.divider()
        
        # File upload section
        st.header("📄 Upload CIM")
        uploaded_file = st.file_uploader(
            "Choose a PDF file",
            type=['pdf'],
            help="Upload your CIM in PDF format"
        )
        
        if uploaded_file:
            if st.button("🔍 Process CIM", type="primary"):
                with st.spinner("🔄 Processing CIM..."):
                    # Store PDF file data for viewer
                    st.session_state.pdf_file_data = uploaded_file.read()
                    st.session_state.pdf_file_name = uploaded_file.name
                    
                    # Reset file pointer and extract text
                    uploaded_file.seek(0)
                    text, pdf_reader = extract_text_from_pdf(uploaded_file)
                    
                    if text:
                        st.session_state.cim_text = text
                        st.session_state.pdf_reader = pdf_reader  # Store PDF reader
                        
                        # Quick processing for faster loading
                        fast_mode = st.session_state.get('fast_mode', True)
                        
                        if SEMANTIC_SEARCH_AVAILABLE:
                            # Load model in background if needed
                            if st.session_state.embed_model is None:
                                with st.spinner("⚡ Loading AI model (one-time setup)..."):
                                    st.session_state.embed_model = load_embedding_model()
                            
                            if st.session_state.embed_model:
                                # Fast chunking and indexing
                                chunks, _ = chunk_text(text, fast_mode=fast_mode)
                                st.session_state.text_chunks = chunks
                                
                                # Simple page mapping
                                page_mapping = map_chunks_to_pages(chunks, pdf_reader)
                                st.session_state.chunk_page_mapping = page_mapping
                                
                                # Create index with limited chunks
                                index, embeddings = create_semantic_index(chunks)
                                st.session_state.semantic_index = index
                                st.session_state.chunk_embeddings = embeddings
                        
                        # Quick success message
                        semantic_status = "✅ Ready" if st.session_state.semantic_index else "❌ Unavailable"
                        pdf_viewer_status = "✅ Ready" if PDF_VIEWER_AVAILABLE else "❌ Install needed"
                        
                        st.success(f"✅ Ready! Search: {semantic_status} | Viewer: {pdf_viewer_status}")
                        st.rerun()
    
    # Main content area
    if st.session_state.cim_text is None:
        # Welcome screen
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("### 🚀 Welcome to Auctum Enterprise")
            
            with st.container():
                st.markdown("**🔍 Semantic Search with PDF Highlighting**")
                st.write("Natural language search through your CIM documents with instant PDF highlighting")
                
                st.markdown("**📄 Interactive PDF Viewer**") 
                st.write("View your PDF documents with search results highlighted in real-time")
                
                st.markdown("**🧠 AI-Powered Document Analysis**")
                st.write("Advanced semantic understanding to find relevant content even without exact keyword matches")
                
                st.divider()
                
                st.markdown("#### Getting Started")
                st.write("1. Upload a CIM PDF file in the sidebar")
                st.write("2. Click 'Process CIM' to analyze and index the document")
                st.write("3. Use semantic search to find and highlight information in the PDF!")
                
                # Show feature availability
                st.markdown("#### 🔧 Feature Status")
                semantic_status = "✅ Available" if SEMANTIC_SEARCH_AVAILABLE else "❌ Install: sentence-transformers faiss-cpu"
                pdf_status = "✅ Available" if PDF_VIEWER_AVAILABLE else "❌ Install: streamlit-pdf-viewer"
                
                st.write(f"**Semantic Search:** {semantic_status}")
                st.write(f"**PDF Viewer:** {pdf_status}")
    else:
        # Show semantic search interface
        show_semantic_search()

if __name__ == "__main__":
    main()
