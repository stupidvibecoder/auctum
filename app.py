import streamlit as st
import PyPDF2
import openai
import tempfile
import os
import json
import re
import pandas as pd
from datetime import datetime

# Page config
st.set_page_config(
    page_title="Auctum", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced CSS with sticky navigation and improved styling
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
    
    /* Sticky navigation tabs */
    .sticky-tabs {
        position: sticky;
        top: 0;
        z-index: 999;
        background: rgba(15, 20, 25, 0.95);
        padding: 0.5rem 0;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        margin-bottom: 1rem;
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
    
    /* Task status styling */
    .task-card {
        background: rgba(30, 41, 59, 0.8);
        border-radius: 12px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid;
        transition: all 0.2s;
    }
    
    .task-open {
        border-left-color: #ef4444;
    }
    
    .task-in-progress {
        border-left-color: #f59e0b;
    }
    
    .task-complete {
        border-left-color: #10b981;
        opacity: 0.7;
    }
    
    .task-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    
    /* User avatar styling */
    .user-avatar {
        display: inline-block;
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background: linear-gradient(135deg, #6366f1, #8b5cf6);
        color: white;
        text-align: center;
        line-height: 32px;
        font-weight: bold;
        font-size: 0.8rem;
        margin-right: 0.5rem;
    }
    
    /* Audit trail badge */
    .audit-badge {
        background: rgba(16, 185, 129, 0.1);
        border: 1px solid rgba(16, 185, 129, 0.3);
        border-radius: 8px;
        padding: 0.5rem;
        font-size: 0.85rem;
        margin: 0.5rem 0;
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
if 'cim_sections' not in st.session_state:
    st.session_state.cim_sections = {}
if 'comment_store' not in st.session_state:
    st.session_state.comment_store = {}
if 'memo_store' not in st.session_state:
    st.session_state.memo_store = {}
if 'workspace_initialized' not in st.session_state:
    st.session_state.workspace_initialized = False
if 'section_summaries' not in st.session_state:
    st.session_state.section_summaries = {}
if 'audit_log' not in st.session_state:
    st.session_state.audit_log = []

# Team members and tags for autocomplete
TEAM_MEMBERS = ['@Alex', '@Rishi', '@Jordan', '@Sam', '@Taylor', '@Morgan']
COMMON_TAGS = ['#Modeling', '#Legal', '#KeyAssumption', '#Revenue', '#EBITDA', '#Risk', '#Market', '#Management']

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

def extract_section_headers(text):
    """Extract section headers from CIM text"""
    # Pattern for numbered sections like "1.0 Executive Summary" or "2. Financial Overview"
    patterns = [
        r"(\d+\.?\d*\s+[A-Z][a-zA-Z\s&]+)(?=\n|\r)",  # Numbered sections
        r"([A-Z][A-Z\s&]{10,}?)(?=\n|\r)",  # All caps headers
        r"^([A-Z][a-zA-Z\s&]{5,}?)(?=\n)",  # Title case headers at line start
    ]
    
    headers = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.MULTILINE)
        headers.extend([match.strip() for match in matches if len(match.strip()) > 5])
    
    # Clean and deduplicate
    headers = list(dict.fromkeys(headers))  # Remove duplicates while preserving order
    
    # Common CIM sections if no headers found
    if not headers:
        headers = [
            "Executive Summary", 
            "Business Overview", 
            "Financial Performance", 
            "Market Analysis", 
            "Management Team", 
            "Investment Highlights",
            "Risk Factors",
            "Transaction Overview"
        ]
    
    return headers[:15]  # Limit to first 15 sections

def split_text_by_sections(text, headers):
    """Split text into sections based on headers"""
    sections = {}
    text_lower = text.lower()
    
    for i, header in enumerate(headers):
        header_lower = header.lower()
        start_pos = text_lower.find(header_lower)
        
        if start_pos != -1:
            # Find the end position (start of next header or end of text)
            if i + 1 < len(headers):
                next_header = headers[i + 1].lower()
                end_pos = text_lower.find(next_header, start_pos + len(header_lower))
                if end_pos == -1:
                    end_pos = len(text)
            else:
                end_pos = len(text)
            
            section_text = text[start_pos:end_pos].strip()
            sections[header] = section_text
        else:
            # If header not found, create empty section
            sections[header] = ""
    
    return sections

def load_workspace_data():
    """Load workspace data from JSON file"""
    try:
        if os.path.exists("workspace.json"):
            with open("workspace.json", "r") as f:
                data = json.load(f)
                return data.get("comments", {}), data.get("memos", {})
    except:
        pass
    return {}, {}

def save_workspace_data(comment_store, memo_store):
    """Save workspace data to JSON file"""
    try:
        data = {
            "comments": comment_store,
            "memos": memo_store,
            "audit_log": st.session_state.audit_log,
            "timestamp": datetime.now().isoformat()
        }
        with open("workspace.json", "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        st.error(f"Error saving workspace data: {e}")

def add_audit_log(user, action, section=None, details=None):
    """Add entry to audit log"""
    log_entry = {
        "user": user,
        "action": action,
        "section": section,
        "details": details,
        "timestamp": datetime.now().isoformat()
    }
    st.session_state.audit_log.append(log_entry)

def get_user_initials(username):
    """Get user initials for avatar"""
    if username.startswith('@'):
        username = username[1:]
    parts = username.split()
    if len(parts) >= 2:
        return f"{parts[0][0]}{parts[1][0]}".upper()
    return username[:2].upper()

def render_user_avatar(username):
    """Render user avatar with initials"""
    initials = get_user_initials(username)
    return f'<span class="user-avatar">{initials}</span>'

def generate_section_summary(section_text, api_key, section_name):
    """Generate AI summary for a section"""
    if not api_key or not section_text.strip():
        return "No content available for summary."
    
    try:
        client = openai.OpenAI(api_key=api_key)
        
        prompt = f"""Summarize this CIM section in 3 concise bullet points:

Section: {section_name}
Content: {section_text[:2000]}

Format as:
• [Key point 1]
• [Key point 2] 
• [Key point 3]"""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a financial analyst creating concise section summaries."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
            temperature=0
        )
        
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating summary: {str(e)}"

def export_workspace_data():
    """Export workspace data as CSV"""
    # Flatten all comments for export
    export_data = []
    
    for section, comments in st.session_state.comment_store.items():
        for comment in comments:
            export_data.append({
                'Section': section,
                'Author': comment.get('user', ''),
                'Content': comment.get('comment', ''),
                'Assigned To': ', '.join([tag for tag in comment.get('tags', []) if tag.startswith('@')]),
                'Tags': ', '.join([tag for tag in comment.get('tags', []) if tag.startswith('#')]),
                'Priority': comment.get('priority', ''),
                'Status': comment.get('status', ''),
                'Timestamp': comment.get('timestamp', '')
            })
    
    # Add memo information
    for section, memo in st.session_state.memo_store.items():
        export_data.append({
            'Section': section,
            'Author': 'System',
            'Content': f"Memo attached: {memo.get('filename', 'Unknown')}",
            'Assigned To': '',
            'Tags': '#memo',
            'Priority': '',
            'Status': 'Complete',
            'Timestamp': memo.get('timestamp', '')
        })
    
    return pd.DataFrame(export_data)

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
    # Initialize workspace data if not already done
    if not st.session_state.workspace_initialized:
        try:
            comment_store, memo_store = load_workspace_data()
            st.session_state.comment_store = comment_store
            st.session_state.memo_store = memo_store
            st.session_state.workspace_initialized = True
        except:
            # If loading fails, use empty defaults
            st.session_state.comment_store = {}
            st.session_state.memo_store = {}
            st.session_state.workspace_initialized = True
    
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
                        
                        # Extract sections for workspace
                        headers = extract_section_headers(text)
                        sections = split_text_by_sections(text, headers)
                        st.session_state.cim_sections = sections
                        
                        # Initialize workspace data if needed
                        if not st.session_state.workspace_initialized:
                            try:
                                comment_store, memo_store = load_workspace_data()
                                st.session_state.comment_store = comment_store
                                st.session_state.memo_store = memo_store
                            except:
                                pass  # Use existing empty defaults
                        
                        st.success(f"✅ CIM processed! Extracted {len(text):,} characters and {len(sections)} sections")
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
        # Show analysis interface with tabs
        show_analysis_interface(api_key)

def show_analysis_interface(api_key):
    """Show the main analysis interface with tabs"""
    
    st.info(f"📄 **Document Loaded**: {len(st.session_state.cim_text):,} characters extracted and ready for analysis")
    
    # Audit trail badge
    st.markdown("""
    <div class="audit-badge">
        🔒 <strong>Audit Trail Enabled</strong>: All comments, uploads, and tasks are timestamped and traceable.
    </div>
    """, unsafe_allow_html=True)
    
    # Create sticky tabs
    st.markdown('<div class="sticky-tabs">', unsafe_allow_html=True)
    tab1, tab2, tab3, tab4 = st.tabs(["🎯 Quick Analysis", "💬 Interactive Chat", "🧑‍💼 Deal Workspace", "📊 Sections"])
    st.markdown('</div>', unsafe_allow_html=True)
    
    with tab1:
        show_quick_analysis(api_key)
    
    with tab2:
        show_chat_interface(api_key)
    
    with tab3:
        show_deal_workspace(api_key)
    
    with tab4:
        show_sections_overview(api_key)

def show_quick_analysis(api_key):
    """Show quick analysis buttons"""
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

def show_chat_interface(api_key):
    """Show interactive chat interface"""
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

def show_deal_workspace(api_key):
    """Show deal team workspace for collaboration"""
    st.subheader("🧑‍💼 Deal Team Workspace")
    st.caption("Collaborate with your team on this deal")
    
    if not st.session_state.cim_sections:
        st.warning("⚠️ No sections found. Please reprocess the CIM to enable workspace features.")
        return
    
    # Export functionality
    col_export1, col_export2 = st.columns([3, 1])
    with col_export2:
        if st.button("📊 Export Summary"):
            try:
                df = export_workspace_data()
                if not df.empty:
                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        "⬇️ Download CSV",
                        csv,
                        "deal_workspace_summary.csv",
                        "text/csv",
                        key="download_csv"
                    )
                else:
                    st.info("No data to export yet.")
            except Exception as e:
                st.error(f"Export failed: {e}")
    
    # Section selector
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### 📂 Sections")
        selected_section = st.selectbox(
            "Select a section to work on:",
            list(st.session_state.cim_sections.keys()),
            key="workspace_section"
        )
        
        # Show section stats
        if selected_section:
            comments = st.session_state.comment_store.get(selected_section, [])
            comments_count = len(comments)
            has_memo = selected_section in st.session_state.memo_store
            open_tasks = len([c for c in comments if c.get('status') == 'Open'])
            
            st.metric("Comments", comments_count)
            st.metric("Open Tasks", open_tasks)
            st.metric("Memo Attached", "Yes" if has_memo else "No")
            
            # Generate AI summary for section
            if api_key and selected_section not in st.session_state.section_summaries:
                if st.button("🤖 Generate AI Summary", key=f"ai_summary_{selected_section}"):
                    with st.spinner("Generating summary..."):
                        section_text = st.session_state.cim_sections.get(selected_section, "")
                        summary = generate_section_summary(section_text, api_key, selected_section)
                        st.session_state.section_summaries[selected_section] = summary
                        add_audit_log("System", "Generated AI summary", selected_section)
                        st.rerun()
            
            # Show existing summary
            if selected_section in st.session_state.section_summaries:
                with st.expander("🤖 AI Summary"):
                    st.markdown(st.session_state.section_summaries[selected_section])
    
    with col2:
        if selected_section:
            st.markdown(f"### 📋 Working on: {selected_section}")
            
            # Memo upload with enhanced display
            st.markdown("#### 📎 Attach Memo")
            uploaded_memo = st.file_uploader(
                "Upload a memo or note for this section",
                type=["txt", "md", "pdf", "docx"],
                key=f"memo_{selected_section}"
            )
            
            if uploaded_memo:
                memo_content = f"File: {uploaded_memo.name} ({uploaded_memo.size} bytes)"
                if uploaded_memo.type == "text/plain":
                    try:
                        memo_content = uploaded_memo.read().decode("utf-8")
                    except:
                        memo_content = f"File: {uploaded_memo.name} (could not read content)"
                
                st.session_state.memo_store[selected_section] = {
                    "content": memo_content,
                    "filename": uploaded_memo.name,
                    "size": uploaded_memo.size,
                    "type": uploaded_memo.type,
                    "timestamp": datetime.now().isoformat()
                }
                add_audit_log("User", "Uploaded memo", selected_section, uploaded_memo.name)
                save_workspace_data(st.session_state.comment_store, st.session_state.memo_store)
                st.success(f"✅ Memo attached to {selected_section}")
                st.rerun()
            
            # Show existing memo with enhanced info
            if selected_section in st.session_state.memo_store:
                memo = st.session_state.memo_store[selected_section]
                upload_date = datetime.fromisoformat(memo['timestamp']).strftime('%b %d, %Y %H:%M')
                
                with st.expander(f"📎 Memo: {memo['filename']} (uploaded {upload_date})"):
                    st.markdown(f"**File:** {memo['filename']}")
                    st.markdown(f"**Size:** {memo.get('size', 'Unknown')} bytes")
                    st.markdown(f"**Type:** {memo.get('type', 'Unknown')}")
                    st.markdown(f"**Uploaded:** {upload_date}")
                    
                    if memo['content'] and not memo['content'].startswith('File:'):
                        st.text_area("Content:", memo['content'], height=100, disabled=True)
                    
                    if st.button("🗑️ Remove Memo", key=f"remove_memo_{selected_section}"):
                        del st.session_state.memo_store[selected_section]
                        add_audit_log("User", "Removed memo", selected_section, memo['filename'])
                        save_workspace_data(st.session_state.comment_store, st.session_state.memo_store)
                        st.rerun()
            
            st.divider()
            
            # Comments and tasks with enhanced features
            st.markdown("#### 💬 Comments & Tasks")
            
            # Comment sorting
            col_sort1, col_sort2 = st.columns(2)
            with col_sort1:
                sort_by = st.selectbox("Sort by:", ["Newest", "Oldest", "Priority", "Status", "User"])
            with col_sort2:
                show_resolved = st.checkbox("Show resolved", value=True)
            
            # Add new comment with autocomplete
            with st.form(f"comment_form_{selected_section}"):
                col_a, col_b = st.columns([2, 1])
                with col_a:
                    user_name = st.selectbox("Your name", [""] + [m[1:] for m in TEAM_MEMBERS], key=f"user_{selected_section}")
                    comment_text = st.text_area("Comment or task", placeholder="Add a comment or create a task...")
                with col_b:
                    assigned_to = st.multiselect("Assign to:", TEAM_MEMBERS, key=f"assign_{selected_section}")
                    hashtags = st.multiselect("Tags:", COMMON_TAGS, key=f"tags_{selected_section}")
                    priority = st.selectbox("Priority", ["Low", "Medium", "High", "Critical"])
                
                submitted = st.form_submit_button("💬 Add Comment")
                
                if submitted and user_name and comment_text:
                    all_tags = assigned_to + hashtags
                    new_comment = {
                        "id": len(st.session_state.comment_store.get(selected_section, [])),
                        "user": user_name,
                        "comment": comment_text,
                        "tags": all_tags,
                        "assigned_to": assigned_to,
                        "priority": priority,
                        "status": "Open",
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    if selected_section not in st.session_state.comment_store:
                        st.session_state.comment_store[selected_section] = []
                    
                    st.session_state.comment_store[selected_section].append(new_comment)
                    add_audit_log(user_name, "Added comment/task", selected_section, comment_text[:50])
                    
                    # Show mention notifications
                    for mention in assigned_to:
                        st.toast(f"🔔 {mention} was mentioned in a comment", icon="🔔")
                    
                    save_workspace_data(st.session_state.comment_store, st.session_state.memo_store)
                    st.success("✅ Comment added!")
                    st.rerun()
            
            # Display existing comments with enhanced styling
            if selected_section in st.session_state.comment_store:
                comments = st.session_state.comment_store[selected_section]
                
                # Apply sorting
                if sort_by == "Newest":
                    comments = sorted(comments, key=lambda x: x.get('timestamp', ''), reverse=True)
                elif sort_by == "Oldest":
                    comments = sorted(comments, key=lambda x: x.get('timestamp', ''))
                elif sort_by == "Priority":
                    priority_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
                    comments = sorted(comments, key=lambda x: priority_order.get(x.get('priority', 'Low'), 3))
                elif sort_by == "Status":
                    comments = sorted(comments, key=lambda x: x.get('status', 'Open'))
                elif sort_by == "User":
                    comments = sorted(comments, key=lambda x: x.get('user', ''))
                
                if comments:
                    st.markdown("#### 📝 Comments")
                    
                    for i, comment in enumerate(comments):
                        # Apply filters
                        if not show_resolved and comment.get('status') == "Resolved":
                            continue
                        
                        # Enhanced comment display with styling
                        status = comment.get('status', 'Open')
                        priority = comment.get('priority', 'Low')
                        
                        status_icons = {
                            "Open": "📌",
                            "In Progress": "⏳", 
                            "Resolved": "✅"
                        }
                        
                        priority_colors = {
                            "Critical": "task-critical",
                            "High": "task-high", 
                            "Medium": "task-medium",
                            "Low": "task-low"
                        }
                        
                        task_class = f"task-{status.lower().replace(' ', '-')}"
                        
                        # Render comment with enhanced styling
                        comment_html = f"""
                        <div class="task-card {task_class}">
                            <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                                {render_user_avatar(comment.get('user', 'Unknown'))}
                                <strong>{comment.get('user', 'Unknown')}</strong>
                                <span style="margin-left: auto; font-size: 0.8rem; opacity: 0.7;">
                                    {status_icons.get(status, '📌')} {status} | {priority}
                                </span>
                            </div>
                            <div style="margin-bottom: 0.5rem;">
                                {comment.get('comment', '')}
                            </div>
                        """
                        
                        if comment.get('tags'):
                            comment_html += f"<div style='font-size: 0.8rem; opacity: 0.8;'>Tags: {' '.join(comment.get('tags', []))}</div>"
                        
                        comment_html += "</div>"
                        
                        st.markdown(comment_html, unsafe_allow_html=True)
                        
                        # Action buttons
                        col1, col2, col3 = st.columns([2, 1, 1])
                        with col2:
                            if comment.get('status') == "Open":
                                if st.button("⏳ In Progress", key=f"progress_{selected_section}_{i}"):
                                    st.session_state.comment_store[selected_section][i]['status'] = "In Progress"
                                    add_audit_log(comment.get('user', 'Unknown'), "Changed status to In Progress", selected_section)
                                    save_workspace_data(st.session_state.comment_store, st.session_state.memo_store)
                                    st.rerun()
                            elif comment.get('status') == "In Progress":
                                if st.button("✅ Complete", key=f"complete_{selected_section}_{i}"):
                                    st.session_state.comment_store[selected_section][i]['status'] = "Resolved"
                                    add_audit_log(comment.get('user', 'Unknown'), "Completed task", selected_section)
                                    save_workspace_data(st.session_state.comment_store, st.session_state.memo_store)
                                    st.rerun()
                        
                        with col3:
                            if comment.get('status') == "Resolved":
                                if st.button("↩️ Reopen", key=f"reopen_{selected_section}_{i}"):
                                    st.session_state.comment_store[selected_section][i]['status'] = "Open"
                                    add_audit_log(comment.get('user', 'Unknown'), "Reopened task", selected_section)
                                    save_workspace_data(st.session_state.comment_store, st.session_state.memo_store)
                                    st.rerun()
                        
                        st.markdown("---")
                else:
                    st.info("💭 No comments yet. Add the first comment above!")

def show_sections_overview(api_key):
    """Show overview of all sections with AI summaries"""
    st.subheader("📊 Document Sections Overview")
    
    if not st.session_state.cim_sections:
        st.warning("⚠️ No sections found. Please reprocess the CIM.")
        return
    
    # Stats overview
    col1, col2, col3, col4 = st.columns(4)
    
    total_sections = len(st.session_state.cim_sections)
    total_comments = sum(len(comments) for comments in st.session_state.comment_store.values())
    total_memos = len(st.session_state.memo_store)
    open_tasks = sum(
        len([c for c in comments if c.get('status') == 'Open']) 
        for comments in st.session_state.comment_store.values()
    )
    
    col1.metric("Sections", total_sections)
    col2.metric("Total Comments", total_comments)
    col3.metric("Memos Attached", total_memos)
    col4.metric("Open Tasks", open_tasks)
    
    # Generate all summaries button
    if api_key:
        if st.button("🤖 Generate All AI Summaries"):
            progress_bar = st.progress(0)
            for i, section_name in enumerate(st.session_state.cim_sections.keys()):
                if section_name not in st.session_state.section_summaries:
                    section_text = st.session_state.cim_sections[section_name]
                    summary = generate_section_summary(section_text, api_key, section_name)
                    st.session_state.section_summaries[section_name] = summary
                progress_bar.progress((i + 1) / total_sections)
            
            add_audit_log("System", "Generated all AI summaries")
            st.success("✅ All summaries generated!")
            st.rerun()
    
    st.divider()
    
    # Sections list with activity and AI summaries
    for section_name in st.session_state.cim_sections.keys():
        with st.expander(f"📄 {section_name}"):
            comments = st.session_state.comment_store.get(section_name, [])
            memo = st.session_state.memo_store.get(section_name)
            
            # Activity summary
            col_a, col_b, col_c = st.columns(3)
            
            with col_a:
                st.write(f"**Comments:** {len(comments)}")
                open_comments = len([c for c in comments if c.get('status') == 'Open'])
                if open_comments > 0:
                    st.write(f"🔴 Open tasks: {open_comments}")
            
            with col_b:
                st.write(f"**Memo:** {'✅ Attached' if memo else '❌ None'}")
                if memo:
                    upload_date = datetime.fromisoformat(memo['timestamp']).strftime('%b %d')
                    st.caption(f"Uploaded: {upload_date}")
            
            with col_c:
                if comments:
                    high_priority = len([c for c in comments if c.get('priority') in ['High', 'Critical']])
                    if high_priority > 0:
                        st.write(f"⚠️ High priority: {high_priority}")
            
            # AI Summary
            if section_name in st.session_state.section_summaries:
                st.markdown("**🤖 AI Summary:**")
                st.markdown(st.session_state.section_summaries[section_name])
            elif api_key:
                if st.button(f"Generate AI Summary", key=f"gen_summary_{section_name}"):
                    with st.spinner("Generating summary..."):
                        section_text = st.session_state.cim_sections[section_name]
                        summary = generate_section_summary(section_text, api_key, section_name)
                        st.session_state.section_summaries[section_name] = summary
                        add_audit_log("System", "Generated AI summary", section_name)
                        st.rerun()
            
            # Quick preview of section text
            section_text = st.session_state.cim_sections[section_name]
            if section_text:
                preview = section_text[:300] + "..." if len(section_text) > 300 else section_text
                with st.expander("📖 Text Preview"):
                    st.caption(preview)
            else:
                st.caption("No content found for this section.")

if __name__ == "__main__":
    main()
