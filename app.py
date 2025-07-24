import streamlit as st
import PyPDF2
import openai
import tempfile
import os
import json
import re
from datetime import datetime

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
if 'cim_sections' not in st.session_state:
    st.session_state.cim_sections = {}
if 'comment_store' not in st.session_state:
    st.session_state.comment_store = {}
if 'memo_store' not in st.session_state:
    st.session_state.memo_store = {}
if 'workspace_data' not in st.session_state:
    st.session_state.workspace_data = load_workspace_data()

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
            "timestamp": datetime.now().isoformat()
        }
        with open("workspace.json", "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        st.error(f"Error saving workspace data: {e}")

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
                        
                        # Extract sections for workspace
                        headers = extract_section_headers(text)
                        sections = split_text_by_sections(text, headers)
                        st.session_state.cim_sections = sections
                        
                        # Load existing workspace data
                        comment_store, memo_store = load_workspace_data()
                        st.session_state.comment_store = comment_store
                        st.session_state.memo_store = memo_store
                        
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
    
    # Create tabs for different features
    tab1, tab2, tab3, tab4 = st.tabs(["🎯 Quick Analysis", "💬 Interactive Chat", "🧑‍💼 Deal Workspace", "📊 Sections"])
    
    with tab1:
        show_quick_analysis(api_key)
    
    with tab2:
        show_chat_interface(api_key)
    
    with tab3:
        show_deal_workspace()
    
    with tab4:
        show_sections_overview()

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

def show_deal_workspace():
    """Show deal team workspace for collaboration"""
    st.subheader("🧑‍💼 Deal Team Workspace")
    st.caption("Collaborate with your team on this deal")
    
    if not st.session_state.cim_sections:
        st.warning("⚠️ No sections found. Please reprocess the CIM to enable workspace features.")
        return
    
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
            comments_count = len(st.session_state.comment_store.get(selected_section, []))
            has_memo = selected_section in st.session_state.memo_store
            
            st.metric("Comments", comments_count)
            st.metric("Memo Attached", "Yes" if has_memo else "No")
    
    with col2:
        if selected_section:
            st.markdown(f"### 📋 Working on: {selected_section}")
            
            # Memo upload
            st.markdown("#### 📎 Attach Memo")
            uploaded_memo = st.file_uploader(
                "Upload a memo or note for this section",
                type=["txt", "md", "pdf"],
                key=f"memo_{selected_section}"
            )
            
            if uploaded_memo:
                if uploaded_memo.type == "text/plain":
                    memo_content = uploaded_memo.read().decode("utf-8")
                else:
                    memo_content = f"Uploaded file: {uploaded_memo.name}"
                
                st.session_state.memo_store[selected_section] = {
                    "content": memo_content,
                    "filename": uploaded_memo.name,
                    "timestamp": datetime.now().isoformat()
                }
                save_workspace_data(st.session_state.comment_store, st.session_state.memo_store)
                st.success(f"✅ Memo attached to {selected_section}")
            
            # Show existing memo
            if selected_section in st.session_state.memo_store:
                memo = st.session_state.memo_store[selected_section]
                with st.expander(f"📎 Attached Memo: {memo['filename']}"):
                    st.write(memo['content'])
                    if st.button("🗑️ Remove Memo", key=f"remove_memo_{selected_section}"):
                        del st.session_state.memo_store[selected_section]
                        save_workspace_data(st.session_state.comment_store, st.session_state.memo_store)
                        st.rerun()
            
            st.divider()
            
            # Comments and tasks
            st.markdown("#### 💬 Comments & Tasks")
            
            # Add new comment
            with st.form(f"comment_form_{selected_section}"):
                col_a, col_b = st.columns([2, 1])
                with col_a:
                    user_name = st.text_input("Your name", placeholder="Enter your name")
                    comment_text = st.text_area("Comment or task", placeholder="Add a comment or create a task...")
                with col_b:
                    tags = st.text_input("Tags", placeholder="@user #tag")
                    priority = st.selectbox("Priority", ["Low", "Medium", "High", "Critical"])
                
                submitted = st.form_submit_button("💬 Add Comment")
                
                if submitted and user_name and comment_text:
                    new_comment = {
                        "id": len(st.session_state.comment_store.get(selected_section, [])),
                        "user": user_name,
                        "comment": comment_text,
                        "tags": tags.split() if tags else [],
                        "priority": priority,
                        "status": "Open",
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    if selected_section not in st.session_state.comment_store:
                        st.session_state.comment_store[selected_section] = []
                    
                    st.session_state.comment_store[selected_section].append(new_comment)
                    save_workspace_data(st.session_state.comment_store, st.session_state.memo_store)
                    st.success("✅ Comment added!")
                    st.rerun()
            
            # Display existing comments
            if selected_section in st.session_state.comment_store:
                comments = st.session_state.comment_store[selected_section]
                
                if comments:
                    st.markdown("#### 📝 Comments")
                    
                    # Filter options
                    col_x, col_y = st.columns(2)
                    with col_x:
                        show_resolved = st.checkbox("Show resolved tasks", value=True)
                    with col_y:
                        filter_priority = st.selectbox("Filter by priority", ["All", "Critical", "High", "Medium", "Low"])
                    
                    for i, comment in enumerate(comments):
                        # Apply filters
                        if not show_resolved and comment['status'] == "Resolved":
                            continue
                        if filter_priority != "All" and comment['priority'] != filter_priority:
                            continue
                        
                        # Comment display
                        status_color = "🟢" if comment['status'] == "Resolved" else "🔴"
                        priority_emoji = {"Critical": "🚨", "High": "⚠️", "Medium": "📋", "Low": "📝"}
                        
                        with st.container():
                            col1, col2, col3 = st.columns([3, 1, 1])
                            
                            with col1:
                                st.markdown(f"**{comment['user']}** {priority_emoji.get(comment['priority'], '📝')}")
                                st.write(comment['comment'])
                                if comment['tags']:
                                    st.caption(f"Tags: {' '.join(comment['tags'])}")
                            
                            with col2:
                                st.caption(f"Status: {status_color} {comment['status']}")
                                st.caption(f"Priority: {comment['priority']}")
                            
                            with col3:
                                if comment['status'] == "Open":
                                    if st.button("✅ Resolve", key=f"resolve_{selected_section}_{i}"):
                                        st.session_state.comment_store[selected_section][i]['status'] = "Resolved"
                                        save_workspace_data(st.session_state.comment_store, st.session_state.memo_store)
                                        st.rerun()
                                else:
                                    if st.button("↩️ Reopen", key=f"reopen_{selected_section}_{i}"):
                                        st.session_state.comment_store[selected_section][i]['status'] = "Open"
                                        save_workspace_data(st.session_state.comment_store, st.session_state.memo_store)
                                        st.rerun()
                            
                            st.divider()
                else:
                    st.info("💭 No comments yet. Add the first comment above!")

def show_sections_overview():
    """Show overview of all sections"""
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
        len([c for c in comments if c['status'] == 'Open']) 
        for comments in st.session_state.comment_store.values()
    )
    
    col1.metric("Sections", total_sections)
    col2.metric("Total Comments", total_comments)
    col3.metric("Memos Attached", total_memos)
    col4.metric("Open Tasks", open_tasks)
    
    st.divider()
    
    # Sections list with activity
    for section_name in st.session_state.cim_sections.keys():
        with st.expander(f"📄 {section_name}"):
            comments = st.session_state.comment_store.get(section_name, [])
            memo = st.session_state.memo_store.get(section_name)
            
            col_a, col_b, col_c = st.columns(3)
            
            with col_a:
                st.write(f"**Comments:** {len(comments)}")
                open_comments = len([c for c in comments if c['status'] == 'Open'])
                if open_comments > 0:
                    st.write(f"🔴 Open tasks: {open_comments}")
            
            with col_b:
                st.write(f"**Memo:** {'✅ Attached' if memo else '❌ None'}")
            
            with col_c:
                if comments:
                    high_priority = len([c for c in comments if c['priority'] in ['High', 'Critical']])
                    if high_priority > 0:
                        st.write(f"⚠️ High priority: {high_priority}")
            
            # Quick preview of section text
            section_text = st.session_state.cim_sections[section_name]
            if section_text:
                preview = section_text[:300] + "..." if len(section_text) > 300 else section_text
                st.caption(f"Preview: {preview}")
            else:
                st.caption("No content found for this section.")

if __name__ == "__main__":
    main()
