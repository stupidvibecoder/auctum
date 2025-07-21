import os
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
import tempfile
import logging

logger = logging.getLogger(__name__)

class CIMAnalyzer:
    def __init__(self, document_chunks):
        """
        Initialize the CIM analyzer with document chunks
        """
        self.document_chunks = document_chunks
        self.llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo")
        self.embeddings = OpenAIEmbeddings()
        
        # Create vector store for retrieval
        self.setup_vector_store()
        
    def setup_vector_store(self):
        """Set up vector store for document retrieval"""
        try:
            # Create temporary directory for Chroma DB
            self.temp_dir = tempfile.mkdtemp()
            
            # Create vector store with better search settings
            self.vectorstore = Chroma.from_documents(
                documents=self.document_chunks,
                embedding=self.embeddings,
                persist_directory=self.temp_dir
            )
            
            # Create retrieval chain with more chunks
            self.qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=self.vectorstore.as_retriever(
                    search_type="similarity",
                    search_kwargs={"k": 8}  # Increased from 4 to 8
                ),
                return_source_documents=True
            )
            
            logger.info("Vector store and QA chain initialized successfully")
            logger.info(f"Indexed {len(self.document_chunks)} document chunks")
            
        except Exception as e:
            logger.error(f"Error setting up vector store: {e}")
            raise
    
    def answer_question(self, question):
        """Answer a question about the CIM using enhanced retrieval"""
        try:
            # Use the existing QA chain which already does vector search
            result = self.qa_chain({"query": question})
            
            # Additionally, get more context if the question seems complex
            if len(question) > 50 or any(word in question.lower() for word in ['detailed', 'comprehensive', 'all', 'complete']):
                # Get additional relevant chunks
                extra_docs = self.get_similar_documents(question, k=6)
                extra_context = "\n\n".join([doc.page_content for doc in extra_docs])
                
                # If the initial answer is short, enhance it
                if len(result["result"]) < 200:
                    enhanced_prompt = f"""
                    Question: {question}
                    
                    Initial answer: {result["result"]}
                    
                    Additional context from document: {extra_context[:3000]}
                    
                    Please provide a more comprehensive answer using all available context.
                    """
                    
                    enhanced_response = self.llm.invoke(enhanced_prompt)
                    return enhanced_response.content
            
            return result["result"]
            
        except Exception as e:
            logger.error(f"Error answering question: {e}")
            return f"Sorry, I encountered an error: {str(e)}"
    
    def generate_summary(self):
        """Generate an executive summary of the CIM"""
        # Use vector search to get comprehensive overview
        summary_queries = [
            "executive summary overview",
            "business model revenue", 
            "financial performance metrics",
            "company description industry",
            "investment highlights value proposition"
        ]
        
        # Gather relevant content from across the document
        relevant_chunks = []
        for query in summary_queries:
            docs = self.get_similar_documents(query, k=4)
            relevant_chunks.extend(docs)
        
        # Remove duplicates and get comprehensive context
        unique_content = list(set([doc.page_content for doc in relevant_chunks]))
        context = "\n\n".join(unique_content[:15])  # More comprehensive context
        
        summary_prompt = """
        Based on the following CIM document, provide a comprehensive executive summary that includes:
        
        1. **Company Overview**: What does the company do? What industry/sector?
        2. **Business Model**: How does the company make money?
        3. **Key Metrics**: Revenue, EBITDA, growth rates (if available)
        4. **Investment Highlights**: Main selling points
        5. **Market Position**: Competitive advantages
        
        Please be concise but comprehensive. Use bullet points where appropriate.
        
        Document content: {context}
        """
        
        try:
            response = self.llm.invoke(summary_prompt.format(context=context))
            return response.content
        except Exception as e:
            return f"Error generating summary: {str(e)}"
    
    def extract_financial_metrics(self):
        """Extract key financial metrics from the CIM"""
        # Use vector search to find financial information
        financial_queries = [
            "revenue sales financial performance",
            "EBITDA profit margin earnings",
            "growth rate year over year",
            "cash flow financial statements",
            "valuation multiple enterprise value"
        ]
        
        # Gather financial content from across the document
        relevant_chunks = []
        for query in financial_queries:
            docs = self.get_similar_documents(query, k=4)
            relevant_chunks.extend(docs)
        
        # Remove duplicates and combine
        unique_content = list(set([doc.page_content for doc in relevant_chunks]))
        context = "\n\n".join(unique_content[:12])  # Financial-focused context
        
        metrics_prompt = """
        Extract and summarize the key financial metrics from this CIM document:
        
        Look for and organize:
        - **Revenue**: Historical and projected
        - **EBITDA**: Historical and margins
        - **Growth Rates**: Year-over-year growth
        - **Valuation Metrics**: Multiples, enterprise value
        - **Profitability**: Gross margins, operating margins
        - **Cash Flow**: Operating cash flow, free cash flow
        
        Present in a clear, organized format. If specific numbers aren't available, note that.
        
        Document content: {context}
        """
        
        try:
            response = self.llm.invoke(metrics_prompt.format(context=context))
            return response.content
        except Exception as e:
            return f"Error extracting metrics: {str(e)}"
    
    def analyze_risks(self):
        """Analyze potential risks mentioned in the CIM"""
        # Use vector search to find risk-related content
        risk_queries = [
            "risks challenges threats",
            "competition competitive market risks", 
            "financial risks debt liquidity",
            "operational risks management",
            "regulatory compliance legal risks"
        ]
        
        # Gather risk-related content from across the document
        relevant_chunks = []
        for query in risk_queries:
            docs = self.get_similar_documents(query, k=3)
            relevant_chunks.extend(docs)
        
        # Remove duplicates and combine
        unique_content = list(set([doc.page_content for doc in relevant_chunks]))
        context = "\n\n".join(unique_content[:10])  # Top 10 unique chunks
        
        risks_prompt = """
        Analyze potential risks and challenges mentioned in this CIM document:
        
        Identify and categorize:
        - **Market Risks**: Industry trends, competition, market size
        - **Operational Risks**: Management, operations, scalability
        - **Financial Risks**: Debt, cash flow, capital requirements
        - **Regulatory Risks**: Compliance, legal issues
        - **Other Risks**: Technology, customer concentration, etc.
        
        For each risk category, provide specific examples from the document if available.
        
        Document content: {context}
        """
        
        try:
            response = self.llm.invoke(risks_prompt.format(context=context))
            return response.content
        except Exception as e:
            return f"Error analyzing risks: {str(e)}"
    
    def _get_document_context(self, max_chars=8000):
        """Get document context for prompts"""
        # Combine first few chunks for context
        context = ""
        for chunk in self.document_chunks[:10]:  # First 10 chunks
            if len(context) + len(chunk.page_content) > max_chars:
                break
            context += chunk.page_content + "\n\n"
        
        return context[:max_chars]
    
    def get_similar_documents(self, query, k=3):
        """Get similar document chunks for a query"""
        try:
            docs = self.vectorstore.similarity_search(query, k=k)
            return docs
        except Exception as e:
            logger.error(f"Error retrieving similar documents: {e}")
            return []

# Example usage and testing
if __name__ == "__main__":
    # This would typically be called from the main app
    print("CIM Analyzer module loaded successfully")
    print("Use this module with processed document chunks from extract.py")