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
    
    /* Debug info styling */
    .debug-info {
        background: rgba(59, 130, 246, 0.1);
        border: 1px solid rgba(59, 130, 246, 0.3);
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-size: 0.9rem;
        margin: 0.5rem 0;
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
if 'text_chunks' not in st.session_state:
    st.session_state.text_chunks = []
if 'debug_mode' not in st.session_state:
    st.session_state.debug_mode = False

# PDF extraction and processing functions
def extract_text_from_pdf(pdf_file):
    """Extract text from PDF using PyPDF2"""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page_num, page in enumerate(pdf_reader.pages):
            page_text = page.extract_text()
            if page_text:
                text += f"\n\n--- PAGE {page_num + 1} ---\n\n" + page_text
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

def chunk_text(text, chunk_size=1500, overlap=300):
    """Split text into overlapping chunks for better context retrieval"""
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        
        # Try to break at sentence boundaries
        if end < len(text):
            last_period = chunk.rfind('.')
            if last_period > chunk_size * 0.8:
                end = start + last_period + 1
                chunk = text[start:end]
        
        chunks.append({
            'text': chunk,
            'start': start,
            'end': end,
            'index': len(chunks)
        })
        start = end - overlap
    
    return chunks

def search_for_financial_terms(text):
    """Search specifically for financial terms and amounts"""
    financial_patterns = [
        r'\$[\d,]+\.?\d*\s*(million|billion|thousand)?',
        r'€[\d,]+\.?\d*\s*(million|billion|thousand)?',
        r'[\d,]+\.?\d*\s*(million|billion|thousand)?\s*(USD|EUR|dollars|euros)',
        r'revenue[s]?\s*:?\s*\$?€?[\d,]+',
        r'profit[s]?\s*:?\s*\$?€?[\d,]+',
        r'debt[s]?\s*:?\s*\$?€?[\d,]+',
        r'financial\s+(?:details|information|data|metrics)',
        r'senior\s+secured\s+credit\s+facilities',
    ]
    
    findings = []
    for pattern in financial_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            start = max(0, match.start() - 200)
            end = min(len(text), match.end() + 200)
            context = text[start:end]
            findings.append({
                'match': match.group(),
                'context': context,
                'position': match.start()
            })
    
    return findings

def find_relevant_chunks_advanced(query, chunks, text, top_k=5):
    """Advanced chunk finding with multiple strategies"""
    query_lower = query.lower()
    scored_chunks = []
    
    # Strategy 1: Direct keyword matching
    keywords = set(query_lower.split())
    financial_keywords = {'financial', 'finance', 'revenue', 'profit', 'debt', 'million', 'billion', 
                         'dollar', 'euro', 'usd', 'eur', 'credit', 'facilities', 'senior', 'secured'}
    
    # Add financial keywords if query seems financial
    if any(kw in query_lower for kw in ['financial', 'finance', 'money', 'revenue', 'profit']):
        keywords.update(financial_keywords)
    
    # Strategy 2: Search for specific financial amounts if mentioned
    financial_findings = search_for_financial_terms(text)
    
    for i, chunk in enumerate(chunks):
        chunk_text_lower = chunk['text'].lower()
        score = 0
        
        # Keyword matching score
        for keyword in keywords:
            score += chunk_text_lower.count(keyword) * 2
        
        # Financial pattern matching score
        for finding in financial_findings:
            if finding['position'] >= chunk['start'] and finding['position'] <= chunk['end']:
                score += 10  # High score for chunks containing financial data
        
        # Boost score for chunks containing dollar or euro symbols
        score += chunk['text'].count('$') * 3
        score += chunk['text'].count('€') * 3
        
        scored_chunks.append((score, i, chunk))
    
    # Sort by score
    scored_chunks.sort(key=lambda x: x[0], reverse=True)
    
    # Return top k chunks
    return [chunk for _, _, chunk in scored_chunks[:top_k]]

def get_comprehensive_context(query, full_text, chunks):
    """Get comprehensive context using multiple strategies"""
    query_lower = query.lower()
    
    # First, try to find specific financial mentions
    if any(term in query_lower for term in ['financial', 'finance', 'money', 'revenue', 'debt', 'million']):
        financial_findings = search_for_financial_terms(full_text)
        if financial_findings:
            # Create context from financial findings
            context_parts = []
            for finding in financial_findings[:5]:  # Top 5 financial mentions
                context_parts.append(f"[Financial mention: {finding['match']}]\n{finding['context']}")
            return "\n\n---\n\n".join(context_parts)
    
    # Otherwise, use chunk-based retrieval
    relevant_chunks = find_relevant_chunks_advanced(query, chunks, full_text)
    context_parts = [f"[Chunk {chunk['index']+1}]\n{chunk['text']}" for chunk in relevant_chunks]
    
    return "\n\n---\n\n".join(context_parts)

def main():
    # Main title
    st.markdown('<h1 class="main-title">Auctum</h1>', unsafe_allow_html=True)
    
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
        
        # Debug mode toggle
        st.session_state.debug_mode = st.checkbox("🔍 Debug Mode", value=st.session_state.debug_mode,
                                                  help="Show additional information about document processing")
        
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
                        st.session_state.chat_history = []
                        
                        # Extract sections
                        headers = extract_section_headers(text)
                        sections = split_text_by_sections(text, headers)
                        st.session_state.cim_sections = sections
                        
                        # Create chunks
                        chunks = chunk_text(text)
                        st.session_state.text_chunks = chunks
                        
                        st.success(f"✅ Document processed! Extracted {len(text):,} characters")
                        st.info(f"📊 Created {len(chunks)} searchable chunks")
                        
                        # Debug: Show sample of financial findings
                        if st.session_state.debug_mode:
                            financial_findings = search_for_financial_terms(text)
                            if financial_findings:
                                st.markdown("### 💰 Financial Terms Found:")
                                for i, finding in enumerate(financial_findings[:5]):
                                    st.markdown(f'<div class="debug-info">Match {i+1}: {finding["match"]}</div>', 
                                              unsafe_allow_html=True)
                        
                        st.rerun()
    
    # Main content area
    if st.session_state.cim_text is None:
        # Welcome screen
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("### 🚀 Welcome to Auctum")
            
            with st.container():
                st.markdown("**💬 AI-Powered Document Analysis**")
                st.write("Upload any PDF document and ask questions about its content using advanced AI")
                
                st.markdown("**🔍 Full Document Search**") 
                st.write("Intelligently searches through the entire document to find relevant information")
                
                st.markdown("**📊 Financial Data Extraction**")
                st.write("Automatically detects and extracts financial figures, amounts, and metrics")
                
                st.divider()
                
                st.markdown("#### Getting Started")
                st.write("1. Enter your OpenAI API key in the sidebar")
                st.write("2. Upload a PDF document") 
                st.write("3. Click 'Process Document' to analyze")
                st.write("4. Start asking questions - the AI will search the entire document!")
    else:
        # Show chat interface
        show_chat_interface(api_key)

def show_chat_interface(api_key):
    """Interactive chat interface"""
    st.subheader("💬 Document Analysis Chat")
    
    # Document info
    if st.session_state.current_filename:
        st.info(f"📄 **Document**: {st.session_state.current_filename} | **Size**: {len(st.session_state.cim_text):,} characters | **Sections**: {len(st.session_state.cim_sections)} | **Chunks**: {len(st.session_state.text_chunks)}")
    
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
                with st.spinner("🔄 Searching entire document..."):
                    try:
                        client = openai.OpenAI(api_key=api_key)
                        
                        # Get comprehensive context
                        context = get_comprehensive_context(
                            prompt, 
                            st.session_state.cim_text,
                            st.session_state.text_chunks
                        )
                        
                        # Debug: Show what context we're sending
                        if st.session_state.debug_mode:
                            with st.expander("🔍 Debug: Context being sent to AI"):
                                st.text(context[:1000] + "..." if len(context) > 1000 else context)
                        
                        # System message
                        system_message = """You are an expert document analyst. You have access to excerpts from a document.
                        Your job is to answer questions based on the provided excerpts. Be specific and cite the exact 
                        figures or information you find. If you cannot find the requested information in the provided 
                        excerpts, clearly state that."""
                        
                        # Create the prompt
                        full_prompt = f"""Based on these document excerpts, please answer the user's question.
                        
Document Excerpts:
{context}

User Question: {prompt}

Please provide a specific answer based on the excerpts above. If you find financial figures, cite them exactly."""
                        
                        response = client.chat.completions.create(
                            model="gpt-4-turbo-preview" if "gpt-4" in api_key else "gpt-3.5-turbo-16k",
                            messages=[
                                {"role": "system", "content": system_message},
                                {"role": "user", "content": full_prompt}
                            ],
                            max_tokens=1000,
                            temperature=0.3  # Lower temperature for more focused answers
                        )
                        
                        answer = response.choices[0].message.content
                        st.write(answer)
                        
                        # Update chat history
                        st.session_state.chat_history[-1] = (prompt, answer)
                        
                    except Exception as e:
                        st.error(f"Error: {e}")
                        if st.session_state.debug_mode:
                            st.exception(e)
                        st.session_state.chat_history[-1] = (prompt, f"Error: {e}")
        else:
            st.warning("⚠️ Please enter your OpenAI API key to use the chat feature")
    
    # Quick action buttons
    st.markdown("### 💡 Quick Actions")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📊 Summarize", use_container_width=True):
            if api_key:
                prompt = "Provide a comprehensive summary of this document"
                process_quick_action(prompt, api_key)
    
    with col2:
        if st.button("💰 Find Financials", use_container_width=True):
            if api_key:
                prompt = "Find and list all financial figures, amounts, revenues, debts, or monetary values mentioned in this document"
                process_quick_action(prompt, api_key)
    
    with col3:
        if st.button("🔍 Key Points", use_container_width=True):
            if api_key:
                prompt = "What are the most important key points from this document?"
                process_quick_action(prompt, api_key)
    
    with col4:
        if st.button("📋 List Sections", use_container_width=True):
            if st.session_state.cim_sections:
                sections_list = "\n".join([f"• {section}" for section in st.session_state.cim_sections.keys()])
                st.session_state.chat_history.append(("List all sections", f"Document sections:\n\n{sections_list}"))
                st.rerun()

def process_quick_action(prompt, api_key):
    """Process quick action buttons"""
    st.session_state.chat_history.append((prompt, ""))
    
    try:
        client = openai.OpenAI(api_key=api_key)
        
        # Get comprehensive context
        context = get_comprehensive_context(prompt, st.session_state.cim_text, st.session_state.text_chunks)
        
        system_message = """You are an expert document analyst. Provide detailed, accurate answers based on the document content."""
        
        full_prompt = f"""Document excerpts:
{context}

Request: {prompt}

Please provide a comprehensive answer based on the document excerpts above."""
        
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview" if "gpt-4" in api_key else "gpt-3.5-turbo-16k",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": full_prompt}
            ],
            max_tokens=1500,
            temperature=0.3
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
