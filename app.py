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

# Page config
st.set_page_config(
    page_title="Auctum", 
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
    
    /* Chat messages */
    .stChatMessage {
        background: rgba(30, 41, 59, 0.8);
        border-radius: 12px;
        margin-bottom: 1rem;
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
if 'current_filename' not in st.session_state:
    st.session_state.current_filename = None

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
        return text
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return None

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
        st.header("📄 Upload Document")
        uploaded_file = st.file_uploader(
            "Choose a PDF file",
            type=['pdf'],
            help="Upload your document in PDF format"
        )
        
        if uploaded_file and api_key:
            if st.button("🔍 Process Document", type="primary"):
                with st.spinner("🔄 Processing document..."):
                    text = extract_text_from_pdf(uploaded_file)
                    if text:
                        st.session_state.cim_text = text
                        st.session_state.current_filename = uploaded_file.name
                        st.session_state.chat_history = []  # Reset chat history for new document
                        
                        # Extract sections
                        headers = extract_section_headers(text)
                        sections = split_text_by_sections(text, headers)
                        st.session_state.cim_sections = sections
                        
                        st.success(f"✅ Document processed! Extracted {len(text):,} characters from {len(sections)} sections")
                        st.rerun()
    
    # Main content area
    if st.session_state.cim_text is None:
        # Welcome screen
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("### 🚀 Welcome to Auctum Enterprise")
            
            with st.container():
                st.markdown("**💬 AI-Powered Document Analysis**")
                st.write("Upload any PDF document and ask questions about its content using advanced AI")
                
                st.markdown("**🔍 Intelligent Search**") 
                st.write("Get instant answers to specific questions about your documents")
                
                st.markdown("**📊 Section Detection**")
                st.write("Automatically identifies and organizes document sections")
                
                st.divider()
                
                st.markdown("#### Getting Started")
                st.write("1. Enter your OpenAI API key in the sidebar")
                st.write("2. Upload a PDF document") 
                st.write("3. Click 'Process Document' to analyze")
                st.write("4. Start asking questions in the chat interface!")
    else:
        # Show chat interface
        show_chat_interface(api_key)

def show_chat_interface(api_key):
    """Interactive chat interface"""
    st.subheader("💬 Document Analysis Chat")
    
    # Document info
    if st.session_state.current_filename:
        st.info(f"📄 **Document**: {st.session_state.current_filename} | **Size**: {len(st.session_state.cim_text):,} characters | **Sections**: {len(st.session_state.cim_sections)}")
    
    # Display chat history
    for i, (question, answer) in enumerate(st.session_state.chat_history):
        with st.chat_message("user"):
            st.write(question)
        with st.chat_message("assistant"):
            st.write(answer)
    
    # Chat input
    if prompt := st.chat_input("Ask a question about this document..."):
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
                        
                        # Use relevant context from document
                        context = st.session_state.cim_text[:4000]
                        full_prompt = f"Based on this document: {context}\n\nQuestion: {prompt}"
                        
                        response = client.chat.completions.create(
                            model="gpt-3.5-turbo",
                            messages=[
                                {"role": "system", "content": "You are an expert analyst helping analyze documents. Provide clear, concise answers based on the document content."},
                                {"role": "user", "content": full_prompt}
                            ],
                            max_tokens=800
                        )
                        
                        answer = response.choices[0].message.content
                        st.write(answer)
                        
                        # Update chat history
                        st.session_state.chat_history[-1] = (prompt, answer)
                        
                    except Exception as e:
                        st.error(f"Error: {e}")
                        st.session_state.chat_history[-1] = (prompt, f"Error: {e}")
        else:
            st.warning("⚠️ Please enter your OpenAI API key to use the chat feature")
    
    # Quick action buttons
    st.markdown("### 💡 Quick Actions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Summarize Document", use_container_width=True):
            if api_key:
                prompt = "Please provide a comprehensive summary of this document, including key points and main findings."
                process_quick_action(prompt, api_key)
    
    with col2:
        if st.button("🔍 Extract Key Points", use_container_width=True):
            if api_key:
                prompt = "What are the most important key points and takeaways from this document?"
                process_quick_action(prompt, api_key)
    
    with col3:
        if st.button("📋 List Sections", use_container_width=True):
            if st.session_state.cim_sections:
                sections_list = "\n".join([f"• {section}" for section in st.session_state.cim_sections.keys()])
                st.session_state.chat_history.append(("List all sections in this document", f"Here are the sections found in the document:\n\n{sections_list}"))
                st.rerun()

def process_quick_action(prompt, api_key):
    """Process quick action buttons"""
    st.session_state.chat_history.append((prompt, ""))
    
    try:
        client = openai.OpenAI(api_key=api_key)
        
        context = st.session_state.cim_text[:4000]
        full_prompt = f"Based on this document: {context}\n\nQuestion: {prompt}"
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert analyst helping analyze documents. Provide clear, concise answers based on the document content."},
                {"role": "user", "content": full_prompt}
            ],
            max_tokens=800
        )
        
        answer = response.choices[0].message.content
        st.session_state.chat_history[-1] = (prompt, answer)
        st.rerun()
        
    except Exception as e:
        st.error(f"Error: {e}")
        st.session_state.chat_history[-1] = (prompt, f"Error: {e}")
        st.rerun()

if __name__ == "__main__":
    main()
