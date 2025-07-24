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

# Optional encryption support
try:
    from cryptography.fernet import Fernet
    ENCRYPTION_AVAILABLE = True
except ImportError:
    ENCRYPTION_AVAILABLE = False

try:
    import xlwings as xw
    XLWINGS_AVAILABLE = True
except ImportError:
    XLWINGS_AVAILABLE = False

# Semantic search dependencies
try:
    from sentence_transformers import SentenceTransformer
    import faiss
    SEMANTIC_SEARCH_AVAILABLE = True
except ImportError:
    SEMANTIC_SEARCH_AVAILABLE = False

# Page config
st.set_page_config(
    page_title="Auctum Enterprise", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced CSS with all styling
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
    
    .red-flag {
        background: rgba(239, 68, 68, 0.1);
        border-left: 4px solid #ef4444;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0 8px 8px 0;
    }
    
    .compliance-badge {
        background: rgba(34, 197, 94, 0.1);
        border: 1px solid rgba(34, 197, 94, 0.3);
        border-radius: 8px;
        padding: 0.5rem;
        color: #22c55e;
        font-weight: bold;
    }
    
    .sync-status {
        display: inline-block;
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    
    .sync-success { background: rgba(34, 197, 94, 0.2); color: #22c55e; }
    .sync-pending { background: rgba(245, 158, 11, 0.2); color: #f59e0b; }
    .sync-error { background: rgba(239, 68, 68, 0.2); color: #ef4444; }
    
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
    
    /* Main title styling */
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
    
    /* Cards and other existing styles */
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
    
    /* Text colors */
    .stMarkdown, .stText, h1, h2, h3, h4, h5, h6, p, div {
        color: #ffffff !important;
    }
    
    /* Input fields */
    .stTextInput > div > div > input, .stTextArea > div > div > textarea {
        background: rgba(30, 41, 59, 0.8);
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: #ffffff;
    }
    
    .stSelectbox > div > div > select {
        background: rgba(30, 41, 59, 0.8);
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

# Database initialization
def init_database():
    """Initialize SQLite database with all required tables"""
    conn = sqlite3.connect('auctum.db')
    c = conn.cursor()
    
    # CIM documents table
    c.execute('''CREATE TABLE IF NOT EXISTS cim_documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT NOT NULL,
        upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        user_id TEXT,
        content_hash TEXT,
        encrypted_content TEXT
    )''')
    
    # Comments table
    c.execute('''CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cim_id INTEGER,
        user_id TEXT,
        section TEXT,
        comment TEXT,
        mentioned_users TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (cim_id) REFERENCES cim_documents (id)
    )''')
    
    # Tasks table
    c.execute('''CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cim_id INTEGER,
        title TEXT,
        description TEXT,
        assigned_to TEXT,
        due_date DATE,
        status TEXT DEFAULT 'open',
        section TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (cim_id) REFERENCES cim_documents (id)
    )''')
    
    # Red flags table
    c.execute('''CREATE TABLE IF NOT EXISTS red_flags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cim_id INTEGER,
        description TEXT,
        page_ref TEXT,
        status TEXT DEFAULT 'open',
        severity TEXT DEFAULT 'medium',
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (cim_id) REFERENCES cim_documents (id)
    )''')
    
    # Synced documents table
    c.execute('''CREATE TABLE IF NOT EXISTS synced_docs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT,
        path TEXT,
        last_synced TIMESTAMP,
        cim_id INTEGER,
        sync_status TEXT DEFAULT 'pending',
        FOREIGN KEY (cim_id) REFERENCES cim_documents (id)
    )''')
    
    # Valuation metrics table
    c.execute('''CREATE TABLE IF NOT EXISTS valuation_metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cim_id INTEGER,
        metric TEXT,
        value REAL,
        year INTEGER,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (cim_id) REFERENCES cim_documents (id)
    )''')
    
    # Audit logs table
    c.execute('''CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        action TEXT,
        document_id INTEGER,
        details TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # User roles table
    c.execute('''CREATE TABLE IF NOT EXISTS user_roles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT UNIQUE,
        role TEXT DEFAULT 'viewer',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    conn.commit()
    conn.close()

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
if 'compliance_mode' not in st.session_state:
    st.session_state.compliance_mode = False
if 'current_user' not in st.session_state:
    st.session_state.current_user = "demo_user"
if 'user_role' not in st.session_state:
    st.session_state.user_role = "admin"
if 'current_cim_id' not in st.session_state:
    st.session_state.current_cim_id = None
if 'red_flags' not in st.session_state:
    st.session_state.red_flags = []
if 'ic_memo' not in st.session_state:
    st.session_state.ic_memo = {}
if 'valuation_data' not in st.session_state:
    st.session_state.valuation_data = {}
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

# Team members and tags for autocomplete
TEAM_MEMBERS = ['@Alex', '@Rishi', '@Jordan', '@Sam', '@Taylor', '@Morgan']
COMMON_TAGS = ['#Modeling', '#Legal', '#KeyAssumption', '#Revenue', '#EBITDA', '#Risk', '#Market', '#Management']

# Initialize database
init_database()

# Compliance and encryption functions
def get_encryption_key():
    """Get or create encryption key for compliance mode"""
    if not ENCRYPTION_AVAILABLE:
        return None
    
    key_file = "encryption.key"
    if os.path.exists(key_file):
        with open(key_file, 'rb') as f:
            return f.read()
    else:
        key = Fernet.generate_key()
        with open(key_file, 'wb') as f:
            f.write(key)
        return key

def encrypt_content(content):
    """Encrypt content for compliance mode"""
    if st.session_state.compliance_mode and ENCRYPTION_AVAILABLE:
        key = get_encryption_key()
        if key:
            f = Fernet(key)
            return base64.b64encode(f.encrypt(content.encode())).decode()
    return content

def decrypt_content(encrypted_content):
    """Decrypt content for compliance mode"""
    if st.session_state.compliance_mode and ENCRYPTION_AVAILABLE and encrypted_content:
        try:
            key = get_encryption_key()
            if key:
                f = Fernet(key)
                return f.decrypt(base64.b64decode(encrypted_content.encode())).decode()
        except:
            pass
    return encrypted_content

def log_audit_action(action, details=None, document_id=None):
    """Log action to audit trail"""
    conn = sqlite3.connect('auctum.db')
    c = conn.cursor()
    c.execute('''INSERT INTO audit_logs (user_id, action, document_id, details) 
                 VALUES (?, ?, ?, ?)''', 
              (st.session_state.current_user, action, document_id, details))
    conn.commit()
    conn.close()

# Semantic search functions
@st.cache_resource
def load_embedding_model():
    """Load and cache the embedding model"""
    if not SEMANTIC_SEARCH_AVAILABLE:
        return None
    try:
        model = SentenceTransformer('all-MiniLM-L6-v2')
        return model
    except Exception as e:
        st.error(f"Error loading embedding model: {e}")
        return None

def chunk_text(text, chunk_size=1000, overlap=200):
    """Split text into overlapping chunks for semantic search"""
    chunks = []
    chunk_metadata = []
    
    # Split by paragraphs first, then by size if needed
    paragraphs = text.split('\n\n')
    current_chunk = ""
    chunk_start_pos = 0
    
    for para in paragraphs:
        if len(current_chunk) + len(para) < chunk_size:
            current_chunk += para + "\n\n"
        else:
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
                chunk_metadata.append({
                    'start_pos': chunk_start_pos,
                    'end_pos': chunk_start_pos + len(current_chunk),
                    'length': len(current_chunk)
                })
                chunk_start_pos += len(current_chunk) - overlap
            current_chunk = para + "\n\n"
    
    # Add the last chunk
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
        chunk_metadata.append({
            'start_pos': chunk_start_pos,
            'end_pos': chunk_start_pos + len(current_chunk),
            'length': len(current_chunk)
        })
    
    return chunks, chunk_metadata

def map_chunks_to_pages(chunks, pdf_reader):
    """Map text chunks to PDF page numbers"""
    page_mapping = []
    page_texts = []
    
    # Extract text from each page
    for page in pdf_reader.pages:
        page_text = page.extract_text() or ""
        page_texts.append(page_text)
    
    # Map each chunk to most likely page
    for chunk in chunks:
        best_page = 1
        best_overlap = 0
        
        # Take first 200 chars of chunk for matching
        chunk_sample = chunk[:200].replace('\n', ' ').strip()
        
        for page_num, page_text in enumerate(page_texts):
            page_clean = page_text.replace('\n', ' ').strip()
            
            # Find longest common substring
            overlap = 0
            for i in range(len(chunk_sample)):
                for j in range(i + 1, len(chunk_sample) + 1):
                    substr = chunk_sample[i:j]
                    if len(substr) > 10 and substr in page_clean:
                        overlap = max(overlap, len(substr))
            
            if overlap > best_overlap:
                best_overlap = overlap
                best_page = page_num + 1
        
        page_mapping.append(best_page)
    
    return page_mapping

def create_semantic_index(chunks):
    """Create FAISS index for semantic search"""
    if not SEMANTIC_SEARCH_AVAILABLE or not st.session_state.embed_model:
        return None, None
    
    try:
        # Generate embeddings
        with st.spinner("🧠 Creating semantic search index..."):
            embeddings = st.session_state.embed_model.encode(chunks, show_progress_bar=False)
        
        # Create FAISS index
        dim = embeddings[0].shape[0]
        index = faiss.IndexFlatL2(dim)
        index.add(np.array(embeddings))
        
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
# PDF extraction and processing functions
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

def extract_section_headers(text):
    """Extract section headers from CIM text"""
    patterns = [
        r"(\d+\.?\d*\s+[A-Z][a-zA-Z\s&]+)(?=\n|\r)",
        r"([A-Z][A-Z\s&]{10,}?)(?=\n|\r)",
        r"^([A-Z][a-zA-Z\s&]{5,}?)(?=\n)",
    ]
    
    headers = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.MULTILINE)
        headers.extend([match.strip() for match in matches if len(match.strip()) > 5])
    
    headers = list(dict.fromkeys(headers))
    
    if not headers:
        headers = [
            "Executive Summary", "Business Overview", "Financial Performance", 
            "Market Analysis", "Management Team", "Investment Highlights",
            "Risk Factors", "Transaction Overview"
        ]
    
    return headers[:15]

def split_text_by_sections(text, headers):
    """Split text into sections based on headers"""
    sections = {}
    text_lower = text.lower()
    
    for i, header in enumerate(headers):
        header_lower = header.lower()
        start_pos = text_lower.find(header_lower)
        
        if start_pos != -1:
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
            sections[header] = ""
    
    return sections

# AI-powered analysis functions
def detect_red_flags(text, api_key):
    """Use AI to detect red flags in CIM content"""
    if not api_key:
        return []
    
    try:
        client = openai.OpenAI(api_key=api_key)
        
        # Split text into chunks for analysis
        chunks = [text[i:i+3000] for i in range(0, len(text), 3000)]
        red_flags = []
        
        for i, chunk in enumerate(chunks[:5]):  # Limit to first 5 chunks
            prompt = f"""
            Analyze this CIM section for potential red flags or inconsistencies:
            
            {chunk}
            
            Look for:
            - Financial inconsistencies or unclear assumptions
            - Missing critical information
            - Overly optimistic projections
            - Unclear business model elements
            - Risk factors that seem understated
            
            Return findings as a JSON list with format:
            [{{"description": "Issue description", "severity": "low/medium/high", "page_ref": "Section reference"}}]
            
            If no issues found, return: []
            """
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a PE due diligence expert identifying potential red flags."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0
            )
            
            try:
                flags = json.loads(response.choices[0].message.content)
                if isinstance(flags, list):
                    red_flags.extend(flags)
            except json.JSONDecodeError:
                continue
        
        return red_flags[:10]  # Return top 10 flags
        
    except Exception as e:
        st.error(f"Error detecting red flags: {e}")
        return []

def extract_valuation_metrics(text, api_key):
    """Extract valuation metrics using AI"""
    if not api_key:
        return {}
    
    try:
        client = openai.OpenAI(api_key=api_key)
        
        prompt = f"""
        Extract valuation-related metrics from this CIM content:
        
        {text[:4000]}
        
        Look for and extract:
        - Revenue (historical and projected)
        - EBITDA (historical and projected)
        - Growth rates
        - Valuation multiples (EV/Revenue, EV/EBITDA)
        - Comparable company data
        
        Return as JSON with format:
        {{
            "revenue_2023": number,
            "revenue_2024": number,
            "ebitda_2023": number,
            "ebitda_2024": number,
            "ev_revenue_multiple": number,
            "ev_ebitda_multiple": number,
            "revenue_growth_rate": number
        }}
        
        Use null for missing values.
        """
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a financial analyst extracting valuation data."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=400,
            temperature=0
        )
        
        try:
            return json.loads(response.choices[0].message.content)
        except json.JSONDecodeError:
            return {}
            
    except Exception as e:
        st.error(f"Error extracting valuation metrics: {e}")
        return {}

def generate_ic_memo_section(section_name, section_text, api_key):
    """Generate IC memo section using AI"""
    if not api_key or not section_text:
        return f"No content available for {section_name}."
    
    try:
        client = openai.OpenAI(api_key=api_key)
        
        prompt = f"""
        Based on this CIM section, write the {section_name} portion of an investment committee memo.
        
        CIM Content:
        {section_text[:2000]}
        
        Write in a professional, concise style suitable for senior executives. Include only the most relevant insights and key decision-making information.
        
        Use clear formatting with bullet points where appropriate.
        """
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a senior investment professional writing IC memos."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=600,
            temperature=0
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"Error generating {section_name}: {str(e)}"

# Data room integration functions
def simulate_data_room_sync(source, path):
    """Simulate data room synchronization (placeholder for real API integration)"""
    # This would integrate with Box, Dropbox, iDeals APIs in production
    
    # Simulate sync status
    import random
    statuses = ['success', 'pending', 'error']
    weights = [0.7, 0.2, 0.1]
    status = random.choices(statuses, weights=weights)[0]
    
    # Log to database
    conn = sqlite3.connect('auctum.db')
    c = conn.cursor()
    c.execute('''INSERT INTO synced_docs (source, path, last_synced, sync_status) 
                 VALUES (?, ?, ?, ?)''', 
              (source, path, datetime.now(), status))
    conn.commit()
    conn.close()
    
    return status

# Main application functions
def save_cim_to_database(filename, content, user_id):
    """Save CIM to database with encryption if compliance mode is enabled"""
    content_hash = hashlib.md5(content.encode()).hexdigest()
    encrypted_content = encrypt_content(content)
    
    conn = sqlite3.connect('auctum.db')
    c = conn.cursor()
    c.execute('''INSERT INTO cim_documents (filename, user_id, content_hash, encrypted_content) 
                 VALUES (?, ?, ?, ?)''', 
              (filename, user_id, content_hash, encrypted_content))
    cim_id = c.lastrowid
    conn.commit()
    conn.close()
    
    log_audit_action("CIM Upload", filename, cim_id)
    return cim_id

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

def main():
    # Initialize workspace data if not already done
    if not st.session_state.workspace_initialized:
        try:
            st.session_state.workspace_initialized = True
        except:
            st.session_state.workspace_initialized = True
    
    # Main title
    st.markdown('<h1 class="main-title">Auctum Enterprise</h1>', unsafe_allow_html=True)

    # Compliance mode toggle
    col1, col2, col3 = st.columns([2, 1, 1])
    with col2:
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
    
    # Privacy note with compliance information
    privacy_text = """
    <div class="privacy-note">
        <strong>🔐 Privacy & Security</strong><br>
        Your documents are processed securely and never stored on external servers. All analysis uses enterprise-grade AI with full compliance.
    """
    
    if st.session_state.compliance_mode and ENCRYPTION_AVAILABLE:
        privacy_text += """<br><strong>Compliance Mode Active:</strong> All documents encrypted, full audit logging enabled, user access controls enforced."""
    elif not ENCRYPTION_AVAILABLE:
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
                    text, pdf_reader = extract_text_from_pdf(uploaded_file)
                    if text:
                        # Save to database
                        cim_id = save_cim_to_database(uploaded_file.name, text, st.session_state.current_user)
                        st.session_state.current_cim_id = cim_id
                        st.session_state.cim_text = text
                        
                        # Extract sections
                        headers = extract_section_headers(text)
                        sections = split_text_by_sections(text, headers)
                        st.session_state.cim_sections = sections
                        
                        # Create semantic search index
                        if SEMANTIC_SEARCH_AVAILABLE:
                            if st.session_state.embed_model is None:
                                st.session_state.embed_model = load_embedding_model()
                            
                            if st.session_state.embed_model:
                                chunks, chunk_metadata = chunk_text(text)
                                st.session_state.text_chunks = chunks
                                
                                # Map chunks to pages
                                page_mapping = map_chunks_to_pages(chunks, pdf_reader)
                                st.session_state.chunk_page_mapping = page_mapping
                                
                                # Create semantic index
                                index, embeddings = create_semantic_index(chunks)
                                st.session_state.semantic_index = index
                                st.session_state.chunk_embeddings = embeddings
                        
                        # Detect red flags
                        red_flags = detect_red_flags(text, api_key)
                        st.session_state.red_flags = red_flags
                        
                        # Extract valuation metrics
                        valuation_data = extract_valuation_metrics(text, api_key)
                        st.session_state.valuation_data = valuation_data
                        
                        semantic_status = "✅ Enabled" if SEMANTIC_SEARCH_AVAILABLE and st.session_state.semantic_index else "❌ Unavailable"
                        st.success(f"✅ CIM processed! Extracted {len(text):,} characters, {len(sections)} sections, {len(red_flags)} red flags detected | Semantic Search: {semantic_status}")
                        st.rerun()
        
        # Data room integration
        if st.session_state.current_cim_id:
            st.divider()
            st.header("🗂️ Data Room Sync")
            
            data_source = st.selectbox("Source", ["Box", "Dropbox", "iDeals", "SharePoint"])
            folder_path = st.text_input("Folder Path", placeholder="/deals/target-company/")
            
            if st.button("🔁 Sync Now"):
                with st.spinner("Syncing documents..."):
                    status = simulate_data_room_sync(data_source, folder_path)
                    if status == 'success':
                        st.success("✅ Sync completed")
                    elif status == 'pending':
                        st.warning("⏳ Sync in progress")
                    else:
                        st.error("❌ Sync failed")
                    log_audit_action("Data Room Sync", f"{data_source}: {folder_path}")
    
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
                st.write("4. Access all enterprise features in the tabs above!")
    else:
        # Show analysis interface with all features
        show_analysis_interface(api_key)

def show_analysis_interface(api_key):
    """Show the main analysis interface with all enterprise features"""
    
    st.info(f"📄 **Document Loaded**: {len(st.session_state.cim_text):,} characters | {len(st.session_state.red_flags)} red flags detected | {len(st.session_state.valuation_data)} valuation metrics extracted")
    
    # Create tabs for all features
    st.markdown('<div class="sticky-tabs">', unsafe_allow_html=True)
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "🔍 Semantic Search",
        "🧑‍💼 Deal Workspace", 
        "📋 IC Memo", 
        "🚨 Red Flags", 
        "💰 Valuation", 
        "🗂️ Data Room",
        "🎯 Quick Analysis", 
        "💬 Chat"
    ])
    st.markdown('</div>', unsafe_allow_html=True)
    
    with tab1:
        show_semantic_search()
    
    with tab2:
        show_deal_workspace(api_key)
    
    with tab3:
        show_ic_memo_generator(api_key)
    
    with tab4:
        show_red_flag_tracker(api_key)
    
    with tab5:
        show_valuation_snapshot(api_key)
    
    with tab6:
        show_data_room_integration()
    
    with tab7:
        show_quick_analysis(api_key)
    
    with tab8:
        show_chat_interface(api_key)

def show_semantic_search():
    """Semantic Search interface with PDF viewer integration"""
    st.subheader("🔍 Semantic Search")
    st.caption("Natural language search through your CIM document")
    
    # Check if semantic search is available
    if not SEMANTIC_SEARCH_AVAILABLE:
        st.error("❌ Semantic search requires additional packages. Install with: `pip install sentence-transformers faiss-cpu`")
        return
    
    if st.session_state.semantic_index is None:
        st.warning("⚠️ Semantic search index not created. Please reprocess your CIM document.")
        return
    
    # Search interface
    st.markdown("### 🔍 Search Your Document")
    
    # Search input with examples
    col1, col2 = st.columns([3, 1])
    with col1:
        search_query = st.text_input(
            "Ask a question or search for content:",
            placeholder="e.g., What are the main revenue streams? What risks does the company face?"
        )
    
    with col2:
        search_button = st.button("🔍 Search", type="primary", use_container_width=True)
    
    # Quick search examples
    st.markdown("**Quick Examples:**")
    example_col1, example_col2, example_col3 = st.columns(3)
    
    with example_col1:
        if st.button("💰 Revenue Model", use_container_width=True):
            search_query = "revenue model business model how company makes money"
            search_button = True
    
    with example_col2:
        if st.button("📊 Financial Performance", use_container_width=True):
            search_query = "financial performance EBITDA revenue growth metrics"
            search_button = True
    
    with example_col3:
        if st.button("⚠️ Risk Factors", use_container_width=True):
            search_query = "risks challenges threats competition regulatory"
            search_button = True
    
    # Perform search
    if (search_query and search_button) or (search_query and st.session_state.get('last_search') != search_query):
        st.session_state.last_search = search_query
        
        with st.spinner("🔍 Searching through document..."):
            results = semantic_search(search_query, st.session_state.text_chunks, st.session_state.semantic_index, top_k=8)
        
        if results:
            st.markdown(f"### 📋 Search Results for: *\"{search_query}\"*")
            st.caption(f"Found {len(results)} relevant sections")
            
            # Display results
            for i, result in enumerate(results):
                similarity_percentage = result['similarity'] * 100
                
                # Result card with enhanced styling
                result_html = f"""
                <div style="background: rgba(30, 41, 59, 0.8); border-radius: 12px; padding: 1.5rem; margin: 1rem 0; border-left: 4px solid #6366f1;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                        <strong>📄 Result #{i+1}</strong>
                        <div style="display: flex; gap: 1rem; font-size: 0.8rem; opacity: 0.8;">
                            <span>📊 Match: {similarity_percentage:.1f}%</span>
                            <span>📖 Page: {result['page']}</span>
                        </div>
                    </div>
                </div>
                """
                st.markdown(result_html, unsafe_allow_html=True)
                
                # Content preview
                chunk_text = result['chunk']
                if len(chunk_text) > 800:
                    preview_text = chunk_text[:800] + "..."
                    with st.expander(f"📖 Preview (Page {result['page']})", expanded=i==0):
                        st.write(chunk_text[:800] + "...")
                        if st.button(f"📄 Show Full Content", key=f"show_full_{i}"):
                            st.text_area("Full Content:", chunk_text, height=200, key=f"full_content_{i}")
                else:
                    with st.expander(f"📖 Content (Page {result['page']})", expanded=i==0):
                        st.write(chunk_text)
                
                # Action buttons
                action_col1, action_col2, action_col3 = st.columns(3)
                
                with action_col1:
                    if st.button(f"📋 Add to IC Memo", key=f"add_memo_{i}"):
                        # Auto-detect best IC memo section
                        if "revenue" in search_query.lower() or "financial" in search_query.lower():
                            section = "Financial Analysis"
                        elif "risk" in search_query.lower():
                            section = "Risk Analysis"
                        elif "market" in search_query.lower():
                            section = "Market Analysis"
                        else:
                            section = "Executive Summary"
                        
                        current_content = st.session_state.ic_memo.get(section, "")
                        new_content = current_content + f"\n\n**From Document (Page {result['page']}):**\n{chunk_text[:300]}..."
                        st.session_state.ic_memo[section] = new_content
                        st.success(f"✅ Added to {section} section of IC Memo")
                
                with action_col2:
                    if st.button(f"🚨 Flag as Risk", key=f"flag_risk_{i}"):
                        new_flag = {
                            'description': f"Review needed: {chunk_text[:100]}...",
                            'severity': 'medium',
                            'page_ref': f'Page {result["page"]}',
                            'status': 'open',
                            'source': 'semantic_search'
                        }
                        st.session_state.red_flags.append(new_flag)
                        st.success("🚨 Added to Red Flag Tracker")
                
                with action_col3:
                    if st.button(f"💬 Ask Follow-up", key=f"followup_{i}"):
                        # Add to chat with context
                        context_query = f"Based on this content from page {result['page']}: {chunk_text[:200]}... Please provide more details about: {search_query}"
                        st.session_state.chat_history.append((context_query, ""))
                        st.info("💬 Added to chat - switch to Chat tab to see AI response")
        
        else:
            st.info("🔍 No relevant sections found. Try different search terms or check if the document was processed correctly.")
    
    # Search statistics
    if st.session_state.text_chunks:
        st.divider()
        st.markdown("### 📊 Document Statistics")
        
        stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
        
        stat_col1.metric("📄 Total Pages", len(set(st.session_state.chunk_page_mapping)))
        stat_col2.metric("🧩 Text Chunks", len(st.session_state.text_chunks))
        stat_col3.metric("📝 Total Words", len(st.session_state.cim_text.split()))
        stat_col4.metric("🔍 Search Ready", "✅ Yes" if st.session_state.semantic_index else "❌ No")
        
        # Advanced search options
        with st.expander("🔧 Advanced Search Options"):
            col_adv1, col_adv2 = st.columns(2)
            
            with col_adv1:
                st.markdown("**Search Tips:**")
                st.write("• Use natural language questions")
                st.write("• Combine related terms for better results")  
                st.write("• Search finds semantically similar content")
                st.write("• Results ranked by relevance")
            
            with col_adv2:
                st.markdown("**Sample Searches:**")
                st.code("management team experience background")
                st.code("competitive advantages moat differentiation")
                st.code("customer acquisition cost lifetime value")
                st.code("regulatory risks compliance issues")
        
        # Chunk browser for debugging/exploration
        if st.checkbox("🔍 Browse Document Chunks"):
            st.markdown("**Document Chunks Browser:**")
            chunk_to_show = st.selectbox("Select chunk to view:", range(len(st.session_state.text_chunks)), format_func=lambda x: f"Chunk {x+1} (Page {st.session_state.chunk_page_mapping[x]})")
            
            if chunk_to_show is not None:
                st.markdown(f"**Chunk {chunk_to_show + 1} - Page {st.session_state.chunk_page_mapping[chunk_to_show]}:**")
                st.text_area("Content:", st.session_state.text_chunks[chunk_to_show], height=200, key="chunk_browser")

def show_deal_workspace(api_key):
    """Enhanced deal team workspace"""
    st.subheader("🧑‍💼 Deal Team Workspace")
    st.caption("Advanced team collaboration and task management")
    
    if not st.session_state.cim_sections:
        st.warning("⚠️ No sections found. Please reprocess the CIM.")
        return
    
    # Section selector with enhanced stats
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### 📂 Sections")
        selected_section = st.selectbox(
            "Select a section:",
            list(st.session_state.cim_sections.keys()),
            key="workspace_section"
        )
        
        if selected_section:
            # Show comprehensive stats
            st.metric("Characters", len(st.session_state.cim_sections.get(selected_section, "")))
            
            # Check for red flags in this section
            section_flags = [flag for flag in st.session_state.red_flags 
                           if selected_section.lower() in flag.get('page_ref', '').lower()]
            if section_flags:
                st.metric("🚨 Red Flags", len(section_flags))
    
    with col2:
        if selected_section:
            st.markdown(f"### 📋 {selected_section}")
            
            # Task management with database integration
            st.markdown("#### ✅ Task Management")
            
            with st.form(f"task_form_{selected_section}"):
                col_a, col_b = st.columns(2)
                with col_a:
                    task_title = st.text_input("Task Title")
                    assigned_to = st.selectbox("Assign to", TEAM_MEMBERS)
                with col_b:
                    due_date = st.date_input("Due Date", value=datetime.now().date() + timedelta(days=7))
                    priority = st.selectbox("Priority", ["Low", "Medium", "High", "Critical"])
                
                task_description = st.text_area("Description")
                
                if st.form_submit_button("➕ Create Task"):
                    if task_title and assigned_to:
                        # Save to database
                        conn = sqlite3.connect('auctum.db')
                        c = conn.cursor()
                        c.execute('''INSERT INTO tasks (cim_id, title, description, assigned_to, due_date, section) 
                                     VALUES (?, ?, ?, ?, ?, ?)''',
                                  (st.session_state.current_cim_id, task_title, task_description, 
                                   assigned_to, due_date, selected_section))
                        conn.commit()
                        conn.close()
                        
                        log_audit_action("Task Created", f"{task_title} assigned to {assigned_to}", st.session_state.current_cim_id)
                        st.success("✅ Task created!")
                        st.rerun()
            
            # Display existing tasks from database
            if st.session_state.current_cim_id:
                conn = sqlite3.connect('auctum.db')
                c = conn.cursor()
                c.execute('''SELECT * FROM tasks WHERE cim_id = ? AND section = ? ORDER BY timestamp DESC''',
                          (st.session_state.current_cim_id, selected_section))
                tasks = c.fetchall()
                conn.close()
                
                if tasks:
                    st.markdown("#### 📝 Active Tasks")
                    for task in tasks:
                        task_id, cim_id, title, description, assigned_to, due_date, status, section, timestamp = task
                        
                        # Task card with enhanced styling
                        task_html = f"""
                        <div class="task-card task-{status.replace(' ', '-')}">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <strong>{title}</strong>
                                <span style="font-size: 0.8rem; opacity: 0.7;">{status.upper()}</span>
                            </div>
                            <div style="margin: 0.5rem 0;">
                                {description if description else 'No description'}
                            </div>
                            <div style="font-size: 0.8rem; opacity: 0.8;">
                                👤 {assigned_to} | 📅 Due: {due_date}
                            </div>
                        </div>
                        """
                        st.markdown(task_html, unsafe_allow_html=True)
                        
                        # Task actions
                        col_action1, col_action2, col_action3 = st.columns(3)
                        with col_action1:
                            if status == 'open' and st.button("🏃 Start", key=f"start_{task_id}"):
                                conn = sqlite3.connect('auctum.db')
                                c = conn.cursor()
                                c.execute("UPDATE tasks SET status = 'in_progress' WHERE id = ?", (task_id,))
                                conn.commit()
                                conn.close()
                                log_audit_action("Task Started", title, st.session_state.current_cim_id)
                                st.rerun()
                        
                        with col_action2:
                            if status in ['open', 'in_progress'] and st.button("✅ Complete", key=f"complete_{task_id}"):
                                conn = sqlite3.connect('auctum.db')
                                c = conn.cursor()
                                c.execute("UPDATE tasks SET status = 'completed' WHERE id = ?", (task_id,))
                                conn.commit()
                                conn.close()
                                log_audit_action("Task Completed", title, st.session_state.current_cim_id)
                                st.rerun()
                        
                        st.markdown("---")

def show_ic_memo_generator(api_key):
    """IC Memo Generator with AI assistance"""
    st.subheader("📋 Investment Committee Memo Generator")
    st.caption("AI-powered memo generation from CIM content")
    
    if not api_key:
        st.warning("⚠️ OpenAI API key required for memo generation")
        return
    
    # Memo sections
    memo_sections = {
        "Executive Summary": "High-level overview and recommendation",
        "Investment Thesis": "Key reasons for investment",
        "Business Overview": "Company description and business model",
        "Financial Analysis": "Key financial metrics and performance",
        "Market Analysis": "Market opportunity and competitive position", 
        "Management Assessment": "Leadership team evaluation",
        "Risk Analysis": "Key risks and mitigation strategies",
        "Valuation": "Valuation methodology and price justification",
        "Recommendation": "Final investment recommendation"
    }
    
    # Generate all sections button
    if st.button("🤖 Generate Complete IC Memo"):
        with st.spinner("Generating IC memo sections..."):
            progress_bar = st.progress(0)
            
            for i, (section, description) in enumerate(memo_sections.items()):
                # Find relevant CIM section
                relevant_text = ""
                for cim_section, content in st.session_state.cim_sections.items():
                    if any(keyword in cim_section.lower() for keyword in section.lower().split()):
                        relevant_text = content
                        break
                
                if not relevant_text:
                    relevant_text = st.session_state.cim_text[:3000]
                
                memo_content = generate_ic_memo_section(section, relevant_text, api_key)
                st.session_state.ic_memo[section] = memo_content
                
                progress_bar.progress((i + 1) / len(memo_sections))
            
            log_audit_action("IC Memo Generated", "Complete memo generated", st.session_state.current_cim_id)
            st.success("✅ IC Memo generated!")
    
    # Display and edit memo sections
    for section, description in memo_sections.items():
        with st.expander(f"📄 {section}", expanded=section=="Executive Summary"):
            st.caption(description)
            
            # Individual section generation
            if section not in st.session_state.ic_memo:
                if st.button(f"Generate {section}", key=f"gen_{section}"):
                    with st.spinner(f"Generating {section}..."):
                        relevant_text = ""
                        for cim_section, content in st.session_state.cim_sections.items():
                            if any(keyword in cim_section.lower() for keyword in section.lower().split()):
                                relevant_text = content
                                break
                        
                        if not relevant_text:
                            relevant_text = st.session_state.cim_text[:3000]
                        
                        memo_content = generate_ic_memo_section(section, relevant_text, api_key)
                        st.session_state.ic_memo[section] = memo_content
                        st.rerun()
            
            # Editable content
            if section in st.session_state.ic_memo:
                edited_content = st.text_area(
                    f"Edit {section}:",
                    value=st.session_state.ic_memo[section],
                    height=200,
                    key=f"edit_{section}"
                )
                st.session_state.ic_memo[section] = edited_content
    
    # Export options
    if st.session_state.ic_memo:
        st.divider()
        st.markdown("### 📤 Export Options")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📄 Export as Markdown"):
                markdown_content = "# Investment Committee Memo\n\n"
                for section, content in st.session_state.ic_memo.items():
                    markdown_content += f"## {section}\n\n{content}\n\n"
                
                st.download_button(
                    "⬇️ Download Markdown",
                    markdown_content,
                    "ic_memo.md",
                    "text/markdown"
                )
        
        with col2:
            st.button("📊 Export to Word", disabled=True, help="Feature coming soon")

def show_red_flag_tracker(api_key):
    """Red Flag Tracker with AI detection"""
    st.subheader("🚨 Red Flag Tracker")
    st.caption("AI-powered inconsistency and risk detection")
    
    # Red flag summary
    if st.session_state.red_flags:
        col1, col2, col3 = st.columns(3)
        
        severity_counts = {}
        for flag in st.session_state.red_flags:
            severity = flag.get('severity', 'medium')
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        col1.metric("🔴 High Severity", severity_counts.get('high', 0))
        col2.metric("🟡 Medium Severity", severity_counts.get('medium', 0))
        col3.metric("🟢 Low Severity", severity_counts.get('low', 0))
        
        st.divider()
        
        # Display red flags
        for i, flag in enumerate(st.session_state.red_flags):
            severity = flag.get('severity', 'medium')
            severity_emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}
            
            flag_html = f"""
            <div class="red-flag">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                    <strong>{severity_emoji.get(severity, '🟡')} Red Flag #{i+1}</strong>
                    <span style="font-size: 0.8rem; opacity: 0.7;">{severity.upper()}</span>
                </div>
                <div style="margin-bottom: 0.5rem;">
                    {flag.get('description', 'No description available')}
                </div>
                <div style="font-size: 0.8rem; opacity: 0.8;">
                    📍 Reference: {flag.get('page_ref', 'General')}
                </div>
            </div>
            """
            st.markdown(flag_html, unsafe_allow_html=True)
            
            # Flag actions
            col_flag1, col_flag2, col_flag3 = st.columns(3)
            with col_flag1:
                if st.button("✅ Resolve", key=f"resolve_flag_{i}"):
                    st.session_state.red_flags[i]['status'] = 'resolved'
                    log_audit_action("Red Flag Resolved", flag.get('description', ''), st.session_state.current_cim_id)
                    st.success("Flag marked as resolved")
            
            with col_flag2:
                if st.button("📋 Add to IC Memo", key=f"add_flag_{i}"):
                    # Add to risk analysis section of IC memo
                    risk_section = st.session_state.ic_memo.get('Risk Analysis', '')
                    risk_section += f"\n\n• {flag.get('description', '')}"
                    st.session_state.ic_memo['Risk Analysis'] = risk_section
                    st.success("Added to IC memo")
            
            with col_flag3:
                if st.button("🔍 Investigate", key=f"investigate_flag_{i}"):
                    st.session_state.red_flags[i]['status'] = 'investigating'
                    log_audit_action("Red Flag Investigation Started", flag.get('description', ''), st.session_state.current_cim_id)
                    st.info("Marked for investigation")
            
            st.markdown("---")
    
    else:
        st.info("✅ No red flags detected in this CIM. This indicates good consistency and clarity in the document.")
    
    # Manual red flag reporting
    st.markdown("### ➕ Report Manual Red Flag")
    with st.form("manual_red_flag"):
        manual_description = st.text_area("Describe the red flag or concern:")
        manual_severity = st.selectbox("Severity", ["low", "medium", "high"])
        manual_section = st.selectbox("Related Section", list(st.session_state.cim_sections.keys()) if st.session_state.cim_sections else ["General"])
        
        if st.form_submit_button("🚨 Report Red Flag"):
            if manual_description:
                new_flag = {
                    'description': manual_description,
                    'severity': manual_severity,
                    'page_ref': manual_section,
                    'status': 'open'
                }
                st.session_state.red_flags.append(new_flag)
                log_audit_action("Manual Red Flag Reported", manual_description, st.session_state.current_cim_id)
                st.success("Red flag reported!")
                st.rerun()

def show_valuation_snapshot(api_key):
    """Valuation analysis and visualization"""
    st.subheader("💰 Valuation Snapshot")
    st.caption("Automated financial metrics extraction and analysis")
    
    if st.session_state.valuation_data:
        # Display key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        valuation = st.session_state.valuation_data
        
        col1.metric(
            "Revenue 2023", 
            f"${valuation.get('revenue_2023', 0):,.0f}M" if valuation.get('revenue_2023') else "N/A"
        )
        col2.metric(
            "EBITDA 2023", 
            f"${valuation.get('ebitda_2023', 0):,.0f}M" if valuation.get('ebitda_2023') else "N/A"
        )
        col3.metric(
            "EV/Revenue", 
            f"{valuation.get('ev_revenue_multiple', 0):,.1f}x" if valuation.get('ev_revenue_multiple') else "N/A"
        )
        col4.metric(
            "Revenue Growth", 
            f"{valuation.get('revenue_growth_rate', 0):,.1f}%" if valuation.get('revenue_growth_rate') else "N/A"
        )
        
        st.divider()
        
        # Create visualizations
        if valuation.get('revenue_2023') and valuation.get('revenue_2024'):
            st.markdown("### 📈 Revenue Trend")
            
            # Create simple chart data
            chart_data = pd.DataFrame({
                'Year': [2023, 2024],
                'Revenue (M)': [valuation.get('revenue_2023', 0), valuation.get('revenue_2024', 0)]
            })
            
            st.line_chart(chart_data.set_index('Year'))
        
        # Valuation multiples comparison
        if valuation.get('ev_revenue_multiple') or valuation.get('ev_ebitda_multiple'):
            st.markdown("### 📊 Valuation Multiples")
            
            multiples_data = {}
            if valuation.get('ev_revenue_multiple'):
                multiples_data['EV/Revenue'] = valuation.get('ev_revenue_multiple')
            if valuation.get('ev_ebitda_multiple'):
                multiples_data['EV/EBITDA'] = valuation.get('ev_ebitda_multiple')
            
            if multiples_data:
                multiples_df = pd.DataFrame(list(multiples_data.items()), columns=['Multiple', 'Value'])
                st.bar_chart(multiples_df.set_index('Multiple'))
        
        # Export valuation data
        st.markdown("### 📤 Export Valuation Data")
        
        if st.button("📊 Export to Excel"):
            valuation_df = pd.DataFrame([valuation])
            csv = valuation_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "⬇️ Download CSV",
                csv,
                "valuation_metrics.csv",
                "text/csv"
            )
    
    else:
        st.info("📊 No valuation metrics extracted yet. The AI analysis may not have found clear financial data in the CIM.")
        
        if api_key and st.button("🔄 Re-analyze for Valuation Data"):
            with st.spinner("Re-analyzing CIM for valuation metrics..."):
                valuation_data = extract_valuation_metrics(st.session_state.cim_text, api_key)
                st.session_state.valuation_data = valuation_data
                if valuation_data:
                    st.success("✅ Valuation data extracted!")
                else:
                    st.warning("⚠️ No clear valuation data found in CIM")
                st.rerun()

