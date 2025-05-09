"""
繪圖服務模組
提供生成圖表的功能
"""

import pandas as pd
import logging
import plotly.graph_objects as go

def create_theta_plot(theta_history_df, subject_name):
    """Creates a Plotly line chart of theta estimation history, starting from question 0 (initial theta)."""
    if theta_history_df is None or theta_history_df.empty:
        logging.warning(f"無法為 {subject_name} 生成 Theta 圖表，因為歷史數據為空。")
        return None

    # Check if we can get the initial theta from the 'before' column
    if 'theta_est_before_answer' in theta_history_df.columns and not theta_history_df['theta_est_before_answer'].empty:
        initial_theta = theta_history_df['theta_est_before_answer'].iloc[0]
        # Prepare data starting from question 0
        x_values = [0] + (theta_history_df.index + 1).tolist()
        y_values = [initial_theta] + theta_history_df['theta_est_after_answer'].tolist()
        hover_text = [f"初始 Theta: {initial_theta:.3f}<extra></extra>"] + \
                         [f"題號 {i+1}<br>Theta: {theta:.3f}<extra></extra>" for i, theta in enumerate(theta_history_df['theta_est_after_answer'])]

    elif 'theta_est_after_answer' in theta_history_df.columns and not theta_history_df['theta_est_after_answer'].empty:
        # Fallback: Start from question 1 if 'before' data is missing
        logging.warning(f"在 {subject_name} 的歷史數據中找不到 'theta_est_before_answer'，圖表將從題號 1 開始。")
        x_values = (theta_history_df.index + 1).tolist()
        y_values = theta_history_df['theta_est_after_answer'].tolist()
        hover_text = [f"題號 {i+1}<br>Theta: {theta:.3f}<extra></extra>" for i, theta in enumerate(y_values)]
    else:
        logging.warning(f"無法為 {subject_name} 生成 Theta 圖表，因為歷史數據缺少必要的 Theta 列。")
        return None

    fig = go.Figure()
    # Add trace using the prepared x and y values
    fig.add_trace(go.Scatter(
        x=x_values,
        y=y_values,
        mode='lines+markers',
        name='Theta 估計值',
        line=dict(color='royalblue', width=2),
        marker=dict(color='royalblue', size=5),
        hovertemplate=hover_text # Use the combined hover text
    ))

    fig.update_layout(
        title=f"{subject_name} 科目能力 (Theta) 估計變化",
        xaxis_title="題號 (0=初始值)", # Update axis title
        yaxis_title="Theta (能力估計值)",
        xaxis=dict(
            showgrid=True,
            zeroline=False,
            # Adjust dtick for potentially starting from 0
            dtick=max(1, (len(x_values)-1) // 10 if len(x_values) > 1 else 1),
            tick0=0 # Ensure ticks start nicely from 0
        ),
        yaxis=dict(
            showgrid=True,
            zeroline=True,
            range=[-4, 4] # FIX: Set fixed y-axis range
        ),
        hovermode="x unified",
        legend_title_text='估計值類型'
    )
    return fig 