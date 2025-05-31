"""
Plotting service module

Provides functions for generating charts
"""

import pandas as pd
import logging
import plotly.graph_objects as go
from gmat_diagnosis_app.i18n import translate as t

def create_theta_plot(theta_history_df, subject_name):
    """Creates a Plotly line chart of theta estimation history, starting from question 0 (initial theta)."""
    if theta_history_df is None or theta_history_df.empty:
        logging.warning(t('plot_theta_empty_data_warning').format(subject_name))
        return None

    # Check if we can get the initial theta from the 'before' column
    if 'theta_est_before_answer' in theta_history_df.columns and not theta_history_df['theta_est_before_answer'].empty:
        initial_theta = theta_history_df['theta_est_before_answer'].iloc[0]
        # Prepare data starting from question 0
        x_values = [0] + (theta_history_df.index + 1).tolist()
        y_values = [initial_theta] + theta_history_df['theta_est_after_answer'].tolist()
        hover_text = [t('plot_initial_theta_hover').format(initial_theta)] + \
                         [t('plot_question_theta_hover').format(i+1, theta) for i, theta in enumerate(theta_history_df['theta_est_after_answer'])]

    elif 'theta_est_after_answer' in theta_history_df.columns and not theta_history_df['theta_est_after_answer'].empty:
        # Fallback: Start from question 1 if 'before' data is missing
        logging.warning(t('plot_theta_missing_before_warning').format(subject_name))
        x_values = (theta_history_df.index + 1).tolist()
        y_values = theta_history_df['theta_est_after_answer'].tolist()
        hover_text = [t('plot_question_theta_hover').format(i+1, theta) for i, theta in enumerate(y_values)]
    else:
        logging.warning(t('plot_theta_missing_columns_warning').format(subject_name))
        return None

    fig = go.Figure()
    # Add trace using the prepared x and y values
    fig.add_trace(go.Scatter(
        x=x_values,
        y=y_values,
        mode='lines+markers',
        name=t('plot_theta_estimation_name'),
        line=dict(color='royalblue', width=2),
        marker=dict(color='royalblue', size=5),
        hovertemplate=hover_text # Use the combined hover text
    ))

    fig.update_layout(
        title=t('plot_theta_title').format(subject_name),
        xaxis_title=t('plot_theta_xaxis_title'), # Update axis title
        yaxis_title=t('plot_theta_yaxis_title'),
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
        legend_title_text=t('plot_legend_title')
    )
    return fig 