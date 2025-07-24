import streamlit as st
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.styling import apply_custom_css
from utils.session_state import initialize_session_state, check_document_loaded, get_api_key
from utils.ai_analysis import generate_ic_memo_section
from utils.database import log_audit_action

# Page config
st.set_page_config(
    page_title="IC Memo Generator - Auctum", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize
apply_custom_css()
initialize_session_state()

def main():
    st.markdown('<h1 class="main-title">IC Memo Generator</h1>', unsafe_allow_html=True)
    
    # Check if document is loaded
    if not check_document_loaded():
        return
    
    api_key = get_api_key()
    if not api_key:
        return
    
    st.subheader("📋 AI-Powered Investment Committee Memo")
    st.caption("Generate professional IC memos from CIM content using AI")
    
    # Memo sections with descriptions
    memo_sections = {
        "Executive Summary": "High-level overview and investment recommendation",
        "Investment Thesis": "Core reasons supporting the investment decision",
        "Business Overview": "Company description, business model, and operations",
        "Financial Analysis": "Key financial metrics, performance, and projections",
        "Market Analysis": "Market opportunity, size, and competitive landscape", 
        "Management Assessment": "Leadership team evaluation and capabilities",
        "Risk Analysis": "Key risks, challenges, and mitigation strategies",
        "Valuation": "Valuation methodology, multiples, and price justification",
        "Recommendation": "Final investment recommendation and next steps"
    }
    
    # Progress tracking
    generated_sections = len([s for s in memo_sections.keys() if s in st.session_state.ic_memo])
    total_sections = len(memo_sections)
    
    # Header with progress
    col1, col2, col3 = st.columns(3)
    col1.metric("📄 Sections", f"{generated_sections}/{total_sections}")
    col2.metric("📊 Progress", f"{int((generated_sections/total_sections)*100)}%")
    col3.metric("📝 Words", sum(len(content.split()) for content in st.session_state.ic_memo.values()))
    
    st.progress(generated_sections / total_sections)
    
    # Main actions
    col_action1, col_action2, col_action3 = st.columns(3)
    
    with col_action1:
        if st.button("🤖 Generate Complete Memo", use_container_width=True, type="primary"):
            generate_complete_memo(api_key, memo_sections)
    
    with col_action2:
        if st.session_state.ic_memo:
            if st.button("📄 Export as Markdown", use_container_width=True):
                export_memo_markdown(memo_sections)
    
    with col_action3:
        if st.session_state.ic_memo:
            if st.button("🗑️ Clear All Sections", use_container_width=True):
                st.session_state.ic_memo = {}
                st.rerun()
    
    st.divider()
    
    # Section-by-section generation and editing
    for section, description in memo_sections.items():
        with st.expander(f"📄 {section}", expanded=(section == "Executive Summary" and section not in st.session_state.ic_memo)):
            st.caption(description)
            
            # Section status
            if section in st.session_state.ic_memo:
                word_count = len(st.session_state.ic_memo[section].split())
                st.success(f"✅ Generated ({word_count} words)")
            else:
                st.info("⏳ Not generated yet")
            
            # Generate individual section
            col_gen1, col_gen2 = st.columns([2, 1])
            
            with col_gen1:
                if section not in st.session_state.ic_memo:
                    if st.button(f"🤖 Generate {section}", key=f"gen_{section}"):
                        generate_individual_section(section, api_key)
                else:
                    if st.button(f"🔄 Regenerate {section}", key=f"regen_{section}"):
                        generate_individual_section(section, api_key)
            
            with col_gen2:
                if section in st.session_state.ic_memo:
                    if st.button(f"🗑️ Clear {section}", key=f"clear_{section}"):
                        del st.session_state.ic_memo[section]
                        st.rerun()
            
            # Editable content area
            if section in st.session_state.ic_memo:
                st.markdown("**Edit Content:**")
                edited_content = st.text_area(
                    f"Content for {section}:",
                    value=st.session_state.ic_memo[section],
                    height=300,
                    key=f"edit_{section}",
                    label_visibility="collapsed"
                )
                
                # Auto-save changes
                if edited_content != st.session_state.ic_memo[section]:
                    st.session_state.ic_memo[section] = edited_content
                    st.caption("💾 Auto-saved")
            
            # Integration with red flags
            if section == "Risk Analysis" and st.session_state.red_flags:
                st.markdown("**🚨 Available Red Flags to Include:**")
                for i, flag in enumerate(st.session_state.red_flags[:3]):
                    if st.button(f"➕ Add: {flag.get('description', '')[:50]}...", key=f"add_flag_{section}_{i}"):
                        current_content = st.session_state.ic_memo.get(section, "")
                        new_content = current_content + f"\n\n• **Red Flag**: {flag.get('description', '')}"
                        st.session_state.ic_memo[section] = new_content
                        st.success("Red flag added to Risk Analysis")
                        st.rerun()

def generate_complete_memo(api_key, memo_sections):
    """Generate all memo sections at once"""
    with st.spinner("🤖 Generating complete IC memo... This may take a few minutes."):
        progress_bar = st.progress(0)
        
        for i, (section, description) in enumerate(memo_sections.items()):
            # Find relevant CIM section
            relevant_text = find_relevant_cim_section(section)
            
            # Generate content
            memo_content = generate_ic_memo_section(section, relevant_text, api_key)
            st.session_state.ic_memo[section] = memo_content
            
            # Update progress
            progress_bar.progress((i + 1) / len(memo_sections))
        
        log_audit_action("IC Memo Generated", "Complete memo generated", st.session_state.current_cim_id)
        st.success("✅ Complete IC memo generated!")
        st.rerun()

def generate_individual_section(section, api_key):
    """Generate an individual section"""
    with st.spinner(f"🤖 Generating {section}..."):
        relevant_text = find_relevant_cim_section(section)
        memo_content = generate_ic_memo_section(section, relevant_text, api_key)
        st.session_state.ic_memo[section] = memo_content
        log_audit_action("IC Memo Section Generated", section, st.session_state.current_cim_id)
        st.success(f"✅ {section} generated!")
        st.rerun()

def find_relevant_cim_section(memo_section):
    """Find the most relevant CIM section for a memo section"""
    # Mapping of memo sections to CIM section keywords
    section_mappings = {
        "Executive Summary": ["executive", "summary", "overview"],
        "Investment Thesis": ["investment", "highlights", "opportunity"],
        "Business Overview": ["business", "company", "operations", "model"],
        "Financial Analysis": ["financial", "revenue", "ebitda", "performance"],
        "Market Analysis": ["market", "industry", "competitive", "sector"],
        "Management Assessment": ["management", "team", "leadership"],
        "Risk Analysis": ["risk", "challenges", "threats"],
        "Valuation": ["valuation", "multiple", "price", "value"],
        "Recommendation": ["recommendation", "conclusion", "next steps"]
    }
    
    keywords = section_mappings.get(memo_section, [memo_section.lower()])
    
    # Find best matching CIM section
    best_match = ""
    best_score = 0
    
    for cim_section, content in st.session_state.cim_sections.items():
        score = 0
        cim_lower = cim_section.lower()
        
        for keyword in keywords:
            if keyword in cim_lower:
                score += 1
        
        if score > best_score:
            best_score = score
            best_match = content
    
    # Fallback to first part of document if no good match
    if not best_match:
        best_match = st.session_state.cim_text[:3000]
    
    return best_match

def export_memo_markdown(memo_sections):
    """Export memo as markdown"""
    markdown_content = "# Investment Committee Memo\n\n"
    markdown_content += f"**Generated on:** {datetime.now().strftime('%B %d, %Y')}\n\n"
    markdown_content += f"**Document:** {st.session_state.current_cim_id}\n\n"
    markdown_content += "---\n\n"
    
    for section in memo_sections.keys():
        if section in st.session_state.ic_memo:
            markdown_content += f"## {section}\n\n"
            markdown_content += f"{st.session_state.ic_memo[section]}\n\n"
    
    markdown_content += "---\n\n"
    markdown_content += "*Generated by Auctum Enterprise*"
    
    st.download_button(
        "⬇️ Download Markdown",
        markdown_content,
        f"ic_memo_{st.session_state.current_cim_id}.md",
        "text/markdown",
        use_container_width=True
    )
    
    log_audit_action("IC Memo Exported", "Markdown export", st.session_state.current_cim_id)

if __name__ == "__main__":
    main()
