import sqlite3
import streamlit as st
import hashlib
import base64
from datetime import datetime

# Optional encryption support
try:
    from cryptography.fernet import Fernet
    ENCRYPTION_AVAILABLE = True
except ImportError:
    ENCRYPTION_AVAILABLE = False

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

def get_encryption_key():
    """Get or create encryption key for compliance mode"""
    if not ENCRYPTION_AVAILABLE:
        return None
    
    key_file = "encryption.key"
    try:
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            return key
    except:
        return None

def encrypt_content(content):
    """Encrypt content for compliance mode"""
    if st.session_state.compliance_mode and ENCRYPTION_AVAILABLE:
        key = get_encryption_key()
        if key:
            try:
                f = Fernet(key)
                return base64.b64encode(f.encrypt(content.encode())).decode()
            except:
                pass
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

def get_tasks_for_section(cim_id, section):
    """Get all tasks for a specific section"""
    conn = sqlite3.connect('auctum.db')
    c = conn.cursor()
    c.execute('''SELECT * FROM tasks WHERE cim_id = ? AND section = ? ORDER BY timestamp DESC''',
              (cim_id, section))
    tasks = c.fetchall()
    conn.close()
    return tasks

def create_task(cim_id, title, description, assigned_to, due_date, section):
    """Create a new task"""
    conn = sqlite3.connect('auctum.db')
    c = conn.cursor()
    c.execute('''INSERT INTO tasks (cim_id, title, description, assigned_to, due_date, section) 
                 VALUES (?, ?, ?, ?, ?, ?)''',
              (cim_id, title, description, assigned_to, due_date, section))
    task_id = c.lastrowid
    conn.commit()
    conn.close()
    return task_id

def update_task_status(task_id, new_status):
    """Update task status"""
    conn = sqlite3.connect('auctum.db')
    c = conn.cursor()
    c.execute("UPDATE tasks SET status = ? WHERE id = ?", (new_status, task_id))
    conn.commit()
    conn.close()

def get_synced_docs():
    """Get all synced documents"""
    conn = sqlite3.connect('auctum.db')
    c = conn.cursor()
    c.execute("SELECT * FROM synced_docs ORDER BY last_synced DESC")
    docs = c.fetchall()
    conn.close()
    return docs

def add_synced_doc(source, path, sync_status='pending'):
    """Add a new synced document"""
    conn = sqlite3.connect('auctum.db')
    c = conn.cursor()
    c.execute('''INSERT INTO synced_docs (source, path, last_synced, sync_status) 
                 VALUES (?, ?, ?, ?)''', 
              (source, path, datetime.now(), sync_status))
    doc_id = c.lastrowid
    conn.commit()
    conn.close()
    return doc_id

def update_sync_status(doc_id, new_status):
    """Update sync status"""
    conn = sqlite3.connect('auctum.db')
    c = conn.cursor()
    c.execute("UPDATE synced_docs SET sync_status = ?, last_synced = ? WHERE id = ?",
              (new_status, datetime.now(), doc_id))
    conn.commit()
    conn.close()
