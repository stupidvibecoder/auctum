import openai
import json
import re
import streamlit as st

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

def detect_red_flags(text, api_key):
    """Use AI to detect red flags in CIM content"""
    if not api_key:
        return []
    
    try:
        client = openai.OpenAI(api_key=api_key)
        
        # Split text into chunks for analysis
        chunks = [text[i:i+3000] for i in range(0, len(text), 3000)]
        red_flags = []
        
        for i, chunk in enumerate(chunks[:5]):  # Limit to first 5 chunks
            prompt = f"""
            Analyze this CIM section for potential red flags or inconsistencies:
            
            {chunk}
            
            Look for:
            - Financial inconsistencies or unclear assumptions
            - Missing critical information
            - Overly optimistic projections
            - Unclear business model elements
            - Risk factors that seem understated
            
            Return findings as a JSON list with format:
            [{{"description": "Issue description", "severity": "low/medium/high", "page_ref": "Section reference"}}]
            
            If no issues found, return: []
            """
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a PE due diligence expert identifying potential red flags."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0
            )
            
            try:
                flags = json.loads(response.choices[0].message.content)
                if isinstance(flags, list):
                    red_flags.extend(flags)
            except json.JSONDecodeError:
                continue
        
        return red_flags[:10]  # Return top 10 flags
        
    except Exception as e:
        st.error(f"Error detecting red flags: {e}")
        return []

def extract_valuation_metrics(text, api_key):
    """Extract valuation metrics using AI"""
    if not api_key:
        return {}
    
    try:
        client = openai.OpenAI(api_key=api_key)
        
        prompt = f"""
        Extract valuation-related metrics from this CIM content:
        
        {text[:4000]}
        
        Look for and extract:
        - Revenue (historical and projected)
        - EBITDA (historical and projected)
        - Growth rates
        - Valuation multiples (EV/Revenue, EV/EBITDA)
        - Comparable company data
        
        Return as JSON with format:
        {{
            "revenue_2023": number,
            "revenue_2024": number,
            "ebitda_2023": number,
            "ebitda_2024": number,
            "ev_revenue_multiple": number,
            "ev_ebitda_multiple": number,
            "revenue_growth_rate": number
        }}
        
        Use null for missing values.
        """
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a financial analyst extracting valuation data."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=400,
            temperature=0
        )
        
        try:
            return json.loads(response.choices[0].message.content)
        except json.JSONDecodeError:
            return {}
            
    except Exception as e:
        st.error(f"Error extracting valuation metrics: {e}")
        return {}

def generate_ic_memo_section(section_name, section_text, api_key):
    """Generate IC memo section using AI"""
    if not api_key or not section_text:
        return f"No content available for {section_name}."
    
    try:
        client = openai.OpenAI(api_key=api_key)
        
        prompt = f"""
        Based on this CIM section, write the {section_name} portion of an investment committee memo.
        
        CIM Content:
        {section_text[:2000]}
        
        Write in a professional, concise style suitable for senior executives. Include only the most relevant insights and key decision-making information.
        
        Use clear formatting with bullet points where appropriate.
        """
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a senior investment professional writing IC memos."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=600,
            temperature=0
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"Error generating {section_name}: {str(e)}"

def generate_quick_analysis(analysis_type, text, api_key):
    """Generate quick analysis for different types"""
    if not api_key:
        return "API key required for analysis"
    
    try:
        client = openai.OpenAI(api_key=api_key)
        
        prompts = {
            "executive_summary": "Provide an executive summary of this CIM including company overview, business model, and key highlights.",
            "financial_analysis": "Extract and analyze key financial metrics including revenue, EBITDA, growth rates, and valuation information.",
            "risk_assessment": "Identify and analyze the key risks and challenges mentioned in this document."
        }
        
        prompt = prompts.get(analysis_type, "Analyze this CIM document.")
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert financial analyst."},
                {"role": "user", "content": f"{prompt}\n\nCIM Content: {text[:3000]}"}
            ],
            max_tokens=800,
            temperature=0
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"Error generating analysis: {str(e)}"

def chat_with_cim(question, context, api_key):
    """Chat interface for CIM questions"""
    if not api_key:
        return "API key required for chat functionality"
    
    try:
        client = openai.OpenAI(api_key=api_key)
        
        full_prompt = f"Based on this CIM: {context[:4000]}\n\nQuestion: {question}"
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert financial analyst helping analyze CIM documents."},
                {"role": "user", "content": full_prompt}
            ],
            max_tokens=800,
            temperature=0
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"Error: {str(e)}"
