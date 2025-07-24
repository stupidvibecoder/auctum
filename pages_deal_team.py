import streamlit as st
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.styling import apply_custom_css
from utils.session_state import initialize_session_state, check_document_loaded, TEAM_MEMBERS, COMMON_TAGS, render_user_avatar
from utils.database import get_tasks_for_section, create_task, update_task_status, log_audit_action

# Page config
st.set_page_config(
    page_title="Deal Team Workspace - Auctum", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize
apply_custom_css()
initialize_session_state()

def main():
    st.markdown('<h1 class="main-title">Deal Team Workspace</h1>', unsafe_allow_html=True)
    
    # Check if document is loaded
    if not check_document_loaded():
        return
    
    st.subheader("🧑‍💼 Team Collaboration & Task Management")
    st.caption("Collaborate on sections, assign tasks, and manage workflow")
    
    # Document info
    st.info(f"📄 **Working on**: {len(st.session_state.cim_text):,} characters | {len(st.session_state.cim_sections)} sections | Document ID: {st.session_state.current_cim_id}")
    
    # Main workspace layout
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### 📂 Sections")
        
        if st.session_state.cim_sections:
            selected_section = st.selectbox(
                "Select a section:",
                list(st.session_state.cim_sections.keys()),
                key="workspace_section"
            )
            
            if selected_section:
                # Section statistics
                section_text = st.session_state.cim_sections.get(selected_section, "")
                tasks = get_tasks_for_section(st.session_state.current_cim_id, selected_section)
                
                st.metric("Characters", len(section_text))
                st.metric("Total Tasks", len(tasks))
                
                open_tasks = len([t for t in tasks if t[6] == 'open'])  # status is at index 6
                st.metric("Open Tasks", open_tasks)
                
                # Section preview
                if section_text:
                    with st.expander("📖 Section Preview"):
                        preview = section_text[:500] + "..." if len(section_text) > 500 else section_text
                        st.text_area("Content:", preview, height=100, disabled=True)
        else:
            st.warning("No sections available. Process the CIM document first.")
    
    with col2:
        if st.session_state.cim_sections and selected_section:
            st.markdown(f"### 📋 {selected_section}")
            
            # Task creation form
            st.markdown("#### ➕ Create New Task")
            
            with st.form(f"task_form_{selected_section}"):
                col_a, col_b = st.columns(2)
                
                with col_a:
                    task_title = st.text_input("Task Title", placeholder="e.g., Verify revenue assumptions")
                    assigned_to = st.selectbox("Assign to", [""] + TEAM_MEMBERS)
                
                with col_b:
                    due_date = st.date_input("Due Date", value=datetime.now().date() + timedelta(days=7))
                    priority = st.selectbox("Priority", ["Low", "Medium", "High", "Critical"])
                
                task_description = st.text_area("Description", placeholder="Detailed task description...")
                
                if st.form_submit_button("➕ Create Task", use_container_width=True):
                    if task_title and assigned_to:
                        try:
                            task_id = create_task(
                                st.session_state.current_cim_id,
                                task_title,
                                task_description,
                                assigned_to,
                                due_date,
                                selected_section
                            )
                            
                            log_audit_action("Task Created", f"{task_title} assigned to {assigned_to}", st.session_state.current_cim_id)
                            st.success(f"✅ Task '{task_title}' created and assigned to {assigned_to}!")
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"Error creating task: {e}")
                    else:
                        st.warning("Please fill in task title and assignee.")
            
            st.divider()
            
            # Display existing tasks
            st.markdown("#### 📝 Tasks")
            
            if st.session_state.current_cim_id:
                tasks = get_tasks_for_section(st.session_state.current_cim_id, selected_section)
                
                if tasks:
                    # Task filtering
                    col_filter1, col_filter2 = st.columns(2)
                    with col_filter1:
                        status_filter = st.selectbox("Filter by Status", ["All", "open", "in_progress", "completed"])
                    with col_filter2:
                        show_completed = st.checkbox("Show Completed", value=True)
                    
                    # Filter tasks
                    filtered_tasks = tasks
                    if status_filter != "All":
                        filtered_tasks = [t for t in tasks if t[6] == status_filter]
                    if not show_completed:
                        filtered_tasks = [t for t in filtered_tasks if t[6] != 'completed']
                    
                    # Display tasks
                    for task in filtered_tasks:
                        task_id, cim_id, title, description, assigned_to, due_date, status, section, timestamp = task
                        
                        # Task card styling based on status
                        status_class = f"task-{status.replace(' ', '-')}"
                        
                        # Status indicators
                        status_icons = {
                            "open": "📌",
                            "in_progress": "⏳", 
                            "completed": "✅"
                        }
                        
                        # Priority colors
                        priority_colors = {
                            "Critical": "🚨",
                            "High": "⚠️",
                            "Medium": "📋",
                            "Low": "📝"
                        }
                        
                        # Format dates
                        try:
                            created_date = datetime.fromisoformat(timestamp).strftime("%m/%d")
                            due_date_formatted = datetime.strptime(due_date, "%Y-%m-%d").strftime("%m/%d")
                        except:
                            created_date = "Unknown"
                            due_date_formatted = due_date
                        
                        # Render task card
                        task_html = f"""
                        <div class="task-card {status_class}">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                                <div style="display: flex; align-items: center;">
                                    {render_user_avatar(assigned_to)}
                                    <strong>{title}</strong>
                                </div>
                                <span style="font-size: 0.8rem; opacity: 0.7;">
                                    {status_icons.get(status, '📌')} {status.upper()}
                                </span>
                            </div>
                            <div style="margin: 0.5rem 0;">
                                {description if description else 'No description provided'}
                            </div>
                            <div style="font-size: 0.8rem; opacity: 0.8; display: flex; justify-content: space-between;">
                                <span>👤 {assigned_to}</span>
                                <span>📅 Due: {due_date_formatted} | Created: {created_date}</span>
                            </div>
                        </div>
                        """
                        st.markdown(task_html, unsafe_allow_html=True)
                        
                        # Task action buttons
                        col_action1, col_action2, col_action3, col_action4 = st.columns(4)
                        
                        with col_action1:
                            if status == 'open' and st.button("🏃 Start", key=f"start_{task_id}"):
                                update_task_status(task_id, 'in_progress')
                                log_audit_action("Task Started", title, st.session_state.current_cim_id)
                                st.success(f"Task '{title}' started!")
                                st.rerun()
                        
                        with col_action2:
                            if status in ['open', 'in_progress'] and st.button("✅ Complete", key=f"complete_{task_id}"):
                                update_task_status(task_id, 'completed')
                                log_audit_action("Task Completed", title, st.session_state.current_cim_id)
                                st.success(f"Task '{title}' completed!")
                                st.rerun()
                        
                        with col_action3:
                            if status == 'completed' and st.button("↩️ Reopen", key=f"reopen_{task_id}"):
                                update_task_status(task_id, 'open')
                                log_audit_action("Task Reopened", title, st.session_state.current_cim_id)
                                st.info(f"Task '{title}' reopened!")
                                st.rerun()
                        
                        with col_action4:
                            if st.button("🔗 Details", key=f"details_{task_id}"):
                                with st.expander(f"Task Details: {title}", expanded=True):
                                    st.write(f"**ID:** {task_id}")
                                    st.write(f"**Status:** {status}")
                                    st.write(f"**Assigned to:** {assigned_to}")
                                    st.write(f"**Due Date:** {due_date}")
                                    st.write(f"**Created:** {timestamp}")
                                    st.write(f"**Section:** {section}")
                                    if description:
                                        st.write(f"**Description:** {description}")
                        
                        st.markdown("---")
                
                else:
                    st.info("💭 No tasks yet. Create the first task for this section above!")
            
            # Section-level actions
            st.markdown("#### 🔧 Section Actions")
            col_section1, col_section2 = st.columns(2)
            
            with col_section1:
                if st.button("📋 Add to IC Memo", use_container_width=True):
                    st.info("This will be integrated with the IC Memo generator")
            
            with col_section2:
                if st.button("🚨 Report Red Flag", use_container_width=True):
                    st.switch_page("pages/Red_Flag_Tracker.py")

    # Team overview
    st.divider()
    st.markdown("### 👥 Team Overview")
    
    # Get all tasks for current CIM
    if st.session_state.current_cim_id:
        import sqlite3
        conn = sqlite3.connect('auctum.db')
        c = conn.cursor()
        c.execute("SELECT * FROM tasks WHERE cim_id = ?", (st.session_state.current_cim_id,))
        all_tasks = c.fetchall()
        conn.close()
        
        if all_tasks:
            # Team member statistics
            team_stats = {}
            for task in all_tasks:
                assigned_to = task[4]  # assigned_to column
                status = task[6]      # status column
                
                if assigned_to not in team_stats:
                    team_stats[assigned_to] = {"total": 0, "open": 0, "in_progress": 0, "completed": 0}
                
                team_stats[assigned_to]["total"] += 1
                team_stats[assigned_to][status] += 1
            
            # Display team stats
            cols = st.columns(min(len(team_stats), 4))
            for i, (member, stats) in enumerate(team_stats.items()):
                with cols[i % 4]:
                    st.metric(
                        f"👤 {member}",
                        f"{stats['total']} tasks",
                        f"{stats['open']} open, {stats['completed']} done"
                    )
        else:
            st.info("No tasks assigned yet. Start by creating tasks in the sections above.")

if __name__ == "__main__":
    main()