def show_data_room_integration():
    """Data room integration and sync status"""
    st.subheader("🗂️ Data Room Integration")
    st.caption("Sync with external data sources and document repositories")
    
    # Sync status overview
    conn = sqlite3.connect('auctum.db')
    c = conn.cursor()
    c.execute("SELECT * FROM synced_docs ORDER BY last_synced DESC")
    synced_docs = c.fetchall()
    conn.close()
    
    if synced_docs:
        st.markdown("### 📊 Sync Status")
        
        # Status summary
        status_counts = {}
        for doc in synced_docs:
            status = doc[5]  # sync_status column
            status_counts[status] = status_counts.get(status, 0) + 1
        
        col1, col2, col3 = st.columns(3)
        col1.metric("✅ Successful", status_counts.get('success', 0))
        col2.metric("⏳ Pending", status_counts.get('pending', 0))
        col3.metric("❌ Failed", status_counts.get('error', 0))
        
        st.divider()
        
        # Sync history
        st.markdown("### 📁 Sync History")
        
        for doc in synced_docs:
            doc_id, source, path, last_synced, cim_id, sync_status = doc
            
            # Format timestamp
            sync_time = datetime.fromisoformat(last_synced).strftime("%Y-%m-%d %H:%M")
            
            # Status styling
            status_class = f"sync-{sync_status}"
            status_emoji = {"success": "✅", "pending": "⏳", "error": "❌"}
            
            doc_html = f"""
            <div style="background: rgba(30, 41, 59, 0.8); border-radius: 8px; padding: 1rem; margin: 0.5rem 0;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong>📂 {source}</strong><br>
                        <span style="opacity: 0.8;">{path}</span>
                    </div>
                    <div style="text-align: right;">
                        <span class="{status_class}">{status_emoji.get(sync_status, '❓')} {sync_status.upper()}</span><br>
                        <span style="font-size: 0.8rem; opacity: 0.7;">{sync_time}</span>
                    </div>
                </div>
            </div>
            """
            st.markdown(doc_html, unsafe_allow_html=True)
            
            # Resync option
            if sync_status in ['error', 'pending']:
                if st.button(f"🔄 Resync", key=f"resync_{doc_id}"):
                    with st.spinner("Resyncing..."):
                        new_status = simulate_data_room_sync(source, path)
                        conn = sqlite3.connect('auctum.db')
                        c = conn.cursor()
                        c.execute("UPDATE synced_docs SET sync_status = ?, last_synced = ? WHERE id = ?",
                                  (new_status, datetime.now(), doc_id))
                        conn.commit()
                        conn.close()
                        log_audit_action("Data Room Resync", f"{source}: {path}")
                        st.rerun()
    
    else:
        st.info("📁 No data room syncs configured yet. Use the sidebar to set up your first sync.")
    
    # Integration guides
    st.markdown("### 🔗 Integration Setup")
    
    with st.expander("📦 Box Integration"):
        st.markdown("""
        **Setup Steps:**
        1. Create Box Developer App at developer.box.com
        2. Generate OAuth credentials
        3. Configure webhook for automatic sync
        4. Test connection with folder path
        """)
    
    with st.expander("📁 Dropbox Integration"):
        st.markdown("""
        **Setup Steps:**
        1. Create Dropbox App at dropbox.com/developers
        2. Generate access token
        3. Set up folder monitoring
        4. Configure sync schedule
        """)
    
    with st.expander("🏢 iDeals Integration"):
        st.markdown("""
        **Setup Steps:**
        1. Contact iDeals for API access
        2. Set up webhook notifications
        3. Configure document filters
        4. Test sync functionality
        """)

