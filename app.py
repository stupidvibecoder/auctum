import streamlit as st
import os
import tempfile
from openai import OpenAI

# Page config
st.set_page_config(
    page_title="Auctum - CIM Analyzer",
    page_icon="📊",
    layout="wide"
)

def extract_pdf_text(uploaded_file):
    """Extract text from PDF using pypdf"""
    try:
        from pypdf import PdfReader
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name
        
        # Extract text
        reader = PdfReader(tmp_path)
        full_text = ""
        
        for page_num, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                full_text += f"\n\n--- PAGE {page_num + 1} ---\n\n" + text
        
        # Clean up
        os.unlink(tmp_path)
        
        return full_text, len(reader.pages)
        
    except Exception as e:
        st.error(f"Error extracting PDF: {e}")
        return None, 0

def analyze_with_openai(text, prompt_type, custom_question=None):
    """Analyze text using OpenAI"""
    try:
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        
        # Truncate text if too long (OpenAI has token limits)
        max_chars = 12000
        if len(text) > max_chars:
            text = text[:max_chars] + "\n\n[Document truncated for analysis...]"
        
        prompts = {
            "summary": """Analyze this CIM and provide an executive summary with:
1. Company Overview
2. Business Model  
3. Key Financial Metrics
4. Investment Highlights
5. Market Position""",
            
            "financial": """Extract and organize key financial metrics:
- Revenue (historical and projected)
- EBITDA and margins
- Growth rates
- Cash flow
- Valuation metrics""",
            
            "risks": """Identify and categorize risks mentioned:
- Market Risks
- Operational Risks  
- Financial Risks
- Regulatory Risks
- Other Risks""",
            
            "custom": custom_question or "Analyze this document."
        }
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert financial analyst reviewing a CIM (Confidential Information Memorandum)."},
                {"role": "user", "content": f"{prompts[prompt_type]}\n\nDocument:\n{text}"}
            ],
            temperature=0.1,
            max_tokens=1500
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"Analysis error: {str(e)}"

def main():
    st.title("🏢 Auctum - CIM Intelligence Platform")
    st.subheader("Upload your Confidential Information Memorandum and get AI-powered insights")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # API Key
        api_key = st.text_input("OpenAI API Key", type="password")
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
            st.success("✅ API key configured")
        else:
            st.warning("⚠️ Enter OpenAI API key to continue")
        
        st.divider()
        
        # File upload
        st.header("📄 Upload CIM")
        uploaded_file = st.file_uploader("Choose PDF file", type=['pdf'])
    
    # Main content
    if uploaded_file and api_key:
        # Process PDF
        with st.spinner("📖 Extracting text from PDF..."):
            full_text, num_pages = extract_pdf_text(uploaded_file)
        
        if full_text:
            st.success(f"✅ Processed {num_pages} pages successfully!")
            
            # Store in session state
            if 'pdf_text' not in st.session_state:
                st.session_state.pdf_text = full_text
            
            # Analysis buttons
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📊 Generate Summary", type="primary"):
                    with st.spinner("Generating summary..."):
                        summary = analyze_with_openai(full_text, "summary")
                        st.markdown("### Executive Summary")
                        st.markdown(summary)
            
            with col2:
                if st.button("💰 Financial Metrics"):
                    with st.spinner("Extracting metrics..."):
                        metrics = analyze_with_openai(full_text, "financial")
                        st.markdown("### Financial Metrics")
                        st.markdown(metrics)
            
            with col3:
                if st.button("⚠️ Risk Analysis"):
                    with st.spinner("Analyzing risks..."):
                        risks = analyze_with_openai(full_text, "risks")
                        st.markdown("### Risk Analysis")
                        st.markdown(risks)
            
            st.divider()
            
            # Q&A Section
            st.header("💬 Ask Questions")
            question = st.text_input("Ask a question about this CIM...")
            
            if question:
                with st.spinner("Thinking..."):
                    answer = analyze_with_openai(full_text, "custom", question)
                    st.markdown("### Answer")
                    st.markdown(answer)
            
            # Document preview
            with st.expander("📄 Document Preview"):
                st.text_area("Extracted Text (first 2000 characters)", 
                           full_text[:2000], height=300)
    
    else:
        # Welcome screen
        st.markdown("""
        ### 🚀 Welcome to Auctum MVP
        
        **Get started:**
        1. Enter your OpenAI API key in the sidebar
        2. Upload a CIM PDF file  
        3. Click analysis buttons or ask questions
        
        **Features:**
        - 📊 Executive summaries
        - 💰 Financial analysis  
        - ⚠️ Risk assessment
        - 💬 Smart Q&A
        """)

if __name__ == "__main__":
    main()
