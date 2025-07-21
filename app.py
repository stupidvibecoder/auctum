import streamlit as st
import PyPDF2
import openai
import tempfile
import os

# Page config
st.set_page_config(
    page_title="Auctum - CIM Analyzer",
    page_icon="📊",
    layout="wide"
)

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

def get_openai_response(prompt, context, api_key):
    """Get response from OpenAI"""
    try:
        client = openai.OpenAI(api_key=api_key)
        
        full_prompt = f"""Based on the following CIM document content, {prompt}

Document content:
{context[:8000]}  # Limit context to avoid token limits

Please provide a comprehensive answer based on the information provided."""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert financial analyst helping analyze CIM documents."},
                {"role": "user", "content": full_prompt}
            ],
            max_tokens=1000,
            temperature=0
        )
        
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating response: {str(e)}"

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
                with st.spinner("🔄 Processing CIM..."):
                    text = extract_text_from_pdf(uploaded_file)
                    if text:
                        st.session_state.cim_text = text
                        st.success(f"✅ CIM processed! Extracted {len(text):,} characters")
                        st.rerun()
    
    # Main content area
    if st.session_state.cim_text is None:
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
        show_analysis_interface(api_key)

def show_analysis_interface(api_key):
    """Show the main analysis interface after CIM is processed"""
    
    st.info(f"📄 Document loaded: {len(st.session_state.cim_text):,} characters")
    
    # Quick analysis buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Generate Summary"):
            with st.spinner("Generating summary..."):
                summary = get_openai_response(
                    "provide an executive summary of this CIM including company overview, business model, and key highlights.",
                    st.session_state.cim_text,
                    api_key
                )
                st.markdown(summary)
    
    with col2:
        if st.button("💰 Financial Metrics"):
            with st.spinner("Extracting financial metrics..."):
                metrics = get_openai_response(
                    "extract and summarize the key financial metrics including revenue, EBITDA, growth rates, and valuation information.",
                    st.session_state.cim_text,
                    api_key
                )
                st.markdown(metrics)
    
    with col3:
        if st.button("⚠️ Risk Analysis"):
            with st.spinner("Analyzing risks..."):
                risks = get_openai_response(
                    "identify and analyze the key risks and challenges mentioned in this document.",
                    st.session_state.cim_text,
                    api_key
                )
                st.markdown(risks)
    
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
                response = get_openai_response(prompt, st.session_state.cim_text, api_key)
                st.write(response)
                
                # Update chat history with response
                st.session_state.chat_history[-1] = (prompt, response)

if __name__ == "__main__":
    main()
