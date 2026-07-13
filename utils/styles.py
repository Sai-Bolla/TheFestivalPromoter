import streamlit as st


def apply_sidebar_styles():
    """
    Brand colour theme - simplified with visible main area fonts
    """
    
    # Brand colours
    COLOURS = {
        "primary": "#1A3A8F",    # Deep navy blue
        "secondary": "#6B35C8",  # Mid purple
        "accent": "#00B4C8",     # Teal/cyan
        "dark": "#0D1F5C",       # Near-black navy
        "light": "#C8B8F0",      # Pale lavender
        "neutral": "#F4F4F6",    # Off-white
        "white": "#FFFFFF",
        "text_dark": "#1A1A2E",
    }

    st.markdown(
        f"""
<style>
    /* ============ PAGE BACKGROUND ============ */
    .stApp {{
        background-color: {COLOURS['dark']};
    }}
    
    /* ============ MAIN CONTAINER ============ */
    .main .block-container {{
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px !important;
    }}
    
    /* ============ MAIN AREA - ALL TEXT VISIBLE ============ */
    /* Force all main area text to be dark and visible */
    .main * {{
        color: {COLOURS['text_dark']} !important;
    }}
    
    .main .stMarkdown,
    .main .stMarkdown p,
    .main .stMarkdown div,
    .main .stMarkdown span,
    .main p,
    .main div,
    .main span {{
        color: {COLOURS['text_dark']} !important;
        font-weight: 400 !important;
    }}
    
    /* ============ HEADERS ============ */
    h1, h2, h3, h4, h5, h6 {{
        color: {COLOURS['primary']} !important;
        font-weight: 700 !important;
    }}
    
    h1 {{
        border-bottom: 3px solid {COLOURS['secondary']};
        padding-bottom: 0.5rem;
        margin-bottom: 1.5rem !important;
    }}
    
    /* ============ SIDEBAR ============ */
    section[data-testid="stSidebar"],
    [data-testid="stSidebarContent"],
    section[role="complementary"] {{
        background-color: {COLOURS['dark']} !important;
    }}
    
    /* Sidebar text - all white */
    [data-testid="stSidebarContent"] *,
    [data-testid="stSidebarContent"] label,
    [data-testid="stSidebarContent"] .stMarkdown,
    [data-testid="stSidebarContent"] p {{
        color: {COLOURS['white']} !important;
    }}
    
    /* Sidebar headers - light purple */
    [data-testid="stSidebarContent"] h1,
    [data-testid="stSidebarContent"] h2,
    [data-testid="stSidebarContent"] h3 {{
        color: {COLOURS['light']} !important;
    }}
    
    /* Sidebar inputs - white background */
    [data-testid="stSidebarContent"] input,
    [data-testid="stSidebarContent"] select {{
        background-color: {COLOURS['white']} !important;
        color: {COLOURS['text_dark']} !important;
        border-radius: 5px !important;
        border: 1px solid {COLOURS['light']} !important;
    }}
    
    /* Sidebar buttons */
    [data-testid="stSidebarContent"] .stButton > button,
    .main .stButton > button,
    .stDownloadButton > button {{
        background: linear-gradient(135deg, {COLOURS['primary']}, {COLOURS['secondary']}) !important;
        color: {COLOURS['white']} !important;
        font-weight: 700 !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.6rem 1.2rem !important;
        transition: all 0.3s ease !important;
        width: 100% !important;
    }}
    
    [data-testid="stSidebarContent"] .stButton > button:hover,
    .main .stButton > button:hover,
    .stDownloadButton > button:hover {{
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 12px rgba(26, 58, 143, 0.4) !important;
        background: linear-gradient(135deg, {COLOURS['secondary']}, {COLOURS['accent']}) !important;
    }}
    
    /* ============ METRICS ============ */
    [data-testid="stMetric"] {{
        background-color: {COLOURS['white']} !important;
        border-radius: 10px !important;
        padding: 1rem !important;
        box-shadow: 0 2px 8px rgba(13, 31, 92, 0.08) !important;
        border-left: 4px solid {COLOURS['secondary']} !important;
    }}
    
    [data-testid="stMetric"] label {{
        color: {COLOURS['text_dark']} !important;
        font-weight: 600 !important;
    }}
    
    [data-testid="stMetric"] .stMetricValue {{
        color: {COLOURS['primary']} !important;
        font-size: 2rem !important;
        font-weight: 700 !important;
    }}
    
    /* ============ DATA TABLES ============ */
    .stDataFrame {{
        border-radius: 10px !important;
        overflow: hidden !important;
        box-shadow: 0 2px 8px rgba(13, 31, 92, 0.08) !important;
    }}
    
    .stDataFrame thead tr th {{
        background: linear-gradient(135deg, {COLOURS['primary']}, {COLOURS['secondary']}) !important;
        color: {COLOURS['white']} !important;
        padding: 0.75rem !important;
    }}
    
    .stDataFrame tbody td {{
        color: {COLOURS['text_dark']} !important;
    }}
    
    .stDataFrame tbody tr:hover {{
        background-color: {COLOURS['light']} !important;
    }}
    
    /* ============ EXPANDER ============ */
    .streamlit-expanderHeader {{
        background-color: {COLOURS['light']} !important;
        color: {COLOURS['primary']} !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        padding: 0.75rem 1rem !important;
    }}
    
    .streamlit-expanderHeader:hover {{
        background-color: #D8C8F5 !important;
    }}
    
    /* ============ ALERTS ============ */
    .stAlert {{
        border-radius: 10px !important;
        border-left: 4px solid {COLOURS['accent']} !important;
        background-color: {COLOURS['white']} !important;
    }}
    
    .stAlert .stAlertContent {{
        color: {COLOURS['text_dark']} !important;
    }}
    
    /* ============ SIDEBAR NAVIGATION ============ */
    [data-testid="stSidebarNav"] a {{
        color: {COLOURS['white']} !important;
        padding: 0.5rem 0.75rem !important;
        border-radius: 6px !important;
        transition: all 0.2s ease !important;
    }}
    
    [data-testid="stSidebarNav"] a:hover {{
        color: {COLOURS['accent']} !important;
        background-color: rgba(0, 180, 200, 0.1) !important;
    }}
    
    /* ============ SIDEBAR CAPTION ============ */
    [data-testid="stSidebarContent"] .stCaption {{
        color: {COLOURS['light']} !important;
        opacity: 0.8 !important;
    }}
    
    /* ============ COLLAPSED SIDEBAR TOGGLE ============ */
    [data-testid="collapsedControl"] {{
        background-color: {COLOURS['dark']} !important;
        border-radius: 0 8px 8px 0 !important;
        padding: 0.5rem !important;
        border: 1px solid {COLOURS['light']} !important;
        border-left: none !important;
    }}
    
    [data-testid="collapsedControl"] svg {{
        fill: {COLOURS['white']} !important;
    }}
    
    [data-testid="collapsedControl"]:hover {{
        background-color: {COLOURS['primary']} !important;
    }}
    
    /* ============ RESPONSIVE ============ */
    @media (max-width: 768px) {{
        section[data-testid="stSidebar"] {{
            width: 300px !important;
            min-width: 300px !important;
        }}
        
        [data-testid="stMetric"] .stMetricValue {{
            font-size: 1.5rem !important;
        }}
    }}
</style>
""",
        unsafe_allow_html=True,
    )