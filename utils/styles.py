import streamlit as st


def apply_sidebar_styles():
    """
    Colour theme with enhanced readability and contrast
    """

    COLOURS = {
        "primary": "#1A3A8F",  # Deep navy blue — the dominant structural colour
        "secondary": "#6B35C8",  # Mid purple — the gradient midpoint
        "accent": "#00B4C8",  # Teal/cyan — the upward arrow highlight
        "dark": "#0D1F5C",  # Near-black navy — shadows and depth
        "light_purple": "#C8B8F0",  # Pale lavender — for backgrounds or subtle fills
        "background": "#F4F4F6",  # Off-white — clean background
        "white": "#FFFFFF",  # Pure white for maximum contrast
        "light_gray": "#E8E8F0",  # Light gray for borders
        "text_dark": "#1A1A2E",  # Dark text for main content
        "text_light": "#E8E8F0",  # Light text for dark backgrounds
        "shadow": "rgba(13, 31, 92, 0.15)",  # Shadow color
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
        max-width: 1200px !important;
    }}
    
    /* ============ HEADERS - Enhanced Visibility ============ */
    h1, h2, h3, h4, h5, h6 {{
        color: {COLOURS['primary']} !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em !important;
    }}
    
    h1 {{
        color: {COLOURS['primary']} !important;
        font-size: 2.5rem !important;
        border-bottom: 4px solid {COLOURS['secondary']};
        padding-bottom: 0.75rem;
        margin-bottom: 1.5rem !important;
        font-weight: 800 !important;
    }}
    
    h2 {{
        color: {COLOURS['primary']} !important;
        font-size: 1.8rem !important;
        margin-top: 1.5rem !important;
        font-weight: 700 !important;
    }}
    
    h3 {{
        color: {COLOURS['secondary']} !important;
        font-size: 1.3rem !important;
        font-weight: 600 !important;
    }}
    
    /* ============ SIDEBAR - ROBUST SELECTORS ============ */
    /* Primary method: data-testid attributes (most stable) */
    section[data-testid="stSidebar"] {{
        background: linear-gradient(180deg, #0D1F5C 0%, #1A3A8F 50%, #16213E 100%) !important;
    }}
    
    [data-testid="stSidebarContent"] {{
        background: linear-gradient(180deg, #0D1F5C 0%, #1A3A8F 50%, #16213E 100%) !important;
        padding: 1.5rem 1rem !important;
    }}
    
    /* Fallback: Target by role (accessibility standard) */
    section[role="complementary"] {{
        background: linear-gradient(180deg, #0D1F5C 0%, #1A3A8F 50%, #16213E 100%) !important;
    }}
    
    /* Fallback: Pattern matching for class names */
    section[class*="stSidebar"] {{
        background: linear-gradient(180deg, #0D1F5C 0%, #1A3A8F 50%, #16213E 100%) !important;
    }}
    
    /* ============ SIDEBAR TEXT - MAXIMUM VISIBILITY ============ */
    /* Target all text elements in sidebar with enhanced contrast */
    [data-testid="stSidebarContent"] {{
        color: {COLOURS['white']} !important;
    }}
    
    [data-testid="stSidebarContent"] .stMarkdown,
    [data-testid="stSidebarContent"] p,
    [data-testid="stSidebarContent"] label,
    [data-testid="stSidebarContent"] .stTextInput label,
    [data-testid="stSidebarContent"] .stSelectbox label,
    [data-testid="stSidebarContent"] .stDateInput label,
    [data-testid="stSidebarContent"] .stNumberInput label,
    [data-testid="stSidebarContent"] .stSlider label,
    [data-testid="stSidebarContent"] .stCheckbox label {{
        color: {COLOURS['white']} !important;
        font-weight: 500 !important;
        text-shadow: 0 1px 3px rgba(0, 0, 0, 0.4) !important;
    }}
    
    /* Sidebar headers - extra bright */
    [data-testid="stSidebarContent"] h1,
    [data-testid="stSidebarContent"] h2,
    [data-testid="stSidebarContent"] h3,
    [data-testid="stSidebarContent"] h4,
    [data-testid="stSidebarContent"] h5,
    [data-testid="stSidebarContent"] h6 {{
        color: {COLOURS['white']} !important;
        font-weight: 700 !important;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3) !important;
    }}
    
    /* Sidebar navigation items - enhanced contrast */
    [data-testid="stSidebarNav"] {{
        padding: 0.5rem 0 !important;
    }}
    
    [data-testid="stSidebarNav"] a {{
        color: {COLOURS['white']} !important;
        font-weight: 500 !important;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3) !important;
        padding: 0.5rem 0.75rem !important;
        border-radius: 6px !important;
        transition: all 0.2s ease !important;
    }}
    
    [data-testid="stSidebarNav"] a:hover {{
        color: {COLOURS['accent']} !important;
        background-color: rgba(0, 180, 200, 0.15) !important;
        text-shadow: 0 0 8px rgba(0, 180, 200, 0.3) !important;
    }}
    
    [data-testid="stSidebarNav"] .stSidebarNavSelected {{
        background: linear-gradient(135deg, {COLOURS['primary']}, {COLOURS['secondary']}) !important;
        border-radius: 6px !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3) !important;
    }}
    
    /* ============ SIDEBAR INPUT FIELDS ============ */
    [data-testid="stSidebarContent"] .stTextInput input,
    [data-testid="stSidebarContent"] .stSelectbox select,
    [data-testid="stSidebarContent"] .stDateInput input,
    [data-testid="stSidebarContent"] .stNumberInput input {{
        background-color: {COLOURS['white']} !important;
        color: {COLOURS['text_dark']} !important;
        border-radius: 8px !important;
        border: 2px solid {COLOURS['light_purple']} !important;
        padding: 0.6rem 0.8rem !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
    }}
    
    [data-testid="stSidebarContent"] .stTextInput input:focus,
    [data-testid="stSidebarContent"] .stSelectbox select:focus,
    [data-testid="stSidebarContent"] .stDateInput input:focus,
    [data-testid="stSidebarContent"] .stNumberInput input:focus {{
        border-color: {COLOURS['accent']} !important;
        box-shadow: 0 0 0 3px rgba(0, 180, 200, 0.3) !important;
        outline: none !important;
    }}
    
    /* Sidebar select dropdown options */
    [data-testid="stSidebarContent"] .stSelectbox option {{
        background-color: {COLOURS['white']} !important;
        color: {COLOURS['text_dark']} !important;
        padding: 0.5rem !important;
    }}
    
    /* Slider styling */
    [data-testid="stSidebarContent"] .stSlider {{
        padding: 0.5rem 0 !important;
    }}
    
    [data-testid="stSidebarContent"] .stSlider .stSliderValue {{
        color: {COLOURS['white']} !important;
        font-weight: 700 !important;
        background: rgba(0, 0, 0, 0.3) !important;
        padding: 0.15rem 0.6rem !important;
        border-radius: 4px !important;
    }}
    
    /* ============ SIDEBAR BUTTONS ============ */
    [data-testid="stSidebarContent"] .stButton > button {{
        background: linear-gradient(135deg, {COLOURS['primary']}, {COLOURS['secondary']}) !important;
        color: {COLOURS['white']} !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.7rem 1.4rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(26, 58, 143, 0.4) !important;
        width: 100% !important;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2) !important;
    }}
    
    [data-testid="stSidebarContent"] .stButton > button:hover {{
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 25px rgba(26, 58, 143, 0.6) !important;
        background: linear-gradient(135deg, {COLOURS['secondary']}, {COLOURS['accent']}) !important;
    }}
    
    [data-testid="stSidebarContent"] .stButton > button:active {{
        transform: translateY(0px) !important;
    }}
    
    [data-testid="stSidebarContent"] .stButton > button:disabled {{
        opacity: 0.5;
        background: {COLOURS['light_purple']} !important;
        color: {COLOURS['text_dark']} !important;
        transform: none !important;
        box-shadow: none !important;
    }}
    
    /* ============ COLLAPSED SIDEBAR TOGGLE ============ */
    [data-testid="collapsedControl"] {{
        background-color: {COLOURS['dark']} !important;
        border-radius: 0 8px 8px 0 !important;
        padding: 0.5rem !important;
        border: 2px solid {COLOURS['light_purple']} !important;
        border-left: none !important;
        transition: all 0.3s ease !important;
    }}
    
    [data-testid="collapsedControl"] svg {{
        fill: {COLOURS['white']} !important;
    }}
    
    [data-testid="collapsedControl"]:hover {{
        background-color: {COLOURS['primary']} !important;
        border-color: {COLOURS['accent']} !important;
        transform: translateX(4px) !important;
    }}
    
    /* ============ MAIN AREA BUTTONS ============ */
    .stButton > button {{
        background: linear-gradient(135deg, {COLOURS['primary']}, {COLOURS['secondary']}) !important;
        color: {COLOURS['white']} !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.7rem 1.4rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(26, 58, 143, 0.3) !important;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2) !important;
    }}
    
    .stButton > button:hover {{
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 25px rgba(26, 58, 143, 0.5) !important;
        background: linear-gradient(135deg, {COLOURS['secondary']}, {COLOURS['accent']}) !important;
    }}
    
    .stButton > button:active {{
        transform: translateY(0px) !important;
    }}
    
    .stButton > button:disabled {{
        opacity: 0.5;
        background: {COLOURS['light_purple']} !important;
        color: {COLOURS['text_dark']} !important;
        transform: none !important;
        box-shadow: none !important;
    }}
    
    /* ============ METRICS - Enhanced Visibility ============ */
    .stMetric {{
        background: linear-gradient(135deg, {COLOURS['white']} 0%, #F8F8FF 100%) !important;
        border-radius: 12px !important;
        padding: 1.25rem !important;
        box-shadow: 0 4px 20px {COLOURS['shadow']} !important;
        border-left: 4px solid {COLOURS['secondary']} !important;
        transition: all 0.3s ease !important;
    }}
    
    .stMetric:hover {{
        transform: translateY(-4px) !important;
        box-shadow: 0 8px 30px {COLOURS['shadow']} !important;
    }}
    
    .stMetric label {{
        color: {COLOURS['text_dark']} !important;
        font-weight: 700 !important;
        font-size: 0.9rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }}
    
    .stMetric .stMetricValue {{
        color: {COLOURS['primary']} !important;
        font-size: 2.2rem !important;
        font-weight: 800 !important;
        background: linear-gradient(135deg, {COLOURS['primary']}, {COLOURS['secondary']});
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }}
    
    .stMetric .stMetricDelta {{
        color: {COLOURS['accent']} !important;
        font-weight: 600 !important;
    }}
    
    /* ============ DATAFRAMES / TABLES ============ */
    .stDataFrame {{
        border-radius: 12px !important;
        overflow: hidden !important;
        box-shadow: 0 4px 20px {COLOURS['shadow']} !important;
        background: {COLOURS['white']} !important;
    }}
    
    .stDataFrame thead tr th {{
        background: linear-gradient(135deg, {COLOURS['primary']}, {COLOURS['secondary']}) !important;
        color: {COLOURS['white']} !important;
        font-weight: 700 !important;
        padding: 0.75rem 1rem !important;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2) !important;
    }}
    
    .stDataFrame tbody tr:hover {{
        background-color: {COLOURS['light_purple']} !important;
    }}
    
    .stDataFrame tbody td {{
        padding: 0.5rem 1rem !important;
        color: {COLOURS['text_dark']} !important;
        font-weight: 400 !important;
    }}
    
    .stDataFrame tbody tr:nth-child(even) {{
        background-color: #F8F8FF !important;
    }}
    
    /* ============ ALERTS / MESSAGES ============ */
    .stAlert {{
        border-radius: 12px !important;
        border-left: 5px solid {COLOURS['accent']} !important;
        box-shadow: 0 4px 15px {COLOURS['shadow']} !important;
        padding: 1rem !important;
    }}
    
    .stAlert .stAlertContent {{
        color: {COLOURS['text_dark']} !important;
        font-weight: 500 !important;
    }}
    
    .stAlert[data-baseweb="notification"] {{
        border-radius: 12px !important;
    }}
    
    /* Success messages */
    .stAlert[data-baseweb="notification"]:has(svg[data-testid="icon-check"]) {{
        border-left-color: #00C853 !important;
        background: #E8F5E9 !important;
    }}
    
    /* Warning messages */
    .stAlert[data-baseweb="notification"]:has(svg[data-testid="icon-alert"]) {{
        border-left-color: #FF9800 !important;
        background: #FFF3E0 !important;
    }}
    
    /* Error messages */
    .stAlert[data-baseweb="notification"]:has(svg[data-testid="icon-error"]) {{
        border-left-color: #F44336 !important;
        background: #FFEBEE !important;
    }}
    
    /* ============ EXPANDER ============ */
    .streamlit-expanderHeader {{
        background: linear-gradient(135deg, {COLOURS['light_purple']}, #E8E0F8) !important;
        color: {COLOURS['primary']} !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        font-size: 1.05rem !important;
        padding: 0.75rem 1.2rem !important;
        transition: all 0.3s ease !important;
        border: 1px solid rgba(107, 53, 200, 0.1) !important;
    }}
    
    .streamlit-expanderHeader:hover {{
        background: linear-gradient(135deg, #D8C8F5, #C8B8F0) !important;
        transform: translateX(4px) !important;
        box-shadow: 0 2px 10px {COLOURS['shadow']} !important;
    }}
    
    .streamlit-expanderContent {{
        padding: 1.2rem 0.8rem !important;
        border-left: 3px solid {COLOURS['light_purple']} !important;
        margin-left: 0.5rem !important;
        background: {COLOURS['white']} !important;
        border-radius: 0 0 8px 8px !important;
    }}
    
    /* ============ LINKS ============ */
    a {{
        color: {COLOURS['secondary']} !important;
        text-decoration: none !important;
        transition: all 0.2s ease !important;
        font-weight: 500 !important;
    }}
    
    a:hover {{
        color: {COLOURS['accent']} !important;
        text-decoration: underline !important;
    }}
    
    /* ============ DOWNLOAD BUTTON ============ */
    .stDownloadButton > button {{
        background: linear-gradient(135deg, {COLOURS['accent']}, {COLOURS['secondary']}) !important;
        color: {COLOURS['white']} !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        transition: all 0.3s ease !important;
        padding: 0.7rem 1.4rem !important;
        box-shadow: 0 4px 15px rgba(0, 180, 200, 0.3) !important;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2) !important;
    }}
    
    .stDownloadButton > button:hover {{
        background: linear-gradient(135deg, {COLOURS['secondary']}, {COLOURS['primary']}) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 25px rgba(107, 53, 200, 0.4) !important;
    }}
    
    /* ============ SIDEBAR FOOTER ============ */
    .sidebar-footer {{
        color: {COLOURS['light_purple']} !important;
        opacity: 0.9 !important;
        font-size: 0.8rem !important;
        text-align: center !important;
        padding-top: 1rem !important;
        border-top: 1px solid rgba(200, 184, 240, 0.3) !important;
        margin-top: 2rem !important;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3) !important;
    }}
    
    /* ============ RESPONSIVE DESIGN ============ */
    @media (max-width: 768px) {{
        section[data-testid="stSidebar"] {{
            width: 320px !important;
            min-width: 320px !important;
            max-width: 320px !important;
        }}
        
        [data-testid="stSidebarContent"] {{
            padding: 1rem !important;
        }}
        
        .stMetric .stMetricValue {{
            font-size: 1.6rem !important;
        }}
        
        h1 {{
            font-size: 2rem !important;
        }}
        
        h2 {{
            font-size: 1.5rem !important;
        }}
    }}
    
    @media (max-width: 480px) {{
        section[data-testid="stSidebar"] {{
            width: 280px !important;
            min-width: 280px !important;
            max-width: 280px !important;
        }}
    }}
    
    /* ============ DARK MODE COMPATIBILITY ============ */
    @media (prefers-color-scheme: dark) {{
        [data-testid="stSidebarContent"] {{
            background: linear-gradient(180deg, #0D1F5C 0%, #1A3A8F 50%, #16213E 100%) !important;
        }}
        
        .stMetric {{
            background: linear-gradient(135deg, #2D2D44 0%, #1A1A2E 100%) !important;
        }}
        
        .stMetric label {{
            color: {COLOURS['light_gray']} !important;
        }}
        
        .stMetric .stMetricValue {{
            background: linear-gradient(135deg, {COLOURS['light_purple']}, {COLOURS['accent']});
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        
        .stDataFrame {{
            background: #2D2D44 !important;
        }}
        
        .stDataFrame tbody td {{
            color: {COLOURS['light_gray']} !important;
        }}
        
        .stDataFrame tbody tr:nth-child(even) {{
            background-color: #3D3D5C !important;
        }}
        
        .stDataFrame tbody tr:hover {{
            background-color: #4D4D6C !important;
        }}
        
        .stAlert {{
            background-color: #2D2D44 !important;
        }}
        
        .stAlert .stAlertContent {{
            color: {COLOURS['light_gray']} !important;
        }}
        
        .streamlit-expanderHeader {{
            background: linear-gradient(135deg, #2D2D44, #3D3D5C) !important;
            color: {COLOURS['light_purple']} !important;
        }}
        
        .streamlit-expanderContent {{
            background: #2D2D44 !important;
        }}
        
        .streamlit-expanderHeader:hover {{
            background: linear-gradient(135deg, #3D3D5C, #4D4D6C) !important;
        }}
    }}
    
    /* ============ SCROLLBAR STYLING ============ */
    ::-webkit-scrollbar {{
        width: 8px !important;
        height: 8px !important;
    }}
    
    ::-webkit-scrollbar-track {{
        background: {COLOURS['light_gray']} !important;
        border-radius: 4px !important;
    }}
    
    ::-webkit-scrollbar-thumb {{
        background: linear-gradient(135deg, {COLOURS['primary']}, {COLOURS['secondary']}) !important;
        border-radius: 4px !important;
        transition: all 0.3s ease !important;
    }}
    
    ::-webkit-scrollbar-thumb:hover {{
        background: linear-gradient(135deg, {COLOURS['secondary']}, {COLOURS['accent']}) !important;
    }}
    
    /* ============ TOOLTIP ENHANCEMENTS ============ */
    .stTooltipContent {{
        background: {COLOURS['dark']} !important;
        color: {COLOURS['white']} !important;
        border-radius: 8px !important;
        padding: 0.5rem 1rem !important;
        font-weight: 500 !important;
    }}
</style>
""",
        unsafe_allow_html=True,
    )