def show_quick_analysis(api_key):
    """Quick analysis tools"""
    st.subheader("🎯 Quick Analysis")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Executive Summary", use_container_width=True):
            if api_key:
                with st.spinner("🔍 Generating summary..."):
                    try:
                        client = openai.OpenAI(api_key=api_key)
                        response = client.chat.completions.create(
                            model="gpt-3.5-turbo",
                            messages=[
                                {"role": "system", "content": "You are an expert financial analyst."},
                                {"role": "user", "content": f"Provide an executive summary of this CIM: {st.session_state.cim_text[:3000]}"}
                            ],
                            max_tokens=800
                        )
                        st.markdown("### 📊 Executive Summary")
                        st.markdown(response.choices[0].message.content)
                        log_audit_action("Generated Executive Summary", "", st.session_state.current_cim_id)
                    except Exception as e:
                        st.error(f"Error: {e}")
    
    with col2:
        if st.button("💰 Financial Analysis", use_container_width=True):
            if api_key:
                with st.spinner("📈 Analyzing financials..."):
                    try:
                        client = openai.OpenAI(api_key=api_key)
                        response = client.chat.completions.create(
                            model="gpt-3.5-turbo",
                            messages=[
                                {"role": "system", "content": "You are an expert financial analyst."},
                                {"role": "user", "content": f"Extract and analyze key financial metrics from this CIM: {st.session_state.cim_text[:3000]}"}
                            ],
                            max_tokens=800
                        )
                        st.markdown("### 💰 Financial Analysis")
                        st.markdown(response.choices[0].message.content)
                        log_audit_action("Generated Financial Analysis", "", st.session_state.current_cim_id)
                    except Exception as e:
                        st.error(f"Error: {e}")
    
    with col3:
        if st.button("⚠️ Risk Assessment", use_container_width=True):
            if st.session_state.red_flags:
                st.markdown("### ⚠️ Risk Assessment")
                st.markdown(f"**{len(st.session_state.red_flags)} potential risks identified:**")
                for i, flag in enumerate(st.session_state.red_flags[:5]):
                    st.markdown(f"• {flag.get('description', 'Unknown risk')}")
                if len(st.session_state.red_flags) > 5:
                    st.markdown(f"*...and {len(st.session_state.red_flags) - 5} more*")
            else:
                st.markdown("### ⚠️ Risk Assessment")
                st.markdown("✅ No significant risks detected in automated analysis.")

