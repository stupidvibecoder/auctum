import streamlit as st

def apply_custom_css():
    """Apply custom CSS styling to the app"""
    st.markdown("""
    <style>
        /* Hide Streamlit branding */
        .stApp > header {
            background-color: transparent;
        }
        
        .stApp > header [data-testid="stHeader"] {
            display: none;
        }
        
        /* Dark theme background */
        .stApp {
            background: linear-gradient(135deg, #0f1419 0%, #1a1f2e 50%, #2d3748 100%);
            color: #ffffff;
        }
        
        /* Sticky navigation tabs */
        .sticky-tabs {
            position: sticky;
            top: 0;
            z-index: 999;
            background: rgba(15, 20, 25, 0.95);
            padding: 0.5rem 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            margin-bottom: 1rem;
        }
        
        /* Floating particles */
        .particle {
            position: fixed;
            border-radius: 50%;
            background: rgba(99, 102, 241, 0.4);
            animation: float 6s ease-in-out infinite;
            pointer-events: none;
            z-index: 0;
        }
        
        .particle:nth-child(odd) {
            background: rgba(139, 92, 246, 0.3);
            animation-delay: -2s;
        }
        
        .particle:nth-child(3n) {
            background: rgba(59, 130, 246, 0.3);
            animation-delay: -4s;
        }
        
        @keyframes float {
            0%, 100% { 
                transform: translateY(0px) translateX(0px) rotate(0deg); 
                opacity: 0.4;
            }
            33% { 
                transform: translateY(-30px) translateX(20px) rotate(120deg); 
                opacity: 0.8;
            }
            66% { 
                transform: translateY(20px) translateX(-20px) rotate(240deg); 
                opacity: 0.6;
            }
        }
        
        /* Task status styling */
        .task-card {
            background: rgba(30, 41, 59, 0.8);
            border-radius: 12px;
            padding: 1rem;
            margin: 0.5rem 0;
            border-left: 4px solid;
            transition: all 0.2s;
        }
        
        .task-open {
            border-left-color: #ef4444;
        }
        
        .task-in-progress {
            border-left-color: #f59e0b;
        }
        
        .task-complete {
            border-left-color: #10b981;
            opacity: 0.7;
        }
        
        .red-flag {
            background: rgba(239, 68, 68, 0.1);
            border-left: 4px solid #ef4444;
            padding: 1rem;
            margin: 0.5rem 0;
            border-radius: 0 8px 8px 0;
        }
        
        .compliance-badge {
            background: rgba(34, 197, 94, 0.1);
            border: 1px solid rgba(34, 197, 94, 0.3);
            border-radius: 8px;
            padding: 0.5rem;
            color: #22c55e;
            font-weight: bold;
        }
        
        .sync-status {
            display: inline-block;
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
            font-size: 0.8rem;
            font-weight: bold;
        }
        
        .sync-success { background: rgba(34, 197, 94, 0.2); color: #22c55e; }
        .sync-pending { background: rgba(245, 158, 11, 0.2); color: #f59e0b; }
        .sync-error { background: rgba(239, 68, 68, 0.2); color: #ef4444; }
        
        /* User avatar styling */
        .user-avatar {
            display: inline-block;
            width: 32px;
            height: 32px;
            border-radius: 50%;
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
            color: white;
            text-align: center;
            line-height: 32px;
            font-weight: bold;
            font-size: 0.8rem;
            margin-right: 0.5rem;
        }
        
        /* Main title styling */
        .main-title {
            font-size: 4rem;
            font-weight: 700;
            text-align: center;
            background: linear-gradient(135deg, #ffffff 0%, #e2e8f0 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 1rem;
            letter-spacing: -2px;
        }
        
        /* Content styling */
        .main .block-container {
            background: rgba(15, 20, 25, 0.6);
            border-radius: 16px;
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 2rem;
            margin-top: 1rem;
            position: relative;
            z-index: 1;
        }
        
        /* Cards and other styling */
        .welcome-card {
            background: rgba(30, 41, 59, 0.8);
            border-radius: 16px;
            padding: 2rem;
            border: 1px solid rgba(255, 255, 255, 0.1);
            color: #ffffff;
        }
        
        .feature-item {
            background: rgba(99, 102, 241, 0.1);
            border-left: 4px solid #6366f1;
            padding: 1rem;
            margin: 1rem 0;
            border-radius: 0 8px 8px 0;
            color: #e2e8f0;
        }
        
        /* Privacy note */
        .privacy-note {
            background: rgba(16, 185, 129, 0.1);
            border: 1px solid rgba(16, 185, 129, 0.3);
            border-radius: 12px;
            padding: 1rem;
            margin: 1rem 0;
            backdrop-filter: blur(10px);
            color: #ffffff;
        }
        
        /* Buttons */
        .stButton > button {
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 0.75rem 1.5rem;
            font-weight: 600;
            transition: all 0.2s;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(99, 102, 241, 0.4);
        }
        
        /* Text colors */
        .stMarkdown, .stText, h1, h2, h3, h4, h5, h6, p, div {
            color: #ffffff !important;
        }
        
        /* Input fields */
        .stTextInput > div > div > input, .stTextArea > div > div > textarea {
            background: rgba(30, 41, 59, 0.8);
            border: 1px solid rgba(255, 255, 255, 0.1);
            color: #ffffff;
        }
        
        .stSelectbox > div > div > select {
            background: rgba(30, 41, 59, 0.8);
            border: 1px solid rgba(255, 255, 255, 0.1);
            color: #ffffff;
        }
        
        /* Chart styling */
        .stPlotlyChart {
            background: rgba(30, 41, 59, 0.8);
            border-radius: 12px;
            padding: 1rem;
        }
    </style>

    <!-- Add floating particles -->
    <div class="particle" style="left: 10%; top: 20%; width: 8px; height: 8px; animation-delay: 0s;"></div>
    <div class="particle" style="left: 80%; top: 80%; width: 6px; height: 6px; animation-delay: 2s;"></div>
    <div class="particle" style="left: 60%; top: 30%; width: 10px; height: 10px; animation-delay: 4s;"></div>
    <div class="particle" style="left: 20%; top: 70%; width: 7px; height: 7px; animation-delay: 1s;"></div>
    <div class="particle" style="left: 90%; top: 10%; width: 5px; height: 5px; animation-delay: 3s;"></div>
    <div class="particle" style="left: 40%; top: 50%; width: 9px; height: 9px; animation-delay: 5s;"></div>
    <div class="particle" style="left: 70%; top: 60%; width: 8px; height: 8px; animation-delay: 1.5s;"></div>
    <div class="particle" style="left: 30%; top: 90%; width: 6px; height: 6px; animation-delay: 3.5s;"></div>
    """, unsafe_allow_html=True)
