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

# Fix arrow icon CSS issue
st.markdown("""
<style>
    .stApp > header {
        background-color: transparent;
    }
    
    .stApp > header [data-testid="stHeader"] {
        display: none;
    }
</style>
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
    # Split document into overlapping chunks
    chunks = []
    overlap = 500
    
    for i in range(0, len(text), chunk_size - overlap):
        chunk = text[i:i + chunk_size]
        if chunk.strip():
            chunks.append((chunk, i))  # Store chunk and position
    
    # Score chunks based on query terms
    scored_chunks = []
    for chunk, position in chunks:
        chunk_lower = chunk.lower()
        score = 0
        
        for term in query_terms:
            score += chunk_lower.count(term.lower())
        
        if score > 0:
            scored_chunks.append((chunk, score, position))
    
    # Sort by score and return top chunks
    scored_chunks.sort(key=lambda x: x[1], reverse=True)
    return [chunk for chunk, score, pos in scored_chunks[:5]]  # Top 5 relevant chunks

def get_openai_response(prompt, context, api_key):
    """Get response from OpenAI with smart document search"""
    try:
        client = openai.OpenAI(api_key=api_key)
        
        # Define search terms based on the prompt
        financial_terms = ['revenue', 'sales', 'income', 'ebitda', 'profit', 'margin', 'growth', 'financial', 'cash flow', 'valuation', 'multiple', 'earnings']
        risk_terms = ['risk', 'challenge', 'threat', 'competition', 'regulatory', 'compliance', 'debt', 'liability', 'uncertainty']
        summary_terms = ['overview', 'summary', 'business', 'company', 'industry', 'market', 'opportunity', 'investment', 'strategy']
        
        # Determine what type of analysis this is
        prompt_lower = prompt.lower()
        if any(term in prompt_lower for term in ['financial', 'revenue', 'ebitda', 'profit', 'metrics']):
            search_terms = financial_terms
        elif any(term in prompt_lower for term in ['risk', 'challenge', 'threat']):
            search_terms = risk_terms
        elif any(term in prompt_lower for term in ['summary', 'overview', 'business']):
            search_terms = summary_terms
        else:
            # For general questions, extract key words from the prompt
            search_terms = [word for word in prompt_lower.split() if len(word) > 3]
        
        # Search for relevant sections
        relevant_sections = search_document_sections(context, search_terms)
        
        if relevant_sections:
            # Use relevant sections found by search
            combined_context = "\n\n--- RELEVANT SECTION ---\n\n".join(relevant_sections)
            context_info = f"Analysis based on {len(relevant_sections)} relevant sections found in the document"
        else:
            # Fallback to previous method if no specific sections found
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
