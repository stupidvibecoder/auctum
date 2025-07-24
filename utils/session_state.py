import streamlit as st

# Team members and tags for autocomplete
TEAM_MEMBERS = ['@Alex', '@Rishi', '@Jordan', '@Sam', '@Taylor', '@Morgan']
COMMON_TAGS = ['#Modeling', '#Legal', '#KeyAssumption', '#Revenue', '#EBITDA', '#Risk', '#Market', '#Management']

def initialize_session_state():
    """Initialize all session state variables"""
    
    # Core document data
    if 'cim_text' not in st.session_state:
        st.session_state.cim_text = None
    if 'cim_sections' not in st.session_state:
        st.session_state.cim_sections = {}
    if 'current_cim_id' not in st.session_state:
        st.session_state.current_cim_id = None
    
    # Chat and interaction
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'api_key' not in st.session_state:
        st.session_state.api_key = None
    
    # Deal workspace data
    if 'comment_store' not in st.session_state:
        st.session_state.comment_store = {}
    if 'memo_store' not in st.session_state:
        st.session_state.memo_store = {}
    if 'workspace_initialized' not in st.session_state:
        st.session_state.workspace_initialized = False
    
    # AI analysis results
    if 'section_summaries' not in st.session_state:
        st.session_state.section_summaries = {}
    if 'red_flags' not in st.session_state:
        st.session_state.red_flags = []
    if 'valuation_data' not in st.session_state:
        st.session_state.valuation_data = {}
    
    # IC memo content
    if 'ic_memo' not in st.session_state:
        st.session_state.ic_memo = {}
    
    # Compliance and audit
    if 'compliance_mode' not in st.session_state:
        st.session_state.compliance_mode = False
    if 'audit_log' not in st.session_state:
        st.session_state.audit_log = []
    
    # User management
    if 'current_user' not in st.session_state:
        st.session_state.current_user = "demo_user"
    if 'user_role' not in st.session_state:
        st.session_state.user_role = "admin"

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

def check_document_loaded():
    """Check if a document is loaded and show appropriate message"""
    if st.session_state.cim_text is None:
        st.warning("⚠️ No document loaded. Please upload and process a CIM document from the Home page.")
        if st.button("🏠 Go to Home"):
            st.switch_page("Home.py")
        return False
    return True

def get_api_key():
    """Get API key from session state or prompt for it"""
    if 'api_key' not in st.session_state or not st.session_state.api_key:
        st.warning("⚠️ OpenAI API key required. Please configure it on the Home page.")
        return None
    return st.session_state.api_key
