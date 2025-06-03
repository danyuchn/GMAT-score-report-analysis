#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modern GUI Styles Module
現代化 GUI 樣式模組

Provides modern, minimalist CSS styles and layout components for the GMAT GUI system
為 GMAT GUI 系統提供現代化、極簡的 CSS 樣式和佈局組件
"""

import streamlit as st

def apply_modern_css():
    """Apply modern CSS styling to the Streamlit app"""
    
    st.markdown("""
    <style>
        /* Import Google Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&display=swap');
        
        /* Root variables for consistent theming - New Harmonious Color Palette */
        :root {
            --primary-color: #2563eb;
            --primary-light: #3b82f6;
            --primary-dark: #1d4ed8;
            --secondary-color: #059669;
            --accent-color: #0891b2;
            --warning-color: #d97706;
            --error-color: #dc2626;
            --success-color: #16a34a;
            --neutral-50: #f8fafc;
            --neutral-100: #f1f5f9;
            --neutral-200: #e2e8f0;
            --neutral-300: #cbd5e1;
            --neutral-400: #94a3b8;
            --neutral-500: #64748b;
            --neutral-600: #475569;
            --neutral-700: #334155;
            --neutral-800: #1e293b;
            --neutral-900: #0f172a;
            --surface-primary: rgba(248, 250, 252, 0.95);
            --surface-secondary: rgba(241, 245, 249, 0.9);
            --surface-accent: rgba(226, 232, 240, 0.8);
            --shadow-sm: 0 1px 2px 0 rgb(15 23 42 / 0.05);
            --shadow-md: 0 4px 6px -1px rgb(15 23 42 / 0.1), 0 2px 4px -2px rgb(15 23 42 / 0.1);
            --shadow-lg: 0 10px 15px -3px rgb(15 23 42 / 0.1), 0 4px 6px -4px rgb(15 23 42 / 0.1);
            --shadow-xl: 0 20px 25px -5px rgb(15 23 42 / 0.1), 0 8px 10px -6px rgb(15 23 42 / 0.1);
            --radius-sm: 0.375rem;
            --radius-md: 0.5rem;
            --radius-lg: 0.75rem;
            --radius-xl: 1rem;
        }
        
        /* Global reset and base styles */
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }
        
        /* Hide Streamlit default elements */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Main container with new harmonious background */
        .stApp {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 25%, #334155 50%, #475569 75%, #64748b 100%);
            min-height: 100vh;
        }
        
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 1200px;
        }
        
        /* Modern header styling with new colors */
        .modern-header {
            background: var(--surface-primary);
            backdrop-filter: blur(20px);
            border-radius: var(--radius-xl);
            padding: 2.5rem 2rem;
            margin-bottom: 2rem;
            text-align: center;
            box-shadow: var(--shadow-xl);
            border: 1px solid var(--neutral-200);
        }
        
        .modern-header h1 {
            font-size: 2.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, var(--primary-color), var(--accent-color));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 0.5rem;
            line-height: 1.2;
        }
        
        .modern-header p {
            font-size: 1.125rem;
            color: var(--neutral-600);
            font-weight: 400;
            margin: 0;
            opacity: 0.8;
        }
        
        /* Section headers */
        .section-header {
            background: var(--surface-secondary);
            backdrop-filter: blur(10px);
            border-radius: var(--radius-lg);
            padding: 1.5rem 2rem;
            margin: 1.5rem 0;
            border-left: 4px solid var(--primary-color);
            box-shadow: var(--shadow-md);
            border: 1px solid var(--neutral-200);
        }
        
        .section-header h2 {
            font-size: 1.5rem;
            font-weight: 600;
            color: var(--neutral-800);
            margin: 0;
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }
        
        /* Card components with new harmonious colors */
        .modern-card {
            background: var(--surface-primary);
            backdrop-filter: blur(20px);
            border-radius: var(--radius-xl);
            padding: 2rem;
            margin: 1rem 0;
            box-shadow: var(--shadow-lg);
            border: 1px solid var(--neutral-200);
            transition: all 0.3s ease;
        }
        
        .modern-card:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-xl);
            border-color: var(--neutral-300);
        }
        
        .modern-card-compact {
            background: var(--surface-secondary);
            backdrop-filter: blur(10px);
            border-radius: var(--radius-lg);
            padding: 1.5rem;
            margin: 0.75rem 0;
            box-shadow: var(--shadow-md);
            border: 1px solid var(--neutral-200);
        }
        
        /* Status cards with new color scheme */
        .status-card {
            border-radius: var(--radius-lg);
            padding: 1.5rem;
            margin: 1rem 0;
            box-shadow: var(--shadow-md);
            backdrop-filter: blur(10px);
            border: 1px solid var(--neutral-200);
        }
        
        .status-success {
            background: linear-gradient(135deg, rgba(22, 163, 74, 0.08), rgba(5, 150, 105, 0.05));
            border-left: 4px solid var(--success-color);
            color: var(--neutral-700);
        }
        
        .status-warning {
            background: linear-gradient(135deg, rgba(217, 119, 6, 0.08), rgba(245, 158, 11, 0.05));
            border-left: 4px solid var(--warning-color);
            color: var(--neutral-700);
        }
        
        .status-error {
            background: linear-gradient(135deg, rgba(220, 38, 38, 0.08), rgba(239, 68, 68, 0.05));
            border-left: 4px solid var(--error-color);
            color: var(--neutral-700);
        }
        
        .status-info {
            background: linear-gradient(135deg, rgba(37, 99, 235, 0.08), rgba(8, 145, 178, 0.05));
            border-left: 4px solid var(--primary-color);
            color: var(--neutral-700);
        }
        
        /* Metric cards */
        .metric-card {
            background: var(--surface-secondary);
            backdrop-filter: blur(10px);
            border-radius: var(--radius-lg);
            padding: 1.5rem;
            text-align: center;
            box-shadow: var(--shadow-md);
            border: 1px solid var(--neutral-200);
            transition: all 0.3s ease;
        }
        
        .metric-card:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-lg);
            border-color: var(--neutral-300);
        }
        
        .metric-value {
            font-size: 2rem;
            font-weight: 700;
            color: var(--primary-color);
            margin-bottom: 0.5rem;
        }
        
        .metric-label {
            font-size: 0.875rem;
            font-weight: 500;
            color: var(--neutral-600);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        /* Sidebar styling */
        .css-1d391kg {
            background: var(--surface-primary);
            backdrop-filter: blur(20px);
        }
        
        .css-1cypcdb {
            background: var(--surface-primary);
            backdrop-filter: blur(20px);
        }
        
        /* Tabs styling */
        .stTabs [data-baseweb="tab-list"] {
            background: var(--surface-secondary);
            backdrop-filter: blur(10px);
            border-radius: var(--radius-lg);
            padding: 0.5rem;
            box-shadow: var(--shadow-md);
            gap: 0.5rem;
            border: 1px solid var(--neutral-200);
        }
        
        .stTabs [data-baseweb="tab"] {
            background: transparent;
            border-radius: var(--radius-md);
            padding: 0.75rem 1.5rem;
            font-weight: 500;
            transition: all 0.3s ease;
            border: none;
            color: var(--neutral-600);
        }
        
        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, var(--primary-color), var(--primary-light));
            color: white;
            box-shadow: var(--shadow-sm);
        }
        
        .stTabs [data-baseweb="tab"]:hover {
            background: rgba(37, 99, 235, 0.08);
            color: var(--primary-color);
        }
        
        /* Button styling with new colors */
        .stButton > button {
            background: linear-gradient(135deg, var(--primary-color), var(--primary-light));
            color: white;
            border: none;
            border-radius: var(--radius-md);
            padding: 0.75rem 2rem;
            font-weight: 500;
            font-size: 1rem;
            box-shadow: var(--shadow-md);
            transition: all 0.3s ease;
        }
        
        .stButton > button:hover {
            transform: translateY(-1px);
            box-shadow: var(--shadow-lg);
            background: linear-gradient(135deg, var(--primary-dark), var(--primary-color));
        }
        
        .stButton > button:active {
            transform: translateY(0);
        }
        
        /* Download button styling */
        .stDownloadButton > button {
            background: linear-gradient(135deg, var(--secondary-color), var(--success-color));
            color: white;
            border: none;
            border-radius: var(--radius-md);
            padding: 0.75rem 1.5rem;
            font-weight: 500;
            box-shadow: var(--shadow-md);
            transition: all 0.3s ease;
        }
        
        .stDownloadButton > button:hover {
            transform: translateY(-1px);
            box-shadow: var(--shadow-lg);
        }
        
        /* Input styling */
        .stSelectbox > div > div,
        .stNumberInput > div > div > input,
        .stTextInput > div > div > input,
        .stDateInput > div > div > input {
            background: var(--surface-primary);
            backdrop-filter: blur(5px);
            border: 1px solid var(--neutral-300);
            border-radius: var(--radius-md);
            box-shadow: var(--shadow-sm);
            transition: all 0.3s ease;
            color: var(--neutral-700);
        }
        
        .stSelectbox > div > div:focus-within,
        .stNumberInput > div > div > input:focus,
        .stTextInput > div > div > input:focus,
        .stDateInput > div > div > input:focus {
            border-color: var(--primary-color);
            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
        }
        
        /* Slider styling */
        .stSlider > div > div > div > div {
            background: var(--primary-color);
        }
        
        /* Checkbox styling */
        .stCheckbox > label > div {
            border-radius: var(--radius-sm);
        }
        
        /* Expander styling */
        .streamlit-expanderHeader {
            background: var(--surface-secondary);
            backdrop-filter: blur(10px);
            border-radius: var(--radius-md);
            border: 1px solid var(--neutral-200);
            font-weight: 500;
            color: var(--neutral-700);
        }
        
        .streamlit-expanderContent {
            background: var(--surface-primary);
            backdrop-filter: blur(10px);
            border-radius: 0 0 var(--radius-md) var(--radius-md);
            border: 1px solid var(--neutral-200);
            border-top: none;
        }
        
        /* DataFrame styling */
        .stDataFrame {
            background: var(--surface-primary);
            backdrop-filter: blur(10px);
            border-radius: var(--radius-md);
            box-shadow: var(--shadow-md);
            overflow: hidden;
            border: 1px solid var(--neutral-200);
        }
        
        /* Code blocks */
        .stCodeBlock {
            background: rgba(15, 23, 42, 0.95);
            backdrop-filter: blur(10px);
            border-radius: var(--radius-md);
            border: 1px solid var(--neutral-700);
            font-family: 'JetBrains Mono', monospace;
        }
        
        /* Plotly charts */
        .js-plotly-plot {
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow-lg);
            overflow: hidden;
        }
        
        /* Custom spacing utilities */
        .mt-4 { margin-top: 1rem; }
        .mb-4 { margin-bottom: 1rem; }
        .py-4 { padding-top: 1rem; padding-bottom: 1rem; }
        .px-4 { padding-left: 1rem; padding-right: 1rem; }
        
        /* Animation utilities */
        .fade-in {
            animation: fadeIn 0.5s ease-in;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .slide-up {
            animation: slideUp 0.3s ease-out;
        }
        
        @keyframes slideUp {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        /* Progress indicator */
        .progress-indicator {
            background: linear-gradient(90deg, var(--primary-color), var(--accent-color));
            height: 4px;
            border-radius: 2px;
            transition: width 0.3s ease;
        }
        
        /* Responsive design */
        @media (max-width: 768px) {
            .modern-header h1 {
                font-size: 2rem;
            }
            
            .modern-header {
                padding: 2rem 1.5rem;
            }
            
            .modern-card {
                padding: 1.5rem;
            }
            
            .section-header {
                padding: 1rem 1.5rem;
            }
        }
        
        /* Additional harmonious styling */
        .text-primary { color: var(--primary-color); }
        .text-secondary { color: var(--secondary-color); }
        .text-muted { color: var(--neutral-500); }
        .bg-gradient {
            background: linear-gradient(135deg, var(--primary-color), var(--accent-color));
        }
        
        /* Smooth transitions for all interactive elements */
        * {
            transition: color 0.2s ease, background-color 0.2s ease, border-color 0.2s ease, opacity 0.2s ease;
        }
        
    </style>
    """, unsafe_allow_html=True)

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
        {f'<div style="margin-bottom: 0.5rem; font-weight: 500; color: var(--neutral-700);">{label}</div>' if label else ''}
        <div style="background: var(--neutral-200); border-radius: 9999px; height: 8px; overflow: hidden;">
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