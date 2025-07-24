from dotenv import load_dotenv
load_dotenv()
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

# Enhanced CSS with particles and modern styling
st.markdown("""
<style>
    /* Hide Streamlit branding and header */
    .stApp > header {
        background-color: transparent;
    }
    
    .stApp > header [data-testid="stHeader"] {
        display: none;
    }
    
    /* Custom styling */
    .main-title {
        font-size: 4rem;
        font-weight: 700;
        text-align: center;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.5rem;
        letter-spacing: -2px;
    }
    
    .subtitle {
        text-align: center;
        font-size: 1.2rem;
        color: #6c757d;
        margin-bottom: 2rem;
    }
    
    /* Particles container */
    #particles-js {
        position: fixed;
        width: 100%;
        height: 100%;
        top: 0;
        left: 0;
        z-index: -1;
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    /* Card styling */
    .welcome-card {
        background: rgba(255, 255, 255, 0.95);
        padding: 2rem;
        border-radius: 20px;
        box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.2);
        margin: 2rem 0;
    }
    
    .feature-item {
        background: rgba(255, 255, 255, 0.8);
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border-left: 4px solid #667eea;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: transform 0.2s;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: rgba(255, 255, 255, 0.95);
    }
    
    /* Privacy note styling */
    .privacy-note {
        background: rgba(40, 167, 69, 0.1);
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
    }
    
    /* Chat interface styling */
    .stChatMessage {
        background: rgba(255, 255, 255, 0.9);
        border-radius: 10px;
        margin: 0.5rem 0;
    }
</style>

<div id="particles-js"></div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/particles.js/2.0.0/particles.min.js"></script>
<script>
particlesJS("particles-js", {
  "particles": {
    "number": {
      "value": 80,
      "density": {
        "enable": true,
        "value_area": 800
      }
    },
    "color": {
      "value": "#667eea"
    },
    "shape": {
      "type": "circle",
      "stroke": {
        "width": 0,
        "color": "#000000"
      }
    },
    "opacity": {
      "value": 0.5,
      "random": false,
      "anim": {
        "enable": false,
        "speed": 1,
        "opacity_min": 0.1,
        "sync": false
      }
    },
    "size": {
      "value": 3,
      "random": true,
      "anim": {
        "enable": false,
        "speed": 40,
        "size_min": 0.1,
        "sync": false
      }
    },
    "line_linked": {
      "enable": true,
      "distance": 150,
      "color": "#667eea",
      "opacity": 0.4,
      "width": 1
    },
    "move": {
      "enable": true,
      "speed": 6,
      "direction": "none",
      "random": false,
      "straight": false,
      "out_mode": "out",
      "bounce": false,
      "attract": {
        "enable": false,
        "rotateX": 600,
        "rotateY": 1200
      }
    }
  },
  "interactivity": {
    "detect_on": "canvas",
    "events": {
      "onhover": {
        "enable": true,
        "mode": "repulse"
      },
      "onclick": {
        "enable": true,
        "mode": "push"
      },
      "resize": true
    },
    "modes": {
      "grab": {
        "distance": 400,
        "line_linked": {
          "opacity": 1
        }
      },
      "bubble": {
        "distance": 400,
        "size": 40,
        "duration": 2,
        "opacity": 8,
        "speed": 3
      },
      "repulse": {
        "distance": 200,
        "duration": 0.4
      },
      "push": {
        "particles_nb": 4
      },
      "remove": {
        "particles_nb": 2
      }
    }
  },
  "retina_detect": true
});
</script>
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
    # Main title
    st.markdown('<h1 class="main-title">Auctum</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">AI-Powered CIM Analysis Platform</p>', unsafe_allow_html=True)

    # Privacy note with better styling
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
        # Welcome screen with better design
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("""
            <div class="welcome-card">
                <h3 style="text-align: center; margin-bottom: 1.5rem;">🚀 Welcome to Auctum</h3>
                
                <div class="feature-item">
                    <strong>📤 Upload Documents</strong><br>
                    Support for PDF CIM documents with intelligent text extraction
                </div>
                
                <div class="feature-item">
                    <strong>🤖 AI-Powered Analysis</strong><br>
                    Get instant insights and comprehensive analysis of investment opportunities
                </div>
                
                <div class="feature-item">
                    <strong>📊 Smart Insights</strong><br>
                    Extract key metrics, financial data, and risk assessments automatically
                </div>
                
                <div class="feature-item">
                    <strong>💬 Interactive Chat</strong><br>
                    Ask specific questions about your CIM documents and get detailed answers
                </div>
                
                <hr style="margin: 2rem 0;">
                
                <h4 style="text-align: center;">Getting Started</h4>
                <ol style="padding-left: 1.5rem;">
                    <li>Enter your OpenAI API key in the sidebar</li>
                    <li>Upload a CIM PDF file</li>
                    <li>Click "Process CIM" to analyze</li>
                    <li>Start asking questions and generating insights!</li>
                </ol>
            </div>
            """, unsafe_allow_html=True)
    else:
        # Show CIM analysis interface
        show_analysis_interface(api_key)

def show_analysis_interface(api_key):
    """Show the main analysis interface after CIM is processed"""
    
    st.info(f"📄 **Document Loaded**: {len(st.session_state.cim_text):,} characters extracted and ready for analysis")
    
    # Quick analysis buttons with better spacing
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
