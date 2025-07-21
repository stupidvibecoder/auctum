import os
from langchain_community.document_loaders import PyPDFLoader, UnstructuredPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_with_pdfplumber(file_path):
    """
    Load PDF using pdfplumber as a fallback method
    """
    try:
        import pdfplumber
        from langchain.schema import Document
        
        documents = []
        
        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text and text.strip():
                    # Create a Document object similar to LangChain loaders
                    doc = Document(
                        page_content=text,
                        metadata={
                            "source": file_path,
                            "page": page_num + 1
                        }
                    )
                    documents.append(doc)
        
        return documents
    except ImportError:
        raise Exception("pdfplumber not installed. Run: pip install pdfplumber")

def load_cim(file_path):
    """
    Load and parse CIM PDF with multiple fallback methods
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"PDF file not found: {file_path}")
    
    # Try multiple loading methods
    loaders = [
        ("PyPDFLoader", lambda: PyPDFLoader(file_path).load()),
        ("PDFPlumber", lambda: load_with_pdfplumber(file_path)),
        ("UnstructuredPDFLoader", lambda: UnstructuredPDFLoader(file_path).load())
    ]
    
    for loader_name, loader_func in loaders:
        try:
            logger.info(f"Trying {loader_name}...")
            pages = loader_func()
            
            if pages and any(page.page_content.strip() for page in pages):
                logger.info(f"Successfully loaded {len(pages)} pages with {loader_name}")
                return pages
            else:
                logger.warning(f"{loader_name} returned empty content")
                
        except Exception as e:
            logger.error(f"{loader_name} failed: {str(e)}")
            continue
    
    raise Exception("All PDF loading methods failed. PDF might be scanned/image-based or corrupted.")

def split_documents(documents, chunk_size=1000, chunk_overlap=200):
    """
    Split documents into smaller chunks for better retrieval
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )
    
    return text_splitter.split_documents(documents)

def extract_text_from_cim(file_path):
    """
    Main function to extract and process CIM text
    """
    try:
        # Load the PDF
        documents = load_cim(file_path)
        
        # Split into chunks
        chunks = split_documents(documents)
        
        # Basic extraction stats
        total_chars = sum(len(chunk.page_content) for chunk in chunks)
        
        logger.info(f"Extraction complete:")
        logger.info(f"- Total pages: {len(documents)}")
        logger.info(f"- Total chunks: {len(chunks)}")
        logger.info(f"- Total characters: {total_chars}")
        
        return {
            'documents': documents,
            'chunks': chunks,
            'stats': {
                'pages': len(documents),
                'chunks': len(chunks),
                'total_chars': total_chars
            }
        }
        
    except Exception as e:
        logger.error(f"Extraction failed: {str(e)}")
        raise

if __name__ == "__main__":
    # Test the extraction
    pdf_path = "YourCIM.pdf"
    
    if os.path.exists(pdf_path):
        try:
            result = extract_text_from_cim(pdf_path)
            
            # Preview first chunk
            if result['chunks']:
                print("\nFirst chunk preview:")
                print("-" * 50)
                print(result['chunks'][0].page_content[:500])
                print("-" * 50)
            
        except Exception as e:
            print(f"Error: {e}")
    else:
        print(f"PDF file '{pdf_path}' not found in current directory")
        print(f"Current directory: {os.getcwd()}")
        print("Available files:", [f for f in os.listdir('.') if f.endswith('.pdf')])