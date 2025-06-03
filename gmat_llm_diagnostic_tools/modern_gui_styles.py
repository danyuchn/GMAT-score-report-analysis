#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modern GUI Styles Module
現代化 GUI 樣式模組

Provides modern day/night theme system with light and dark modes
提供現代化日夜主題系統，支援明亮和暗黑模式
"""

import streamlit as st

def get_theme_css(is_dark_mode: bool = False):
    """Generate CSS for light or dark theme"""
    
    if is_dark_mode:
        # Night Mode: Black background, white text
        theme_vars = """
        :root {
            /* Dark Theme Colors */
            --bg-primary: #000000;
            --bg-secondary: #1a1a1a;
            --bg-tertiary: #2a2a2a;
            --text-primary: #ffffff;
            --text-secondary: #e0e0e0;
            --text-muted: #b0b0b0;
            --border-color: #404040;
            --border-light: #303030;
            --accent-color: #4a90e2;
            --accent-hover: #5ba0f2;
            --success-color: #28a745;
            --warning-color: #ffc107;
            --error-color: #dc3545;
            --info-color: #17a2b8;
            --shadow-color: rgba(0, 0, 0, 0.5);
            --card-bg: rgba(26, 26, 26, 0.95);
            --card-bg-hover: rgba(42, 42, 42, 0.95);
            --input-bg: #2a2a2a;
            --input-border: #404040;
            --input-focus: #4a90e2;
        }
        """
    else:
        # Day Mode: White background, black text
        theme_vars = """
        :root {
            /* Light Theme Colors */
            --bg-primary: #ffffff;
            --bg-secondary: #f8f9fa;
            --bg-tertiary: #e9ecef;
            --text-primary: #000000;
            --text-secondary: #212529;
            --text-muted: #6c757d;
            --border-color: #dee2e6;
            --border-light: #f1f3f4;
            --accent-color: #007bff;
            --accent-hover: #0056b3;
            --success-color: #28a745;
            --warning-color: #ffc107;
            --error-color: #dc3545;
            --info-color: #17a2b8;
            --shadow-color: rgba(0, 0, 0, 0.1);
            --card-bg: rgba(255, 255, 255, 0.95);
            --card-bg-hover: rgba(248, 249, 250, 0.95);
            --input-bg: #ffffff;
            --input-border: #ced4da;
            --input-focus: #007bff;
        }
        """
    
    return f"""
    <style>
        /* Import Google Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&display=swap');
        
        {theme_vars}
        
        /* Global reset and base styles */
        html, body, [class*="css"] {{
            font-family: 'Inter', sans-serif;
            color: var(--text-primary);
        }}
        
        /* Hide Streamlit default elements */
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        header {{visibility: hidden;}}
        
        /* Main container with theme-aware background */
        .stApp {{
            background: var(--bg-primary);
            min-height: 100vh;
            transition: all 0.3s ease;
        }}
        
        .main .block-container {{
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 1200px;
            background: var(--bg-primary);
        }}
        
        /* Modern header styling */
        .modern-header {{
            background: var(--card-bg);
            backdrop-filter: blur(10px);
            border-radius: 1rem;
            padding: 2.5rem 2rem;
            margin-bottom: 2rem;
            text-align: center;
            box-shadow: 0 4px 6px var(--shadow-color);
            border: 1px solid var(--border-color);
            transition: all 0.3s ease;
        }}
        
        .modern-header h1 {{
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--accent-color);
            margin-bottom: 0.5rem;
            line-height: 1.2;
        }}
        
        .modern-header p {{
            font-size: 1.125rem;
            color: var(--text-muted);
            font-weight: 400;
            margin: 0;
        }}
        
        /* Section headers */
        .section-header {{
            background: var(--card-bg);
            backdrop-filter: blur(10px);
            border-radius: 0.75rem;
            padding: 1.5rem 2rem;
            margin: 1.5rem 0;
            border-left: 4px solid var(--accent-color);
            box-shadow: 0 2px 4px var(--shadow-color);
            border: 1px solid var(--border-color);
            transition: all 0.3s ease;
        }}
        
        .section-header h2 {{
            font-size: 1.5rem;
            font-weight: 600;
            color: var(--text-primary);
            margin: 0;
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }}
        
        /* Card components */
        .modern-card {{
            background: var(--card-bg);
            backdrop-filter: blur(10px);
            border-radius: 1rem;
            padding: 2rem;
            margin: 1rem 0;
            box-shadow: 0 4px 6px var(--shadow-color);
            border: 1px solid var(--border-color);
            transition: all 0.3s ease;
        }}
        
        .modern-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 15px var(--shadow-color);
            background: var(--card-bg-hover);
        }}
        
        .modern-card-compact {{
            background: var(--card-bg);
            backdrop-filter: blur(10px);
            border-radius: 0.75rem;
            padding: 1.5rem;
            margin: 0.75rem 0;
            box-shadow: 0 2px 4px var(--shadow-color);
            border: 1px solid var(--border-color);
            transition: all 0.3s ease;
        }}
        
        /* Status cards */
        .status-card {{
            border-radius: 0.75rem;
            padding: 1.5rem;
            margin: 1rem 0;
            box-shadow: 0 2px 4px var(--shadow-color);
            backdrop-filter: blur(10px);
            border: 1px solid var(--border-color);
            transition: all 0.3s ease;
        }}
        
        .status-success {{
            background: var(--card-bg);
            border-left: 4px solid var(--success-color);
            color: var(--text-primary);
        }}
        
        .status-warning {{
            background: var(--card-bg);
            border-left: 4px solid var(--warning-color);
            color: var(--text-primary);
        }}
        
        .status-error {{
            background: var(--card-bg);
            border-left: 4px solid var(--error-color);
            color: var(--text-primary);
        }}
        
        .status-info {{
            background: var(--card-bg);
            border-left: 4px solid var(--info-color);
            color: var(--text-primary);
        }}
        
        /* Metric cards */
        .metric-card {{
            background: var(--card-bg);
            backdrop-filter: blur(10px);
            border-radius: 0.75rem;
            padding: 1.5rem;
            text-align: center;
            box-shadow: 0 2px 4px var(--shadow-color);
            border: 1px solid var(--border-color);
            transition: all 0.3s ease;
        }}
        
        .metric-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 8px var(--shadow-color);
            background: var(--card-bg-hover);
        }}
        
        .metric-value {{
            font-size: 2rem;
            font-weight: 700;
            color: var(--accent-color);
            margin-bottom: 0.5rem;
        }}
        
        .metric-label {{
            font-size: 0.875rem;
            font-weight: 500;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        
        /* Sidebar styling */
        .css-1d391kg, .css-1cypcdb {{
            background: var(--bg-secondary);
            color: var(--text-primary);
        }}
        
        /* Tabs styling */
        .stTabs [data-baseweb="tab-list"] {{
            background: var(--card-bg);
            backdrop-filter: blur(10px);
            border-radius: 0.75rem;
            padding: 0.5rem;
            box-shadow: 0 2px 4px var(--shadow-color);
            gap: 0.5rem;
            border: 1px solid var(--border-color);
        }}
        
        .stTabs [data-baseweb="tab"] {{
            background: transparent;
            border-radius: 0.5rem;
            padding: 0.75rem 1.5rem;
            font-weight: 500;
            transition: all 0.3s ease;
            border: none;
            color: var(--text-secondary);
        }}
        
        .stTabs [aria-selected="true"] {{
            background: var(--accent-color);
            color: white;
            box-shadow: 0 2px 4px var(--shadow-color);
        }}
        
        .stTabs [data-baseweb="tab"]:hover {{
            background: var(--bg-tertiary);
            color: var(--accent-color);
        }}
        
        /* Button styling */
        .stButton > button {{
            background: var(--accent-color);
            color: white;
            border: none;
            border-radius: 0.5rem;
            padding: 0.75rem 2rem;
            font-weight: 500;
            font-size: 1rem;
            box-shadow: 0 2px 4px var(--shadow-color);
            transition: all 0.3s ease;
        }}
        
        .stButton > button:hover {{
            transform: translateY(-1px);
            box-shadow: 0 4px 8px var(--shadow-color);
            background: var(--accent-hover);
        }}
        
        .stButton > button:active {{
            transform: translateY(0);
        }}
        
        /* Download button styling */
        .stDownloadButton > button {{
            background: var(--success-color);
            color: white;
            border: none;
            border-radius: 0.5rem;
            padding: 0.75rem 1.5rem;
            font-weight: 500;
            box-shadow: 0 2px 4px var(--shadow-color);
            transition: all 0.3s ease;
        }}
        
        .stDownloadButton > button:hover {{
            transform: translateY(-1px);
            box-shadow: 0 4px 8px var(--shadow-color);
        }}
        
        /* Input styling */
        .stSelectbox > div > div,
        .stNumberInput > div > div > input,
        .stTextInput > div > div > input,
        .stDateInput > div > div > input {{
            background: var(--input-bg);
            border: 1px solid var(--input-border);
            border-radius: 0.5rem;
            box-shadow: 0 1px 2px var(--shadow-color);
            transition: all 0.3s ease;
            color: var(--text-primary);
        }}
        
        .stSelectbox > div > div:focus-within,
        .stNumberInput > div > div > input:focus,
        .stTextInput > div > div > input:focus,
        .stDateInput > div > div > input:focus {{
            border-color: var(--input-focus);
            box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.1);
        }}
        
        /* Slider styling */
        .stSlider > div > div > div > div {{
            background: var(--accent-color);
        }}
        
        /* Checkbox styling */
        .stCheckbox > label > div {{
            border-radius: 0.25rem;
            border-color: var(--input-border);
        }}
        
        /* Expander styling */
        .streamlit-expanderHeader {{
            background: var(--card-bg);
            backdrop-filter: blur(10px);
            border-radius: 0.5rem;
            border: 1px solid var(--border-color);
            font-weight: 500;
            color: var(--text-primary);
        }}
        
        .streamlit-expanderContent {{
            background: var(--card-bg);
            backdrop-filter: blur(10px);
            border-radius: 0 0 0.5rem 0.5rem;
            border: 1px solid var(--border-color);
            border-top: none;
        }}
        
        /* DataFrame styling */
        .stDataFrame {{
            background: var(--card-bg);
            backdrop-filter: blur(10px);
            border-radius: 0.5rem;
            box-shadow: 0 2px 4px var(--shadow-color);
            overflow: hidden;
            border: 1px solid var(--border-color);
        }}
        
        /* Code blocks */
        .stCodeBlock {{
            background: var(--bg-tertiary);
            backdrop-filter: blur(10px);
            border-radius: 0.5rem;
            border: 1px solid var(--border-color);
            font-family: 'JetBrains Mono', monospace;
            color: var(--text-primary);
        }}
        
        /* Plotly charts */
        .js-plotly-plot {{
            border-radius: 0.75rem;
            box-shadow: 0 4px 6px var(--shadow-color);
            overflow: hidden;
        }}
        
        /* Text color overrides for better theme support */
        .stMarkdown, .stText, p, span, div {{
            color: var(--text-primary) !important;
        }}
        
        h1, h2, h3, h4, h5, h6 {{
            color: var(--text-primary) !important;
        }}
        
        /* Theme toggle button styling */
        .theme-toggle {{
            position: fixed;
            top: 1rem;
            right: 1rem;
            z-index: 1000;
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 50%;
            width: 3rem;
            height: 3rem;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            box-shadow: 0 2px 4px var(--shadow-color);
            transition: all 0.3s ease;
        }}
        
        .theme-toggle:hover {{
            transform: scale(1.1);
            box-shadow: 0 4px 8px var(--shadow-color);
        }}
        
        /* Custom spacing utilities */
        .mt-4 {{ margin-top: 1rem; }}
        .mb-4 {{ margin-bottom: 1rem; }}
        .py-4 {{ padding-top: 1rem; padding-bottom: 1rem; }}
        .px-4 {{ padding-left: 1rem; padding-right: 1rem; }}
        
        /* Animation utilities */
        .fade-in {{
            animation: fadeIn 0.5s ease-in;
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        .slide-up {{
            animation: slideUp 0.3s ease-out;
        }}
        
        @keyframes slideUp {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        /* Progress indicator */
        .progress-indicator {{
            background: var(--accent-color);
            height: 4px;
            border-radius: 2px;
            transition: width 0.3s ease;
        }}
        
        /* Responsive design */
        @media (max-width: 768px) {{
            .modern-header h1 {{
                font-size: 2rem;
            }}
            
            .modern-header {{
                padding: 2rem 1.5rem;
            }}
            
            .modern-card {{
                padding: 1.5rem;
            }}
            
            .section-header {{
                padding: 1rem 1.5rem;
            }}
            
            .theme-toggle {{
                width: 2.5rem;
                height: 2.5rem;
            }}
        }}
        
        /* Smooth transitions for all interactive elements */
        * {{
            transition: color 0.3s ease, background-color 0.3s ease, border-color 0.3s ease;
        }}
        
    </style>
    """

def apply_modern_css(is_dark_mode: bool = False):
    """Apply modern CSS styling with theme support"""
    css = get_theme_css(is_dark_mode)
    st.markdown(css, unsafe_allow_html=True)

def create_theme_toggle():
    """Create a theme toggle button"""
    
    # Initialize theme state
    if 'dark_mode' not in st.session_state:
        st.session_state.dark_mode = False
    
    # Create columns for layout
    col1, col2, col3 = st.columns([6, 1, 1])
    
    with col3:
        # Theme toggle button
        theme_icon = "🌙" if not st.session_state.dark_mode else "☀️"
        theme_label = "夜間模式" if not st.session_state.dark_mode else "日間模式"
        
        if st.button(f"{theme_icon} {theme_label}", key="theme_toggle"):
            st.session_state.dark_mode = not st.session_state.dark_mode
            st.rerun()
    
    return st.session_state.dark_mode

def create_modern_header(title: str, subtitle: str = "", icon: str = "📚"):
    """Create a modern header component"""
    st.markdown(f"""
    <div class="modern-header fade-in">
        <h1>{icon} {title}</h1>
        {f'<p>{subtitle}</p>' if subtitle else ''}
    </div>
    """, unsafe_allow_html=True)

def create_section_header(title: str, icon: str = ""):
    """Create a modern section header"""
    st.markdown(f"""
    <div class="section-header slide-up">
        <h2>{icon} {title}</h2>
    </div>
    """, unsafe_allow_html=True)

def create_status_card(content: str, status: str = "info", icon: str = "ℹ️"):
    """Create a status card with different styles"""
    status_class = f"status-{status}"
    st.markdown(f"""
    <div class="status-card {status_class} slide-up">
        <div style="display: flex; align-items: center; gap: 0.75rem;">
            <span style="font-size: 1.25rem;">{icon}</span>
            <div>{content}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def create_metric_card(value: str, label: str, icon: str = "📊"):
    """Create a metric display card"""
    return f"""
    <div class="metric-card fade-in">
        <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">{icon}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-label">{label}</div>
    </div>
    """

def create_modern_container(content: str, compact: bool = False):
    """Create a modern card container"""
    card_class = "modern-card-compact" if compact else "modern-card"
    st.markdown(f"""
    <div class="{card_class} fade-in">
        {content}
    </div>
    """, unsafe_allow_html=True)

def create_progress_bar(progress: float, label: str = ""):
    """Create a modern progress bar"""
    st.markdown(f"""
    <div style="margin: 1rem 0;">
        {f'<div style="margin-bottom: 0.5rem; font-weight: 500; color: var(--text-secondary);">{label}</div>' if label else ''}
        <div style="background: var(--bg-tertiary); border-radius: 9999px; height: 8px; overflow: hidden;">
            <div class="progress-indicator" style="width: {progress}%;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def create_feature_grid(features: list):
    """Create a grid of feature cards"""
    cols = st.columns(len(features))
    for i, feature in enumerate(features):
        with cols[i]:
            st.markdown(create_metric_card(
                feature.get('value', ''),
                feature.get('label', ''),
                feature.get('icon', '📊')
            ), unsafe_allow_html=True)

def initialize_theme():
    """Initialize theme system and apply CSS"""
    # Create theme toggle and get current mode
    is_dark = create_theme_toggle()
    
    # Apply appropriate CSS
    apply_modern_css(is_dark)
    
    return is_dark 