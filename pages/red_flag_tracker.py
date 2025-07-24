import streamlit as st
import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.styling import apply_custom_css
from utils.session_state import initialize_session_state, check_document_loaded, get_api_key
from utils.ai_analysis import detect_red_flags
from utils.database import log_audit_action

# Page config
st.set_page_config(
    page_title="Red Flag Tracker - Auctum", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize
apply_custom_css()
initialize_session_state()

def main():
    st.markdown('<h1 class="main-title">Red Flag Tracker</h1>', unsafe_allow_html=True)
    
    # Check if document is loaded
    if not check_document_loaded():
        return
    
    api_key = get_api_key()
    
    st.subheader("🚨 AI-Powered Risk Detection & Analysis")
    st.caption("Automatic identification of inconsistencies and potential issues")
    
    # Red flag summary dashboard
    if st.session_state.red_flags:
        display_red_flag_dashboard()
    else:
        st.info("✅ No red flags detected in initial analysis. You can run a re-analysis or report manual red flags below.")
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if api_key and st.button("🔄 Re-analyze Document", use_container_width=True):
            reanalyze_document(api_key)
    
    with col2:
        if st.button("📋 Export Red Flags", use_container_width=True, disabled=not st.session_state.red_flags):
            export_red_flags()
    
    with col3:
        if st.button("🧹 Clear All Flags", use_container_width=True, disabled=not st.session_state.red_flags):
            clear_all_flags()
    
    st.divider()
    
    # Display individual red flags
    if st.session_state.red_flags:
        display_red_flags()
    
    st.divider()
    
    # Manual red flag reporting
    st.markdown("### ➕ Report Manual Red Flag")
    report_manual_red_flag()
    
    # Red flag analytics
    if st.session_state.red_flags:
        st.divider()
        display_red_flag_analytics()

def display_red_flag_dashboard():
    """Display red flag summary dashboard"""
    col1, col2, col3, col4 = st.columns(4)
    
    # Count flags by severity
    severity_counts = {"high": 0, "medium": 0, "low": 0}
    status_counts = {"open": 0, "resolved": 0, "investigating": 0}
    
    for flag in st.session_state.red_flags:
        severity = flag.get('severity', 'medium')
        status = flag.get('status', 'open')
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
        status_counts[status] = status_counts.get(status, 0) + 1
    
    col1.metric("🔴 High Severity", severity_counts["high"])
    col2.metric("🟡 Medium Severity", severity_counts["medium"])  
    col3.metric("🟢 Low Severity", severity_counts["low"])
    col4.metric("📌 Open Issues", status_counts["open"])

def display_red_flags():
    """Display all red flags with actions"""
    st.markdown("### 🚨 Detected Red Flags")
    
    # Filter options
    col_filter1, col_filter2 = st.columns(2)
    with col_filter1:
        severity_filter = st.selectbox("Filter by Severity", ["All", "high", "medium", "low"])
    with col_filter2:
        status_filter = st.selectbox("Filter by Status", ["All", "open", "resolved", "investigating"])
    
    # Apply filters
    filtered_flags = st.session_state.red_flags
    if severity_filter != "All":
        filtered_flags = [f for f in filtered_flags if f.get('severity') == severity_filter]
    if status_filter != "All":
        filtered_flags = [f for f in filtered_flags if f.get('status', 'open') == status_filter]
    
    if not filtered_flags:
        st.info("No red flags match the current filters.")
        return
    
    # Display filtered flags
    for i, flag in enumerate(filtered_flags):
        display_individual_red_flag(flag, i)

def display_individual_red_flag(flag, index):
    """Display an individual red flag with actions"""
    severity = flag.get('severity', 'medium')
    status = flag.get('status', 'open')
    description = flag.get('description', 'No description available')
    page_ref = flag.get('page_ref', 'General')
    
    # Severity styling
    severity_config = {
        'high': {'emoji': '🔴', 'color': '#ef4444'},
        'medium': {'emoji': '🟡', 'color': '#f59e0b'},
        'low': {'emoji': '🟢', 'color': '#10b981'}
    }
    
    config = severity_config.get(severity, severity_config['medium'])
    
    # Status styling
    status_config = {
        'open': {'emoji': '📌', 'color': '#ef4444'},
        'investigating': {'emoji': '🔍', 'color': '#f59e0b'},
        'resolved': {'emoji': '✅', 'color': '#10b981'}
    }
    
    status_info = status_config.get(status, status_config['open'])
    
    # Red flag card
    flag_html = f"""
    <div class="red-flag" style="border-left-color: {config['color']};">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
            <strong>{config['emoji']} Red Flag #{index + 1}</strong>
            <div style="display: flex; gap: 1rem;">
                <span style="font-size: 0.8rem; opacity: 0.7;">{severity.upper()}</span>
                <span style="font-size: 0.8rem; color: {status_info['color']};">{status_info['emoji']} {status.upper()}</span>
            </div>
        </div>
        <div style="margin-bottom: 0.5rem; line-height: 1.5;">
            {description}
        </div>
        <div style="font-size: 0.8rem; opacity: 0.8;">
            📍 Reference: {page_ref}
        </div>
    </div>
    """
    st.markdown(flag_html, unsafe_allow_html=True)
    
    # Action buttons
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if status != 'resolved' and st.button("✅ Resolve", key=f"resolve_flag_{index}"):
            st.session_state.red_flags[index]['status'] = 'resolved'
            log_audit_action("Red Flag Resolved", description[:50], st.session_state.current_cim_id)
            st.success("✅ Flag marked as resolved")
            st.rerun()
    
    with col2:
        if status != 'investigating' and st.button("🔍 Investigate", key=f"investigate_flag_{index}"):
            st.session_state.red_flags[index]['status'] = 'investigating'
            log_audit_action("Red Flag Investigation Started", description[:50], st.session_state.current_cim_id)
            st.info("🔍 Marked for investigation")
            st.rerun()
    
    with col3:
        if st.button("📋 Add to IC Memo", key=f"add_flag_{index}"):
            # Add to risk analysis section of IC memo
            risk_section = st.session_state.ic_memo.get('Risk Analysis', '')
            risk_section += f"\n\n• **{severity.title()} Risk**: {description}"
            st.session_state.ic_memo['Risk Analysis'] = risk_section
            st.success("✅ Added to IC memo Risk Analysis section")
    
    with col4:
        if st.button("🗑️ Remove", key=f"remove_flag_{index}"):
            st.session_state.red_flags.pop(index)
            log_audit_action("Red Flag Removed", description[:50], st.session_state.current_cim_id)
            st.success("🗑️ Red flag removed")
            st.rerun()
    
    st.markdown("---")

def report_manual_red_flag():
    """Interface for reporting manual red flags"""
    with st.form("manual_red_flag_form"):
        st.markdown("Report issues not caught by AI analysis:")
        
        col1, col2 = st.columns(2)
        with col1:
            manual_description = st.text_area("Describe the red flag or concern:", height=100)
            manual_severity = st.selectbox("Severity Level", ["low", "medium", "high"])
        
        with col2:
            manual_section = st.selectbox(
                "Related Section", 
                ["General"] + list(st.session_state.cim_sections.keys()) if st.session_state.cim_sections else ["General"]
            )
            category = st.selectbox("Category", [
                "Financial Inconsistency",
                "Missing Information", 
                "Unrealistic Projections",
                "Market Risk",
                "Operational Risk",
                "Legal/Compliance Risk",
                "Other"
            ])
        
        if st.form_submit_button("🚨 Report Red Flag", use_container_width=True):
            if manual_description:
                new_flag = {
                    'description': f"[{category}] {manual_description}",
                    'severity': manual_severity,
                    'page_ref': manual_section,
                    'status': 'open',
                    'source': 'manual',
                    'timestamp': datetime.now().isoformat()
                }
                st.session_state.red_flags.append(new_flag)
                log_audit_action("Manual Red Flag Reported", manual_description[:50], st.session_state.current_cim_id)
                st.success("🚨 Red flag reported successfully!")
                st.rerun()
            else:
                st.warning("Please provide a description for the red flag.")

def reanalyze_document(api_key):
    """Re-run AI analysis on the document"""
    with st.spinner("🔄 Re-analyzing document for red flags..."):
        new_flags = detect_red_flags(st.session_state.cim_text, api_key)
        
        # Merge with existing manual flags
        manual_flags = [f for f in st.session_state.red_flags if f.get('source') == 'manual']
        st.session_state.red_flags = new_flags + manual_flags
        
        log_audit_action("Red Flag Re-analysis", f"Found {len(new_flags)} new flags", st.session_state.current_cim_id)
        
        if new_flags:
            st.success(f"✅ Re-analysis complete! Found {len(new_flags)} potential red flags.")
        else:
            st.info("✅ Re-analysis complete. No new red flags detected.")
        
        st.rerun()

def export_red_flags():
    """Export red flags as CSV"""
    import pandas as pd
    
    export_data = []
    for i, flag in enumerate(st.session_state.red_flags):
        export_data.append({
            'ID': i + 1,
            'Description': flag.get('description', ''),
            'Severity': flag.get('severity', 'medium'),
            'Status': flag.get('status', 'open'),
            'Section': flag.get('page_ref', 'General'),
            'Source': flag.get('source', 'ai'),
            'Timestamp': flag.get('timestamp', '')
        })
    
    if export_data:
        df = pd.DataFrame(export_data)
        csv = df.to_csv(index=False).encode('utf-8')
        
        st.download_button(
            "⬇️ Download Red Flags CSV",
            csv,
            f"red_flags_{st.session_state.current_cim_id}.csv",
            "text/csv",
            use_container_width=True
        )
        
        log_audit_action("Red Flags Exported", f"Exported {len(export_data)} flags", st.session_state.current_cim_id)

def clear_all_flags():
    """Clear all red flags"""
    if st.button("⚠️ Confirm: Clear All Red Flags", type="secondary"):
        flag_count = len(st.session_state.red_flags)
        st.session_state.red_flags = []
        log_audit_action("All Red Flags Cleared", f"Cleared {flag_count} flags", st.session_state.current_cim_id)
        st.success(f"🧹 Cleared {flag_count} red flags")
        st.rerun()

def display_red_flag_analytics():
    """Display analytics about red flags"""
    st.markdown("### 📊 Red Flag Analytics")
    
    if not st.session_state.red_flags:
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Severity distribution
        severity_counts = {}
        for flag in st.session_state.red_flags:
            severity = flag.get('severity', 'medium')
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        st.markdown("**Severity Distribution:**")
        for severity, count in severity_counts.items():
            percentage = (count / len(st.session_state.red_flags)) * 100
            st.write(f"• {severity.title()}: {count} ({percentage:.1f}%)")
    
    with col2:
        # Section distribution
        section_counts = {}
        for flag in st.session_state.red_flags:
            section = flag.get('page_ref', 'General')
            section_counts[section] = section_counts.get(section, 0) + 1
        
        st.markdown("**Section Distribution:**")
        sorted_sections = sorted(section_counts.items(), key=lambda x: x[1], reverse=True)
        for section, count in sorted_sections[:5]:  # Top 5 sections
            st.write(f"• {section}: {count} flags")

if __name__ == "__main__":
    main()
