import streamlit as st
import PyPDF2
import openai
import tempfile
import os

# Page config
st.set_page_config(
    page_title="Auctum", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Clean dark theme with subtle particles
st.markdown("""
<style>
    /* Hide Streamlit branding */
    .stApp > header {
        background-color: transparent;
    }
    
    .stApp > header [data-testid="stHeader"] {
        display: none;
    }
    
    /* Dark theme background */
    .stApp {
        background: linear-gradient(135deg, #0f1419 0%, #1a1f2e 50%, #2d3748 100%);
        color: #ffffff;
    }
    
    /* Floating particles */
    .particle {
        position: fixed;
        border-radius: 50%;
        background: rgba(99, 102, 241, 0.4);
        animation: float 6s ease-in-out infinite;
        pointer-events: none;
        z-index: 0;
    }
    
    .particle:nth-child(odd) {
        background: rgba(139, 92, 246, 0.3);
        animation-delay: -2s;
    }
    
    .particle:nth-child(3n) {
        background: rgba(59, 130, 246, 0.3);
        animation-delay: -4s;
    }
    
    @keyframes float {
        0%, 100% { 
            transform: translateY(0px) translateX(0px) rotate(0deg); 
            opacity: 0.4;
        }
        33% { 
            transform: translateY(-30px) translateX(20px) rotate(120deg); 
            opacity: 0.8;
        }
        66% { 
            transform: translateY(20px) translateX(-20px) rotate(240deg); 
            opacity: 0.6;
        }
    }
    
    /* Clean title styling */
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
    
    /* Content styling */
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
    
    /* Privacy note */
    .privacy-note {
        background: rgba(16, 185, 129, 0.1);
        border: 1px solid rgba(16, 185, 129, 0.3);
        border-radius: 12px;
        padding: 1rem;
        margin: 1rem 0;
        backdrop-filter: blur(10px);
        color: #ffffff;
    }
    
    /* Cards */
    .welcome-card {
        background: rgba(30, 41, 59, 0.8);
        border-radius: 16px;
        padding: 2rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: #ffffff;
    }
    
    .feature-item {
        background: rgba(99, 102, 241, 0.1);
        border-left: 4px solid #6366f1;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0 8px 8px 0;
        color: #e2e8f0;
    }
    
    /* Buttons */
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
    
    /* Sidebar */
    .css-1d391kg {
        background: rgba(15, 20, 25, 0.9);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Text colors */
    .stMarkdown, .stText, h1, h2, h3, h4, h5, h6, p, div {
        color: #ffffff !important;
    }
    
    /* Info boxes */
    .stInfo {
        background: rgba(59, 130, 246, 0.1);
        border: 1px solid rgba(59, 130, 246, 0.3);
        color: #ffffff;
    }
    
    /* Success boxes */
    .stSuccess {
        background: rgba(16, 185, 129, 0.1);
        border: 1px solid rgba(16, 185, 129, 0.3);
        color: #ffffff;
    }
    
    /* Warning boxes */
    .stWarning {
        background: rgba(245, 158, 11, 0.1);
        border: 1px solid rgba(245, 158, 11, 0.3);
        color: #ffffff;
    }
    
    /* Chat messages */
    .stChatMessage {
        background: rgba(30, 41, 59, 0.8);
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: #ffffff;
    }
    
    /* Input fields */
    .stTextInput > div > div > input {
        background: rgba(30, 41, 59, 0.8);
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: #ffffff;
    }
    
    .stChatInput > div > div > input {
        background: rgba(15, 20, 25, 0.8);
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: #ffffff;
    }
</style>

<!-- Add floating particles -->
<div class="particle" style="left: 10%; top: 20%; width: 8px; height: 8px; animation-delay: 0s;"></div>
<div class="particle" style="left: 80%; top: 80%; width: 6px; height: 6px; animation-delay: 2s;"></div>
<div class="particle" style="left: 60%; top: 30%; width: 10px; height: 10px; animation-delay: 4s;"></div>
<div class="particle" style="left: 20%; top: 70%; width: 7px; height: 7px; animation-delay: 1s;"></div>
<div class="particle" style="left: 90%; top: 10%; width: 5px; height: 5px; animation-delay: 3s;"></div>
<div class="particle" style="left: 40%; top: 50%; width: 9px; height: 9px; animation-delay: 5s;"></div>
<div class="particle" style="left: 70%; top: 60%; width: 8px; height: 8px; animation-delay: 1.5s;"></div>
<div class="particle" style="left: 30%; top: 90%; width: 6px; height: 6px; animation-delay: 3.5s;"></div>
""", unsafe_allow_html=True)

# Initialize session state
if 'cim_text' not in st.session_state:
    st.session_state.cim_text = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

def extract_text_from_pdf(pdf_file):
    """Extract text from PDF using PyPDF2"""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n\n"
        return text
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return None

def search_document_sections(text, query_terms, chunk_size=3000):
    """Search for relevant sections in the document based on query terms"""
    chunks = []
    overlap = 500
    
    for i in range(0, len(text), chunk_size - overlap):
        chunk = text[i:i + chunk_size]
        if chunk.strip():
            chunks.append((chunk, i))
    
    scored_chunks = []
    for chunk, position in chunks:
        chunk_lower = chunk.lower()
        score = 0
        
        for term in query_terms:
            score += chunk_lower.count(term.lower())
        
        if score > 0:
            scored_chunks.append((chunk, score, position))
    
    scored_chunks.sort(key=lambda x: x[1], reverse=True)
    return [chunk for chunk, score, pos in scored_chunks[:5]]

def get_openai_response(prompt, context, api_key):
    """Get response from OpenAI with smart document search"""
    try:
        client = openai.OpenAI(api_key=api_key)
        
        financial_terms = ['revenue', 'sales', 'income', 'ebitda', 'profit', 'margin', 'growth', 'financial', 'cash flow', 'valuation', 'multiple', 'earnings']
        risk_terms = ['risk', 'challenge', 'threat', 'competition', 'regulatory', 'compliance', 'debt', 'liability', 'uncertainty']
        summary_terms = ['overview', 'summary', 'business', 'company', 'industry', 'market', 'opportunity', 'investment', 'strategy']
        
        prompt_lower = prompt.lower()
        if any(term in prompt_lower for term in ['financial', 'revenue', 'ebitda', 'profit', 'metrics']):
            search_terms = financial_terms
        elif any(term in prompt_lower for term in ['risk', 'challenge', 'threat']):
            search_terms = risk_terms
        elif any(term in prompt_lower for term in ['summary', 'overview', 'business']):
            search_terms = summary_terms
        else:
            search_terms = [word for word in prompt_lower.split() if len(word) > 3]
        
        relevant_sections = search_document_sections(context, search_terms)
        
        if relevant_sections:
            combined_context = "\n\n--- RELEVANT SECTION ---\n\n".join(relevant_sections)
            context_info = f"Analysis based on {len(relevant_sections)} relevant sections found in the document"
        else:
            chunk_size = 6000
            chunks = [context[i:i+chunk_size] for i in range(0, len(context), chunk_size)]
            
            selected_chunks = []
            if len(chunks) >= 1:
                selected_chunks.append(chunks[0])
            if len(chunks) >= 3:
                selected_chunks.append(chunks[len(chunks)//2])
            if len(chunks) >= 2:
                selected_chunks.append(chunks[-1])
                
            combined_context = "\n\n--- SECTION BREAK ---\n\n".join(selected_chunks)
            context_info = f"Analysis based on beginning, middle, and end sections of the document"
        
        full_prompt = f"""Based on the following CIM document content, {prompt}

{context_info}:

{combined_context}

Please provide a comprehensive answer based on the information provided. If you notice the information seems incomplete, mention that additional details may be available in other parts of the full document."""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert financial analyst helping analyze CIM documents. You're analyzing the most relevant sections found in the document."},
                {"role": "user", "content": full_prompt}
            ],
            max_tokens=1500,
            temperature=0
        )
        
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating response: {str(e)}"

def main():
    # Clean title only
    st.markdown('<h1 class="main-title">Auctum</h1>', unsafe_allow_html=True)

    # Privacy note
    st.markdown("""
    <div class="privacy-note">
        <strong>🔐 Privacy & Security</strong><br>
        Your documents are processed securely and never stored. All analysis uses enterprise-grade AI with full compliance.
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # OpenAI API Key
        api_key = st.text_input(
            "OpenAI API Key", 
            type="password",
            help="Enter your OpenAI API key"
        )
        
        if api_key:
            st.success("✅ API key configured")
        else:
            st.warning("⚠️ Please enter your OpenAI API key")
        
        st.divider()
        
        # File upload section
        st.header("📄 Upload CIM")
        uploaded_file = st.file_uploader(
            "Choose a PDF file",
            type=['pdf'],
            help="Upload your CIM in PDF format"
        )
        
        if uploaded_file and api_key:
            if st.button("🔍 Process CIM", type="primary"):
                with st.spinner("🔄 Processing CIM..."):
                    text = extract_text_from_pdf(uploaded_file)
                    if text:
                        st.session_state.cim_text = text
                        st.success(f"✅ CIM processed! Extracted {len(text):,} characters")
                        st.rerun()
    
    # Main content area
    if st.session_state.cim_text is None:
        # Welcome screen
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            # Use Streamlit's native components instead of HTML
            st.markdown("### 🚀 Welcome to Auctum")
            
            with st.container():
                st.markdown("**📤 Upload Documents**")
                st.write("Support for PDF CIM documents with intelligent text extraction")
                
                st.markdown("**🤖 AI Analysis**") 
                st.write("Get instant insights and comprehensive analysis of investment opportunities")
                
                st.markdown("**📊 Smart Insights**")
                st.write("Extract key metrics, financial data, and risk assessments automatically")
                
                st.markdown("**💬 Interactive Chat**")
                st.write("Ask specific questions about your CIM documents and get detailed answers")
                
                st.divider()
                
                st.markdown("#### Getting Started")
                st.write("1. Enter your OpenAI API key in the sidebar")
                st.write("2. Upload a CIM PDF file") 
                st.write("3. Click 'Process CIM' to analyze")
                st.write("4. Start asking questions and generating insights!")
    else:
        # Show CIM analysis interface
        show_analysis_interface(api_key)

def show_analysis_interface(api_key):
    """Show the main analysis interface after CIM is processed"""
    
    st.info(f"📄 **Document Loaded**: {len(st.session_state.cim_text):,} characters extracted and ready for analysis")
    
    # Quick analysis buttons
    st.subheader("🎯 Quick Analysis")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Executive Summary", use_container_width=True):
            with st.spinner("🔍 Generating comprehensive summary..."):
                summary = get_openai_response(
                    "provide an executive summary of this CIM including company overview, business model, and key highlights.",
                    st.session_state.cim_text,
                    api_key
                )
                st.markdown("### 📊 Executive Summary")
                st.markdown(summary)
    
    with col2:
        if st.button("💰 Financial Analysis", use_container_width=True):
            with st.spinner("📈 Extracting financial metrics..."):
                metrics = get_openai_response(
                    "extract and summarize the key financial metrics including revenue, EBITDA, growth rates, and valuation information.",
                    st.session_state.cim_text,
                    api_key
                )
                st.markdown("### 💰 Financial Metrics")
                st.markdown(metrics)
    
    with col3:
        if st.button("⚠️ Risk Assessment", use_container_width=True):
            with st.spinner("🛡️ Analyzing potential risks..."):
                risks = get_openai_response(
                    "identify and analyze the key risks and challenges mentioned in this document.",
                    st.session_state.cim_text,
                    api_key
                )
                st.markdown("### ⚠️ Risk Analysis")
                st.markdown(risks)
    
    st.divider()
    
    # Chat interface
    st.subheader("💬 Interactive Analysis")
    st.caption("Ask specific questions about this CIM document")
    
    # Display chat history
    for i, (question, answer) in enumerate(st.session_state.chat_history):
        with st.chat_message("user"):
            st.write(question)
        with st.chat_message("assistant"):
            st.write(answer)
    
    # Chat input
    if prompt := st.chat_input("Ask a question about this CIM document..."):
        # Add user message to chat history
        st.session_state.chat_history.append((prompt, ""))
        
        # Display user message
        with st.chat_message("user"):
            st.write(prompt)
        
        # Generate and display assistant response
        with st.chat_message("assistant"):
            with st.spinner("🤔 Analyzing your question..."):
                response = get_openai_response(prompt, st.session_state.cim_text, api_key)
                st.write(response)
                
                # Update chat history with response
                st.session_state.chat_history[-1] = (prompt, response)

if __name__ == "__main__":
    main()
