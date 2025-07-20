import streamlit as st
import os
from pathlib import Path
import tempfile
from extract import extract_text_from_cim
from check import CIMAnalyzer
import logging

# Page config
st.set_page_config(
    page_title="Auctum - CIM Analyzer",
    page_icon="📊",
    layout="wide"
)

# Initialize session state
if 'cim_data' not in st.session_state:
    st.session_state.cim_data = None
if 'analyzer' not in st.session_state:
    st.session_state.analyzer = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

def main():
    st.title("🏢 Auctum - CIM Intelligence Platform")
    st.subheader("Upload your Confidential Information Memorandum and get AI-powered insights")
    
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
            os.environ["OPENAI_API_KEY"] = api_key
            st.success("API key configured ✅")
        else:
            st.warning("Please enter your OpenAI API key to continue")
        
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
                process_cim(uploaded_file)
    
    # Main content area
    if st.session_state.cim_data is None:
        # Welcome screen
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("""
            ### 🚀 Welcome to Auctum MVP
            
            **What you can do:**
            - 📤 Upload CIM documents (PDF format)
            - 🤖 Ask questions about the investment opportunity
            - 📊 Get AI-powered insights and analysis
            - 💡 Extract key metrics and highlights
            
            **Get started:**
            1. Enter your OpenAI API key in the sidebar
            2. Upload a CIM PDF file
            3. Click "Process CIM" to analyze
            4. Start asking questions!
            """)
    else:
        # Show CIM analysis interface
        show_analysis_interface()

def process_cim(uploaded_file):
    """Process uploaded CIM file"""
    with st.spinner("🔄 Processing CIM... This may take a moment."):
        try:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name
            
            # Extract text from PDF
            st.info("📖 Extracting text from PDF...")
            cim_data = extract_text_from_cim(tmp_path)
            
            # Initialize analyzer
            st.info("🧠 Initializing AI analyzer...")
            analyzer = CIMAnalyzer(cim_data['chunks'])
            
            # Store in session state
            st.session_state.cim_data = cim_data
            st.session_state.analyzer = analyzer
            
            # Clean up temp file
            os.unlink(tmp_path)
            
            st.success(f"✅ CIM processed successfully!")
            st.info(f"📄 Loaded {cim_data['stats']['pages']} pages, {cim_data['stats']['chunks']} text chunks")
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Error processing CIM: {str(e)}")
            logging.error(f"CIM processing error: {e}")

def show_analysis_interface():
    """Show the main analysis interface after CIM is processed"""
    
    # Summary section
    with st.expander("📋 CIM Summary", expanded=True):
        if st.button("📊 Generate Executive Summary"):
            with st.spinner("Generating summary..."):
                try:
                    summary = st.session_state.analyzer.generate_summary()
                    st.markdown(summary)
                except Exception as e:
                    st.error(f"Error generating summary: {e}")
    
    # Quick insights
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("💰 Key Financial Metrics"):
            with st.spinner("Extracting financial metrics..."):
                try:
                    metrics = st.session_state.analyzer.extract_financial_metrics()
                    st.markdown(metrics)
                except Exception as e:
                    st.error(f"Error extracting metrics: {e}")
    
    with col2:
        if st.button("⚠️ Risk Analysis"):
            with st.spinner("Analyzing risks..."):
                try:
                    risks = st.session_state.analyzer.analyze_risks()
                    st.markdown(risks)
                except Exception as e:
                    st.error(f"Error analyzing risks: {e}")
    
    st.divider()
    
    # Chat interface
    st.header("💬 Ask Questions About This CIM")
    
    # Display chat history
    for i, (question, answer) in enumerate(st.session_state.chat_history):
        with st.chat_message("user"):
            st.write(question)
        with st.chat_message("assistant"):
            st.write(answer)
    
    # Chat input
    if prompt := st.chat_input("Ask a question about this CIM..."):
        # Add user message to chat history
        st.session_state.chat_history.append((prompt, ""))
        
        # Display user message
        with st.chat_message("user"):
            st.write(prompt)
        
        # Generate and display assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = st.session_state.analyzer.answer_question(prompt)
                    st.write(response)
                    
                    # Update chat history with response
                    st.session_state.chat_history[-1] = (prompt, response)
                    
                except Exception as e:
                    error_msg = f"Error generating response: {e}"
                    st.error(error_msg)
                    st.session_state.chat_history[-1] = (prompt, error_msg)

if __name__ == "__main__":
    main()
