import streamlit as st
import PyPDF2
from datetime import datetime
from utils.database import init_database, save_cim_to_database, log_audit_action
from utils.ai_analysis import extract_section_headers, split_text_by_sections, detect_red_flags, extract_valuation_metrics
from utils.session_state import initialize_session_state
from utils.styling import apply_custom_css

# Page config
st.set_page_config(
    page_title="Auctum Enterprise", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize everything
apply_custom_css()
init_database()
initialize_session_state()

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

def main():
    # Main title
    st.markdown('<h1 class="main-title">Auctum Enterprise</h1>', unsafe_allow_html=True)

    # Compliance mode toggle
    col1, col2, col3 = st.columns([2, 1, 1])
    with col2:
        try:
            from cryptography.fernet import Fernet
            ENCRYPTION_AVAILABLE = True
        except ImportError:
            ENCRYPTION_AVAILABLE = False
            
        if ENCRYPTION_AVAILABLE:
            compliance_enabled = st.toggle("🔒 Compliance Mode", value=st.session_state.compliance_mode)
            if compliance_enabled != st.session_state.compliance_mode:
                st.session_state.compliance_mode = compliance_enabled
                log_audit_action(f"Compliance Mode {'Enabled' if compliance_enabled else 'Disabled'}")
                st.rerun()
        else:
            st.button("🔒 Compliance Mode", disabled=True, help="Requires cryptography library")
    
    with col3:
        if st.session_state.compliance_mode and ENCRYPTION_AVAILABLE:
            st.markdown('<div class="compliance-badge">🔒 COMPLIANCE ACTIVE</div>', unsafe_allow_html=True)
        elif not ENCRYPTION_AVAILABLE:
            st.caption("⚠️ Encryption unavailable on cloud")
    
    # Privacy note
    privacy_text = """
    <div class="privacy-note">
        <strong>🔐 Privacy & Security</strong><br>
        Your documents are processed securely and never stored on external servers. All analysis uses enterprise-grade AI with full compliance.
    """
    
    try:
        from cryptography.fernet import Fernet
        if st.session_state.compliance_mode:
            privacy_text += """<br><strong>Compliance Mode Active:</strong> All documents encrypted, full audit logging enabled, user access controls enforced."""
    except ImportError:
        privacy_text += """<br><strong>Note:</strong> Full encryption features require local deployment. Cloud version uses secure processing without encryption."""
    
    privacy_text += "</div>"
    st.markdown(privacy_text, unsafe_allow_html=True)
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # User info
        st.markdown(f"**User:** {st.session_state.current_user}")
        st.markdown(f"**Role:** {st.session_state.user_role.title()}")
        
        st.divider()
        
        # OpenAI API Key
        api_key = st.text_input(
            "OpenAI API Key", 
            type="password",
            help="Enter your OpenAI API key"
        )
        
        if api_key:
            st.session_state.api_key = api_key
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
                        # Save to database
                        cim_id = save_cim_to_database(uploaded_file.name, text, st.session_state.current_user)
                        st.session_state.current_cim_id = cim_id
                        st.session_state.cim_text = text
                        
                        # Extract sections
                        headers = extract_section_headers(text)
                        sections = split_text_by_sections(text, headers)
                        st.session_state.cim_sections = sections
                        
                        # Detect red flags
                        red_flags = detect_red_flags(text, api_key)
                        st.session_state.red_flags = red_flags
                        
                        # Extract valuation metrics
                        valuation_data = extract_valuation_metrics(text, api_key)
                        st.session_state.valuation_data = valuation_data
                        
                        st.success(f"✅ CIM processed! Extracted {len(text):,} characters, {len(sections)} sections, {len(red_flags)} red flags detected")
                        st.rerun()
    
    # Main content area
    if st.session_state.cim_text is None:
        # Welcome screen
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("### 🚀 Welcome to Auctum Enterprise")
            
            with st.container():
                st.markdown("**🧑‍💼 Deal Team Workspace**")
                st.write("Advanced team collaboration with comments, tasks, and memo management")
                
                st.markdown("**📋 IC Memo Generator**") 
                st.write("AI-powered investment committee memo generation from CIM content")
                
                st.markdown("**🚨 Red Flag Tracker**")
                st.write("Automatic detection of inconsistencies and potential issues")
                
                st.markdown("**🗂️ Data Room Integration**")
                st.write("Seamless sync with Box, Dropbox, iDeals, and other platforms")
                
                st.markdown("**💰 Valuation Snapshot**")
                st.write("Automated extraction and visualization of key financial metrics")
                
                st.markdown("**🔒 Compliance Mode**")
                st.write("Enterprise-grade security with encryption and audit logging")
                
                st.divider()
                
                st.markdown("#### Getting Started")
                st.write("1. Enter your OpenAI API key in the sidebar")
                st.write("2. Upload a CIM PDF file") 
                st.write("3. Click 'Process CIM' to analyze")
                st.write("4. Navigate to different pages using the sidebar to access all enterprise features!")
                
                # Quick navigation
                st.markdown("#### 🚀 Quick Navigation")
                col_nav1, col_nav2 = st.columns(2)
                
                with col_nav1:
                    if st.button("🧑‍💼 Go to Deal Workspace", use_container_width=True):
                        st.switch_page("pages/Deal_Team.py")
                    if st.button("🚨 View Red Flags", use_container_width=True):
                        st.switch_page("pages/Red_Flag_Tracker.py")
                
                with col_nav2:
                    if st.button("📋 Generate IC Memo", use_container_width=True):
                        st.switch_page("pages/IC_Memo.py")
                    if st.button("💰 Check Valuation", use_container_width=True):
                        st.switch_page("pages/Valuation_Snapshot.py")
    else:
        # Show document loaded status and navigation
        st.info(f"📄 **Document Loaded**: {len(st.session_state.cim_text):,} characters | {len(st.session_state.red_flags)} red flags detected | Use sidebar navigation to access features")
        
        # Feature overview with navigation
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("### 🧑‍💼 Deal Team")
            st.write("Collaborate on sections, assign tasks, manage workflow")
            if st.button("→ Open Deal Workspace", key="nav_deal"):
                st.switch_page("pages/Deal_Team.py")
        
        with col2:
            st.markdown("### 📋 IC Memo")
            st.write("Generate investment committee memos with AI")
            if st.button("→ Generate Memo", key="nav_memo"):
                st.switch_page("pages/IC_Memo.py")
        
        with col3:
            st.markdown("### 🚨 Risk Analysis")
            st.write(f"{len(st.session_state.red_flags)} potential red flags detected")
            if st.button("→ View Red Flags", key="nav_flags"):
                st.switch_page("pages/Red_Flag_Tracker.py")
        
        st.divider()
        
        # Additional features
        col4, col5 = st.columns(2)
        
        with col4:
            st.markdown("### 💰 Valuation")
            metrics_count = len([k for k, v in st.session_state.valuation_data.items() if v is not None])
            st.write(f"{metrics_count} financial metrics extracted")
            if st.button("→ View Valuation", key="nav_val"):
                st.switch_page("pages/Valuation_Snapshot.py")
        
        with col5:
            st.markdown("### 🗂️ Data Room")
            st.write("Sync with external document sources")
            if st.button("→ Manage Data Room", key="nav_data"):
                st.switch_page("pages/Data_Room.py")

if __name__ == "__main__":
    main()
