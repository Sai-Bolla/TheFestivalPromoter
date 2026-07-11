import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# Branding
SIDEBAR_LOGO = "images/eventintelligence-logo.png"
MAIN_ICON = "images/eventintelligence-logo.png"
st.logo(SIDEBAR_LOGO, icon_image=MAIN_ICON)
st.set_page_config(page_title="Branding", page_icon=SIDEBAR_LOGO, layout="wide")

def apply_sidebar_styles():
    """
    Colour theme
    """
    
    COLOURS = {
        "primary": "#1A3A8F",      # Deep navy blue — the dominant structural colour
        "secondary": "#6B35C8",    # Mid purple — the gradient midpoint
        "accent": "#00B4C8",       # Teal/cyan — the upward arrow highlight
        "dark": "#0D1F5C",         # Near-black navy — shadows and depth
        "light_purple": "#C8B8F0", # Pale lavender — for backgrounds or subtle fills
        "background": "#F4F4F6",   # Off-white — clean background
    }
    
    st.markdown(
        f"""
<style>
    /* ============ PAGE BACKGROUND ============ */
    .stApp {{
        background-color: {COLOURS['background']};
    }}
    
    /* ============ MAIN CONTAINER ============ */
    .main .block-container {{
        padding-top: 2rem;
        padding-bottom: 2rem;
    }}
    
    /* ============ HEADERS ============ */
    h1, h2, h3, h4, h5, h6 {{
        color: {COLOURS['primary']} !important;
    }}
    
    h1 {{
        border-bottom: 3px solid {COLOURS['secondary']};
        padding-bottom: 0.5rem;
    }}
    
    /* ============ SIDEBAR - ROBUST SELECTORS ============ */
    /* Primary method: data-testid attributes (most stable) */
    section[data-testid="stSidebar"] {{
        background-color: {COLOURS['dark']} !important;
    }}
    
    [data-testid="stSidebarContent"] {{
        background-color: {COLOURS['dark']} !important;
        padding: 1.5rem 1rem !important;
    }}
    
    /* Fallback: Target by role (accessibility standard) */
    section[role="complementary"] {{
        background-color: {COLOURS['dark']} !important;
    }}
    
    /* Fallback: Pattern matching for class names */
    section[class*="stSidebar"] {{
        background-color: {COLOURS['dark']} !important;
    }}
    
    /* ============ SIDEBAR TEXT ============ */
    /* Target all text elements in sidebar with multiple methods */
    [data-testid="stSidebarContent"] .stMarkdown,
    [data-testid="stSidebarContent"] p,
    [data-testid="stSidebarContent"] label,
    [data-testid="stSidebarContent"] .stTextInput label,
    [data-testid="stSidebarContent"] .stSelectbox label,
    [data-testid="stSidebarContent"] .stDateInput label,
    [data-testid="stSidebarContent"] .stNumberInput label {{
        color: {COLOURS['background']} !important;
    }}
    
    [data-testid="stSidebarContent"] h1,
    [data-testid="stSidebarContent"] h2,
    [data-testid="stSidebarContent"] h3,
    [data-testid="stSidebarContent"] h4,
    [data-testid="stSidebarContent"] h5,
    [data-testid="stSidebarContent"] h6 {{
        color: {COLOURS['light_purple']} !important;
    }}
    
    /* Sidebar navigation items */
    [data-testid="stSidebarNav"] {{
        padding: 0.5rem 0 !important;
    }}
    
    [data-testid="stSidebarNav"] a {{
        color: {COLOURS['background']} !important;
    }}
    
    [data-testid="stSidebarNav"] a:hover {{
        color: {COLOURS['accent']} !important;
        background-color: rgba(0, 180, 200, 0.1) !important;
        border-radius: 4px !important;
    }}
    
    [data-testid="stSidebarNav"] .stSidebarNavSelected {{
        background: linear-gradient(135deg, {COLOURS['primary']}, {COLOURS['secondary']}) !important;
        border-radius: 4px !important;
    }}
    
    /* ============ SIDEBAR INPUT FIELDS ============ */
    [data-testid="stSidebarContent"] .stTextInput input,
    [data-testid="stSidebarContent"] .stSelectbox select,
    [data-testid="stSidebarContent"] .stDateInput input,
    [data-testid="stSidebarContent"] .stNumberInput input {{
        background-color: {COLOURS['background']} !important;
        color: {COLOURS['dark']} !important;
        border-radius: 5px;
        border: 1px solid {COLOURS['light_purple']} !important;
    }}
    
    [data-testid="stSidebarContent"] .stTextInput input:focus,
    [data-testid="stSidebarContent"] .stSelectbox select:focus,
    [data-testid="stSidebarContent"] .stDateInput input:focus,
    [data-testid="stSidebarContent"] .stNumberInput input:focus {{
        border-color: {COLOURS['accent']} !important;
        box-shadow: 0 0 0 2px rgba(0, 180, 200, 0.2) !important;
    }}
    
    /* ============ SIDEBAR BUTTONS ============ */
    [data-testid="stSidebarContent"] .stButton > button {{
        background: linear-gradient(135deg, {COLOURS['primary']}, {COLOURS['secondary']}) !important;
        color: white !important;
        font-weight: bold !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.6rem 1.2rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 2px 8px rgba(26, 58, 143, 0.3);
        width: 100% !important;
    }}
    
    [data-testid="stSidebarContent"] .stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(26, 58, 143, 0.4);
        background: linear-gradient(135deg, {COLOURS['secondary']}, {COLOURS['accent']}) !important;
    }}
    
    [data-testid="stSidebarContent"] .stButton > button:disabled {{
        opacity: 0.6;
        background: {COLOURS['light_purple']} !important;
        color: {COLOURS['dark']} !important;
        transform: none !important;
    }}
    
    /* ============ COLLAPSED SIDEBAR TOGGLE ============ */
    [data-testid="collapsedControl"] {{
        background-color: {COLOURS['dark']} !important;
        border-radius: 0 8px 8px 0 !important;
        padding: 0.5rem !important;
        border: 1px solid {COLOURS['light_purple']} !important;
        border-left: none !important;
    }}
    
    [data-testid="collapsedControl"] svg {{
        fill: {COLOURS['background']} !important;
    }}
    
    [data-testid="collapsedControl"]:hover {{
        background-color: {COLOURS['primary']} !important;
    }}
    
    /* ============ MAIN AREA BUTTONS ============ */
    .stButton > button {{
        background: linear-gradient(135deg, {COLOURS['primary']}, {COLOURS['secondary']}) !important;
        color: white !important;
        font-weight: bold !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.6rem 1.2rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 2px 8px rgba(26, 58, 143, 0.3);
    }}
    
    .stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(26, 58, 143, 0.4);
        background: linear-gradient(135deg, {COLOURS['secondary']}, {COLOURS['accent']}) !important;
    }}
    
    .stButton > button:disabled {{
        opacity: 0.6;
        background: {COLOURS['light_purple']} !important;
        color: {COLOURS['dark']} !important;
        transform: none !important;
    }}
    
    /* ============ METRICS ============ */
    .stMetric {{
        background-color: white;
        border-radius: 10px;
        padding: 1rem;
        box-shadow: 0 2px 8px rgba(13, 31, 92, 0.08);
        border-left: 4px solid {COLOURS['secondary']};
        transition: all 0.3s ease;
    }}
    
    .stMetric:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 16px rgba(13, 31, 92, 0.12);
    }}
    
    .stMetric label {{
        color: {COLOURS['dark']} !important;
        font-weight: 600 !important;
    }}
    
    .stMetric .stMetricValue {{
        color: {COLOURS['primary']} !important;
        font-size: 2rem !important;
        font-weight: bold !important;
    }}
    
    /* ============ DATAFRAMES / TABLES ============ */
    .stDataFrame {{
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(13, 31, 92, 0.08);
    }}
    
    .stDataFrame thead tr th {{
        background: linear-gradient(135deg, {COLOURS['primary']}, {COLOURS['secondary']}) !important;
        color: white !important;
        padding: 0.75rem !important;
    }}
    
    .stDataFrame tbody tr:hover {{
        background-color: {COLOURS['light_purple']} !important;
    }}
    
    .stDataFrame tbody td {{
        padding: 0.5rem !important;
    }}
    
    /* ============ ALERTS / MESSAGES ============ */
    .stAlert {{
        border-radius: 10px !important;
        border-left: 4px solid {COLOURS['accent']} !important;
    }}
    
    .stAlert[data-baseweb="notification"] {{
        border-radius: 10px !important;
    }}
    
    /* Success messages */
    .stAlert[data-baseweb="notification"]:has(svg[data-testid="icon-check"]) {{
        border-left-color: #00C853 !important;
    }}
    
    /* ============ EXPANDER ============ */
    .streamlit-expanderHeader {{
        background-color: {COLOURS['light_purple']} !important;
        color: {COLOURS['primary']} !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        padding: 0.75rem 1rem !important;
        transition: all 0.3s ease !important;
    }}
    
    .streamlit-expanderHeader:hover {{
        background-color: #D8C8F5 !important;
        transform: translateX(4px);
    }}
    
    .streamlit-expanderContent {{
        padding: 1rem 0.5rem !important;
        border-left: 2px solid {COLOURS['light_purple']} !important;
        margin-left: 0.5rem !important;
    }}
    
    /* ============ LINKS ============ */
    a {{
        color: {COLOURS['secondary']} !important;
        text-decoration: none !important;
        transition: all 0.2s ease !important;
    }}
    
    a:hover {{
        color: {COLOURS['accent']} !important;
        text-decoration: underline !important;
    }}
    
    /* ============ DOWNLOAD BUTTON ============ */
    .stDownloadButton > button {{
        background: linear-gradient(135deg, {COLOURS['accent']}, {COLOURS['secondary']}) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        transition: all 0.3s ease !important;
        padding: 0.6rem 1.2rem !important;
    }}
    
    .stDownloadButton > button:hover {{
        background: linear-gradient(135deg, {COLOURS['secondary']}, {COLOURS['primary']}) !important;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(107, 53, 200, 0.3);
    }}
    
    /* ============ SIDEBAR FOOTER ============ */
    .sidebar-footer {{
        color: {COLOURS['light_purple']} !important;
        opacity: 0.8;
        font-size: 0.8rem;
        text-align: center;
        padding-top: 1rem;
        border-top: 1px solid {COLOURS['light_purple']};
        margin-top: 2rem;
    }}
    
    /* ============ RESPONSIVE DESIGN ============ */
    @media (max-width: 768px) {{
        section[data-testid="stSidebar"] {{
            width: 300px !important;
            min-width: 300px !important;
            max-width: 300px !important;
        }}
        
        [data-testid="stSidebarContent"] {{
            padding: 1rem !important;
        }}
        
        .stMetric .stMetricValue {{
            font-size: 1.5rem !important;
        }}
    }}
    
    /* ============ DARK MODE COMPATIBILITY ============ */
    @media (prefers-color-scheme: dark) {{
        [data-testid="stSidebarContent"] {{
            background-color: #1a1a2e !important;
        }}
        
        .stMetric {{
            background-color: #2d2d44 !important;
        }}
        
        .stMetric label {{
            color: {COLOURS['background']} !important;
        }}
        
        .stMetric .stMetricValue {{
            color: {COLOURS['light_purple']} !important;
        }}
        
        .event-card {{
            background-color: #2d2d44 !important;
        }}
        
        .event-card h3 {{
            color: {COLOURS['light_purple']} !important;
        }}
        
        .event-card .event-detail {{
            color: {COLOURS['background']} !important;
        }}
        
        .stDataFrame {{
            background-color: #2d2d44 !important;
        }}
        
        .stDataFrame tbody td {{
            color: {COLOURS['background']} !important;
        }}
        
        .stAlert {{
            background-color: #2d2d44 !important;
        }}
        
        .streamlit-expanderHeader {{
            background-color: #2d2d44 !important;
            color: {COLOURS['light_purple']} !important;
        }}
    }}
</style>
""",
        unsafe_allow_html=True,
    )
    
apply_sidebar_styles()