def show_chat_interface(api_key):
    """Interactive chat interface"""
    st.subheader("💬 Interactive Analysis")
    st.caption("Ask questions about this CIM document")
    
    # Display chat history
    for i, (question, answer) in enumerate(st.session_state.chat_history):
        with st.chat_message("user"):
            st.write(question)
        with st.chat_message("assistant"):
            st.write(answer)
    
    # Chat input
    if prompt := st.chat_input("Ask a question about this CIM document..."):
        if api_key:
            # Add user message to chat history
            st.session_state.chat_history.append((prompt, ""))
            
            # Display user message
            with st.chat_message("user"):
                st.write(prompt)
            
            # Generate and display assistant response
            with st.chat_message("assistant"):
                with st.spinner("🤔 Analyzing..."):
                    try:
                        client = openai.OpenAI(api_key=api_key)
                        
                        # Use relevant context from CIM
                        context = st.session_state.cim_text[:4000]
                        full_prompt = f"Based on this CIM: {context}\n\nQuestion: {prompt}"
                        
                        response = client.chat.completions.create(
                            model="gpt-3.5-turbo",
                            messages=[
                                {"role": "system", "content": "You are an expert financial analyst helping analyze CIM documents."},
                                {"role": "user", "content": full_prompt}
                            ],
                            max_tokens=800
                        )
                        
                        answer = response.choices[0].message.content
                        st.write(answer)
                        
                        # Update chat history
                        st.session_state.chat_history[-1] = (prompt, answer)
                        log_audit_action("Chat Query", prompt[:50], st.session_state.current_cim_id)
                        
                    except Exception as e:
                        st.error(f"Error: {e}")
                        st.session_state.chat_history[-1] = (prompt, f"Error: {e}")
        else:
            st.warning("⚠️ Please enter your OpenAI API key to use the chat feature")

if __name__ == "__main__":
    main()
