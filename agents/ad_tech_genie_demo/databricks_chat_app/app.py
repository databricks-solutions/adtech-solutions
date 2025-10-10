import sys
import os
import io # Added for BytesIO

# Calculate the project root directory
# __file__ is /Users/charlie.hohenstein/Documents/databricks_chat_app/app.py
# os.path.dirname(__file__) is /Users/charlie.hohenstein/Documents/databricks_chat_app
# os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) is /Users/charlie.hohenstein/Documents/
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Add PROJECT_ROOT to sys.path if it's not already there
# This ensures that 'databricks_chat_app' can be imported as a top-level package
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# For debugging the path:
# print("[DEBUG app.py] Current sys.path:", sys.path, flush=True)

import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
from dotenv import load_dotenv
from fpdf import FPDF # Added for PDF generation

# Now this absolute import should work because PROJECT_ROOT (containing databricks_chat_app dir) is on sys.path
from databricks_chat_app.genie_logic import ask_genie_question, get_workspace_client_status
from databricks.sdk.errors import DatabricksError
import pandas as pd

# Load environment variables from .env file in the project root
dotenv_path = os.path.join(PROJECT_ROOT, '.env')
load_dotenv(dotenv_path=dotenv_path)

DATABRICKS_HOST = os.getenv("DATABRICKS_HOST")
DATABRICKS_TOKEN = os.getenv("DATABRICKS_TOKEN")
GENIE_SPACE_ID = os.getenv("GENIE_SPACE_ID")

client_initialized, w = get_workspace_client_status()

# --- PDF Generation Function ---
def generate_report_pdf(message_data):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Agent Chat Report", border=0, ln=1, align="C")
    pdf.ln(5)

    # Main Text / Query Description
    pdf.set_font("Helvetica", "B", 12)
    query_desc_text = message_data.get('query_description')
    main_text_val = message_data.get("main_text")

    if query_desc_text:
        pdf.multi_cell(0, 10, f"Query Analysis: {query_desc_text}", border=0, align="L")
        pdf.ln(1)
    elif main_text_val:
        pdf.multi_cell(0, 10, main_text_val, border=0, align="L")
        pdf.ln(1)
    pdf.ln(5)

    raw_table_data = message_data.get("raw_table_data")
    if raw_table_data and isinstance(raw_table_data, dict):
        cols = raw_table_data.get("columns")
        data_array = raw_table_data.get("data")

        if cols and data_array:
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 10, "Table Data:", border=0, ln=1, align="L")
            pdf.set_font("Helvetica", "", 8)
            
            # Calculate column widths (simple equal distribution for now)
            num_cols = len(cols)
            page_width = pdf.w - 2 * pdf.l_margin
            col_width = page_width / num_cols if num_cols > 0 else page_width
            line_height = pdf.font_size * 1.5

            # Headers
            for col_name in cols:
                pdf.cell(col_width, line_height, col_name, border=1)
            pdf.ln(line_height)

            # Data rows
            for row in data_array:
                for item_idx, item in enumerate(row):
                    pdf.cell(col_width, line_height, str(item), border=1)
                pdf.ln(line_height)
            pdf.ln(10)

    # --- Charts --- 
    raw_table_data_for_charts = message_data.get("raw_table_data")
    if raw_table_data_for_charts and isinstance(raw_table_data_for_charts, dict):
        cols = raw_table_data_for_charts.get("columns")
        data = raw_table_data_for_charts.get("data")

        if cols and data:
            # Common DataFrame for charts
            df_charts = pd.DataFrame(data, columns=cols)
            for col in df_charts.columns:
                df_charts[col] = pd.to_numeric(df_charts[col], errors='ignore')
            
            page_width = pdf.w - 2 * pdf.l_margin # For image width calculations
            img_width = page_width * 0.9 # Use 90% of page width for charts

            # --- Bar Chart (Matplotlib) ---
            try:
                pdf.set_font("Helvetica", "B", 10)
                pdf.cell(0, 10, "Bar Chart:", 0, 1, "L")
                fig_bar, ax_bar = plt.subplots(figsize=(8, 4)) # Adjust figsize as needed for PDF
                numeric_cols_bar = df_charts.select_dtypes(include=np.number).columns.tolist()
                string_cols_bar = df_charts.select_dtypes(include=['object', 'string']).columns.tolist()

                if not numeric_cols_bar:
                    ax_bar.text(0.5, 0.5, "No numeric data for bar chart", ha='center', va='center')
                elif string_cols_bar:
                    chart_df_bar = df_charts.set_index(string_cols_bar[0])
                    if not chart_df_bar.empty and any(chart_df_bar.select_dtypes(include=np.number).any()):
                        chart_df_bar[numeric_cols_bar].plot(kind='bar', ax=ax_bar)
                        ax_bar.tick_params(axis='x', rotation=45)
                    else:
                        ax_bar.text(0.5, 0.5, "Could not generate bar chart", ha='center', va='center')
                elif len(numeric_cols_bar) == 1:
                    df_charts[numeric_cols_bar[0]].plot(kind='bar', ax=ax_bar)
                    ax_bar.set_xlabel(df_charts.columns[0] if len(df_charts.columns)>0 else "Index")
                    ax_bar.tick_params(axis='x', rotation=45)
                else: # Plot all numeric if no string column, or multiple numeric
                    df_charts[numeric_cols_bar].plot(kind='bar', ax=ax_bar)
                    ax_bar.tick_params(axis='x', rotation=45)
                
                ax_bar.set_title("Bar Chart Visualization")
                plt.tight_layout()
                img_bar_bytes = io.BytesIO()
                fig_bar.savefig(img_bar_bytes, format='png', bbox_inches='tight')
                img_bar_bytes.seek(0)
                pdf.image(img_bar_bytes, x=None, y=None, w=img_width, type='PNG')
                plt.close(fig_bar)
                pdf.ln(5)
            except Exception as e:
                pdf.set_font("Helvetica", "", 8)
                pdf.multi_cell(0, 5, f"Error generating bar chart for PDF: {e}", 0, 1)
                plt.close('all') # Close any lingering figures

            # --- Pie Chart (Matplotlib) ---
            try:
                numeric_cols_pie = df_charts.select_dtypes(include=np.number).columns.tolist()
                string_cols_pie = df_charts.select_dtypes(include=['object', 'string']).columns.tolist()
                if len(string_cols_pie) == 1 and len(numeric_cols_pie) == 1:
                    categorical_col_pie = string_cols_pie[0]
                    numerical_col_pie = numeric_cols_pie[0]
                    if df_charts[categorical_col_pie].nunique() > 0 and df_charts[categorical_col_pie].nunique() <= 10:
                        pdf.set_font("Helvetica", "B", 10)
                        pdf.cell(0, 10, "Pie Chart:", 0, 1, "L")
                        fig_pie, ax_pie = plt.subplots(figsize=(6, 4))
                        ax_pie.pie(df_charts[numerical_col_pie], labels=df_charts[categorical_col_pie], autopct='%1.1f%%', startangle=90)
                        ax_pie.axis('equal')
                        ax_pie.set_title(f"Pie Chart: {numerical_col_pie} by {categorical_col_pie}")
                        plt.tight_layout()
                        img_pie_bytes = io.BytesIO()
                        fig_pie.savefig(img_pie_bytes, format='png', bbox_inches='tight')
                        img_pie_bytes.seek(0)
                        pdf.image(img_pie_bytes, x=None, y=None, w=img_width*0.75, type='PNG') # Pie chart often smaller
                        plt.close(fig_pie)
                        pdf.ln(5)
            except Exception as e:
                pdf.set_font("Helvetica", "", 8)
                pdf.multi_cell(0, 5, f"Error generating pie chart for PDF: {e}", 0, 1)
                plt.close('all')

            # --- Line Chart (Matplotlib) ---
            try:
                numeric_cols_line = df_charts.select_dtypes(include=np.number).columns.tolist()
                string_cols_line = df_charts.select_dtypes(include=['object', 'string']).columns.tolist()
                if numeric_cols_line:
                    pdf.set_font("Helvetica", "B", 10)
                    pdf.cell(0, 10, "Line Chart:", 0, 1, "L")
                    fig_line, ax_line = plt.subplots(figsize=(8, 4))
                    df_to_plot_line = df_charts.copy()
                    if string_cols_line:
                        try:
                            df_to_plot_line = df_to_plot_line.set_index(string_cols_line[0])
                            if df_to_plot_line.index.nunique() > 1 or df_to_plot_line.index.is_monotonic_increasing or df_to_plot_line.index.is_monotonic_decreasing:
                                df_to_plot_line[numeric_cols_line].plot(kind='line', ax=ax_line)
                            else:
                                df_charts[numeric_cols_line].plot(kind='line', ax=ax_line, use_index=False) # Plot against numerical index
                        except Exception:
                             df_charts[numeric_cols_line].plot(kind='line', ax=ax_line, use_index=False)
                    else:
                        df_charts[numeric_cols_line].plot(kind='line', ax=ax_line)
                    ax_line.set_title("Line Chart Visualization")
                    plt.tight_layout()
                    img_line_bytes = io.BytesIO()
                    fig_line.savefig(img_line_bytes, format='png', bbox_inches='tight')
                    img_line_bytes.seek(0)
                    pdf.image(img_line_bytes, x=None, y=None, w=img_width, type='PNG')
                    plt.close(fig_line)
                    pdf.ln(5)
            except Exception as e:
                pdf.set_font("Helvetica", "", 8)
                pdf.multi_cell(0, 5, f"Error generating line chart for PDF: {e}", 0, 1)
                plt.close('all')

            # --- Histograms (Matplotlib) ---
            try:
                numeric_cols_hist = df_charts.select_dtypes(include=np.number).columns.tolist()
                if numeric_cols_hist:
                    pdf.set_font("Helvetica", "B", 10)
                    pdf.cell(0, 10, "Histograms:", 0, 1, "L")
                    for num_col in numeric_cols_hist:
                        fig_hist, ax_hist = plt.subplots(figsize=(6, 4))
                        ax_hist.hist(df_charts[num_col].dropna(), bins='auto', edgecolor='black')
                        ax_hist.set_xlabel(num_col)
                        ax_hist.set_ylabel("Frequency")
                        ax_hist.set_title(f"Histogram for: {num_col}")
                        plt.tight_layout()
                        img_hist_bytes = io.BytesIO()
                        fig_hist.savefig(img_hist_bytes, format='png', bbox_inches='tight')
                        img_hist_bytes.seek(0)
                        pdf.image(img_hist_bytes, x=None, y=None, w=img_width*0.8, type='PNG')
                        plt.close(fig_hist)
                        pdf.ln(2) # Smaller break between multiple histograms
                    pdf.ln(5)
            except Exception as e:
                pdf.set_font("Helvetica", "", 8)
                pdf.multi_cell(0, 5, f"Error generating histograms for PDF: {e}", 0, 1)
                plt.close('all')

    pdf_output_bytes = bytes(pdf.output(dest='S'))
    return pdf_output_bytes

# --- Reusable function to display charts ---
def display_charts_from_raw_data(raw_table_data):
    if not raw_table_data or not isinstance(raw_table_data, dict):
        return

    cols = raw_table_data.get("columns")
    data = raw_table_data.get("data")

    if not cols or not data:
        return

    # Bar Chart
    try:
        with st.expander("Bar Chart Visualization", expanded=False):
            df_bar = pd.DataFrame(data, columns=cols)
            for col in df_bar.columns:
                df_bar[col] = pd.to_numeric(df_bar[col], errors='ignore')
            numeric_cols_bar = df_bar.select_dtypes(include=np.number).columns.tolist()
            string_cols_bar = df_bar.select_dtypes(include=['object', 'string']).columns.tolist()
            if not numeric_cols_bar:
                st.caption("No numeric data available to plot a bar chart.")
            elif string_cols_bar:
                chart_df_bar = df_bar.set_index(string_cols_bar[0])
                if not chart_df_bar.empty and any(chart_df_bar.select_dtypes(include=np.number).any()):
                    st.bar_chart(chart_df_bar[numeric_cols_bar])
                else:
                    st.caption("Could not generate a bar chart with the available data.")
            elif len(numeric_cols_bar) == 1:
                st.bar_chart(df_bar[numeric_cols_bar[0]])
            elif len(df_bar.columns) <= 10:
                st.bar_chart(df_bar)
            else:
                st.caption("Displaying first numeric column for bar chart.")
                st.bar_chart(df_bar[numeric_cols_bar[0]])
    except Exception as e_chart:
        st.warning(f"Could not generate bar chart: {e_chart}")
        print(f"[APP_ERROR] Bar charting error: {e_chart}")

    # Pie Chart
    try:
        df_pie = pd.DataFrame(data, columns=cols)
        for col in df_pie.columns:
            df_pie[col] = pd.to_numeric(df_pie[col], errors='ignore')
        numeric_cols_pie = df_pie.select_dtypes(include=np.number).columns.tolist()
        string_cols_pie = df_pie.select_dtypes(include=['object', 'string']).columns.tolist()
        if len(string_cols_pie) == 1 and len(numeric_cols_pie) == 1:
            categorical_col_pie = string_cols_pie[0]
            numerical_col_pie = numeric_cols_pie[0]
            if df_pie[categorical_col_pie].nunique() > 0 and df_pie[categorical_col_pie].nunique() <= 10:
                with st.expander("Pie Chart Visualization", expanded=False):
                    fig, ax = plt.subplots(figsize=(5, 3))
                    ax.pie(df_pie[numerical_col_pie], labels=df_pie[categorical_col_pie], autopct='%1.1f%%', startangle=90)
                    ax.axis('equal')
                    st.pyplot(fig)
                    plt.close(fig)
            # else: (no specific message if pie chart conditions not met)
    except Exception as e_pie_chart:
        st.warning(f"Could not generate pie chart: {e_pie_chart}")
        print(f"[APP_ERROR] Pie charting error: {e_pie_chart}")

    # Line Chart
    try:
        df_line = pd.DataFrame(data, columns=cols)
        for col in df_line.columns:
            df_line[col] = pd.to_numeric(df_line[col], errors='ignore')
        numeric_cols_line = df_line.select_dtypes(include=np.number).columns.tolist()
        string_cols_line = df_line.select_dtypes(include=['object', 'string']).columns.tolist()
        if numeric_cols_line:
            with st.expander("Line Chart Visualization", expanded=False):
                df_to_plot_line = df_line.copy() # Use a copy to avoid modifying original df_line
                if string_cols_line:
                    try:
                        df_to_plot_line = df_to_plot_line.set_index(string_cols_line[0])
                        # Check if index is suitable (e.g. not all identical values if it's numeric after conversion)
                        if df_to_plot_line.index.nunique() > 1 or df_to_plot_line.index.is_monotonic_increasing or df_to_plot_line.index.is_monotonic_decreasing:
                             st.line_chart(df_to_plot_line[numeric_cols_line])
                        else:
                             st.line_chart(df_line[numeric_cols_line]) # Fallback to default numeric plot
                    except Exception:
                         st.line_chart(df_line[numeric_cols_line]) # Fallback on error setting index
                else:
                    st.line_chart(df_line[numeric_cols_line])
        # else: (no specific message if line chart conditions not met)
    except Exception as e_line_chart:
        st.warning(f"Could not generate line chart: {e_line_chart}")
        print(f"[APP_ERROR] Line charting error: {e_line_chart}")

    # Histograms
    try:
        df_hist = pd.DataFrame(data, columns=cols)
        for col_name_hist in df_hist.columns:
            df_hist[col_name_hist] = pd.to_numeric(df_hist[col_name_hist], errors='ignore')
        numeric_cols_hist = df_hist.select_dtypes(include=np.number).columns.tolist()
        if numeric_cols_hist:
            with st.expander("Histogram(s)", expanded=False):
                for num_col in numeric_cols_hist:
                    st.markdown(f"**Histogram for: {num_col}**")
                    fig, ax = plt.subplots(figsize=(5, 3))
                    ax.hist(df_hist[num_col].dropna(), bins='auto', edgecolor='black')
                    ax.set_xlabel(num_col)
                    ax.set_ylabel("Frequency")
                    st.pyplot(fig)
                    plt.close(fig)
    except Exception as e_hist_chart:
        st.warning(f"Could not generate histograms: {e_hist_chart}")
        print(f"[APP_ERROR] Histogram charting error: {e_hist_chart}")

# --- Streamlit App Page Config --- 
st.set_page_config(page_title="Agent Chat", layout="wide")

# --- Custom CSS for Modern Look (Akkio Inspired) --- 
st.markdown("""
<style>
    /* --- General App Body & Font --- */
    body {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji";
        background-color: #f8f9fa; /* Light, clean off-white background */
        color: #343a40; /* Darker text for readability */
        margin: 0;
        padding: 0;
    }
    .stApp {
        background-color: #f8f9fa;
        padding-top: 0 !important; /* Remove Streamlit's default top padding */
    }

    /* --- Header Area --- */
    .main-header-wrapper {
        padding: 0.25rem 1.5rem 0.75rem 1.5rem;
        border-bottom: 1px solid #dee2e6;
        background-color: #ffffff;
        display: flex;
        /* justify-content: space-between; Ensures sub-sections are spaced out if they don't fill 100% */
        align-items: center;
        width: 100%;
        box-sizing: border-box;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 1rem;
    }

    .sub-header-section {
        flex-basis: 50%; /* Each section takes up 50% of the wrapper's width */
        display: flex;
        align-items: center; /* Vertically center content within each sub-header */
        /* padding: 0 10px; Optional: add some padding if needed between sections or at ends */
    }

    .sub-header-section.header-left {
        justify-content: flex-start; /* Align content (logo & title) to the left */
    }
    .sub-header-section.header-left img {
        height: 40px;
        margin-right: 15px;
    }
    .sub-header-section.header-left h1 {
        color: #212529;
        font-size: 1.6rem;
        font-weight: 600;
        margin: 0;
    }

    .sub-header-section.header-right {
        justify-content: flex-start; /* Align title to the left within its 50% space */
        /* To center: justify-content: center; */
        /* To right-align: justify-content: flex-end; padding-right: 1.5rem; (adjust padding) */
    }
    .sub-header-section.header-right h1 {
        color: #212529;
        font-size: 1.6rem;
        font-weight: 600;
        margin: 0;
    }

    /* --- Chat Caption --- */
    .stCaption {
        text-align: center;
        color: #6c757d; /* Standard caption color */
        margin-top: 1rem;
        margin-bottom: 1rem;
    }

    /* --- Chat Input Area --- */
    .stChatInputContainer {
        background-color: #ffffff; /* White background for input bar */
        border-top: 1px solid #dee2e6;
        padding: 0.75rem 1rem;
        position: fixed; 
        bottom: 0;
        left: 0; 
        width: 50vw; 
        z-index: 990;
        box-sizing: border-box; 
        box-shadow: 0 -2px 5px rgba(0,0,0,0.05); /* Shadow on top of input bar */
    }
    .stTextInput input {
        border: 1px solid #ced4da;
        border-radius: 12px; /* More rounded */
        padding: 12px 18px; /* More padding */
        font-size: 1rem;
        background-color: #fff;
        box-shadow: inset 0 1px 2px rgba(0,0,0,0.075); /* Subtle inset shadow */
        transition: border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
    }
    .stTextInput input:focus {
        border-color: #A50034; /* LG Red for focus */
        box-shadow: inset 0 1px 2px rgba(0,0,0,0.075), 0 0 0 0.2rem rgba(165,0,52,0.25); /* LG Red focus ring */
    }
    .stButton>button { 
        background-color: #A50034; 
        color: white;
        border-radius: 12px; /* More rounded */
        border: none;
        padding: 12px 22px; /* More padding */
        font-weight: 500;
        transition: background-color 0.2s ease, transform 0.1s ease, box-shadow 0.2s ease;
        box-shadow: 0 2px 3px rgba(0,0,0,0.1); /* Subtle button shadow */
    }
    .stButton>button:hover {
        background-color: #8A0029;
        color: white;
        transform: translateY(-1px); /* Slight lift on hover */
        box-shadow: 0 4px 6px rgba(0,0,0,0.15);
    }
    .stButton>button:active {
        transform: translateY(0px);
        box-shadow: 0 2px 3px rgba(0,0,0,0.1);
    }

    /* --- Chat Messages --- */
    [data-testid="stChatMessage"] {
        background-color: #e9ecef; /* Default assistant message background */
        border-radius: 18px; /* Softer, more rounded bubbles */
        padding: 14px 20px; /* Increased padding */
        margin-bottom: 12px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.08); /* Softer shadow */
        border: none; 
        max-width: 70%; 
    }
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
        background-color: #A50034; /* LG Red for user messages */
    }
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) p,
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) div,
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) span,
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) strong,
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) table,
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) th,
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) td {
        color: white !important; /* White text for user messages */
    }
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) a {
        color: #ffd1d1 !important; /* Lighter link color for user messages */
    }
    [data-testid="stChatMessage"] p {
        margin-bottom: 0.5em;
        line-height: 1.6;
        color: #212529; /* Default text color */
    }
    [data-testid="stChatMessage"] pre {
        background-color: rgba(0,0,0,0.05); /* Slightly darker pre for contrast */
        border-radius: 8px;
        padding: 0.75em 1em;
    }
    [data-testid="stChatMessage"] table {
        border-collapse: collapse;
        width: 100%;
        margin-top: 1em;
        margin-bottom: 1em;
    }
    [data-testid="stChatMessage"] th, [data-testid="stChatMessage"] td {
        border: 1px solid rgba(0,0,0,0.1); /* Lighter table borders */
        padding: 10px 12px;
    }
    [data-testid="stChatMessage"] th {
        background-color: rgba(0,0,0,0.03); /* Subtle table header background */
    }
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) th {
         background-color: rgba(255,255,255,0.1); /* Lighter table header for user messages */
    }
     [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) td {
        border: 1px solid rgba(255,255,255,0.2);
    }


    /* --- Expanders --- */
    [data-testid="stExpander"] {
        border: 1px solid #dee2e6; /* Lighter border */
        border-radius: 12px; /* More rounded */
        margin-top: 1rem;
        background-color: #ffffff;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04); /* Subtle shadow */
        transition: box-shadow 0.2s ease;
    }
     [data-testid="stExpander"]:hover {
        box-shadow: 0 3px 6px rgba(0,0,0,0.06); /* Slightly more shadow on hover */
    }
    [data-testid="stExpander"] summary {
        font-weight: 600; /* Bolder summary */
        color: #343a40;
        padding: 0.75rem 1rem; /* Adjusted padding */
        border-radius: 12px 12px 0 0; /* Match parent rounding */
    }
    [data-testid="stExpander"] summary:hover {
        background-color: #f8f9fa; /* Slight hover background */
    }
    .streamlit-expanderContent {
        padding: 0.5rem 1rem 1rem 1rem; /* Adjust content padding */
    }

    /* --- Spinner --- */
    .spinner {
        border: 3px solid rgba(0, 0, 0, 0.1);
        width: 20px;
        height: 20px;
        border-radius: 50%;
        border-left-color: #A50034; /* LG Red spinner */
        animation: spin 0.8s ease infinite;
        display: inline-block;
        vertical-align: middle;
        margin-right: 8px;
    }
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }

    /* --- Error Messages --- */
    [data-testid="stErrorMessage"] {
        border-left: 4px solid #A50034 !important; /* Thicker LG Red border */
        background-color: #ffebee; /* Lighter red background */
        border-radius: 8px;
        padding: 1rem;
        box-shadow: 0 2px 4px rgba(165,0,52,0.1); /* Subtle shadow for errors */
    }
    
    /* --- Scrollable Chat Column --- */
    div[data-testid="stApp"] div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(1) {
        height: calc(100vh - 145px); /* 100vh - Est. Header - Est. Chat Input Bar - Small Buffer */
        overflow-y: auto;
        padding: 0.5rem 1rem; /* Top/bottom and Left/right padding inside the scrollable column */
    }
    
    /* --- Dashboard Iframe Container --- */
    .dashboard-iframe-container {
        padding: 1rem; /* Padding around the iframe */
        background-color: #ffffff; /* White background for the container */
        border-radius: 12px; /* Rounded corners */
        box-shadow: 0 4px 12px rgba(0,0,0,0.1); /* More prominent shadow for dashboard area */
        height: calc(800px); /* Ensure container takes up height, adjust if needed */
        display: flex; /* To make iframe fill height */
    }
    .dashboard-iframe-container iframe {
        border-radius: 8px; /* Match iframe border to container */
        flex-grow: 1; /* Allow iframe to fill container */
    }

    /* --- Sleek PDF Download Button --- */
    [data-testid="stChatMessage"] .pdf-button-area button,
    [data-testid="stChatMessage"] .pdf-button-area button:visited,
    [data-testid="stChatMessage"] .pdf-button-area button:hover,
    [data-testid="stChatMessage"] .pdf-button-area button:focus,
    [data-testid="stChatMessage"] .pdf-button-area button:active {
        background-image: none !important; 
        background-color: #add8e6 !important;
        color: black !important;
        border: 1px solid #90c5d7 !important; /* Border to complement light blue */
        border-radius: 8px !important;
        padding: 6px 12px !important; 
        font-size: 0.85rem !important; 
        font-weight: 500 !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji" !important; 
        cursor: pointer !important;
        transition: background-color 0.2s ease, border-color 0.2s ease, transform 0.1s ease, box-shadow 0.2s ease !important;
        margin-top: 0.75rem !important; 
        box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
        line-height: 1.5 !important; 
        text-align: center !important;
        text-decoration: none !important; 
    }
    [data-testid="stChatMessage"] .pdf-button-area button:hover {
        background-image: none !important;
        background-color: #90c5d7 !important; /* Slightly darker blue for hover */
        border-color: #7eb8cc !important;
        color: black !important; /* Keep text black on hover */
        transform: translateY(-1px) !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
    }
    [data-testid="stChatMessage"] .pdf-button-area button:active {
        background-image: none !important;
        background-color: #7eb8cc !important;
        transform: translateY(0px) !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
        color: black !important; /* Keep text black on active */
    }

</style>
""", unsafe_allow_html=True)

# --- App Header (Logo & Title - Top Center) --- 
LOGO_URL = "lkn"

# Header HTML - This is a fixed header
st.markdown(f'''
<div class="main-header-wrapper">
    <div class="sub-header-section header-left">
        <img src="{LOGO_URL}" alt="LG Logo">
        <h1>Agent Chat</h1>
    </div>
    <div class="sub-header-section header-right">
        <h1>Campaign Reporting Dashboard</h1>
    </div>
</div>
''', unsafe_allow_html=True)

if not client_initialized:
    st.error(
        "WorkspaceClient initialization failed. "
        "Check DATABRICKS_HOST and DATABRICKS_TOKEN in .env file and server logs."
    )
else:
    # --- Create two columns: Chat on the left, Dashboard on the right ---
    col1, col2 = st.columns(2) # Adjusted for 50/50 split

    with col1:
        # st.caption(f"Using Genie Space ID: {GENIE_SPACE_ID if GENIE_SPACE_ID and GENIE_SPACE_ID != 'YOUR_GENIE_SPACE_ID_ENV_NOT_SET' else 'Not Configured (Set GENIE_SPACE_ID env var)"})

        if "messages" not in st.session_state:
            st.session_state.messages = []

        if not st.session_state.messages: # If truly empty (first run, no history yet)
            st.session_state.messages.append({
                "role": "assistant",
                "main_text": "Hi there! Ask me anything about your data to get started.",
                "original_genie_text_response": None,
                "query_description": None,
                "table_html": None,
                "raw_table_data": None,
                "additional_texts": [],
                "visualization_info": None,
                "error_message": None
            })

        # Render all messages from history
        for message_data in st.session_state.messages:
            with st.chat_message(message_data["role"]):
                if message_data["role"] == "user":
                    st.markdown(message_data["content"]) # User messages still use "content"
                else: # Assistant message
                    # Display the main text content
                    st.markdown(message_data.get("main_text", "Response from assistant."))

                    # Display error if present and not already part of main_text
                    error_msg = message_data.get("error_message")
                    if error_msg and not (message_data.get("main_text","") and error_msg in message_data.get("main_text","")):
                        st.error(f"**An error occurred:** {error_msg}")
                    
                    additional_texts = message_data.get("additional_texts")
                    if additional_texts:
                        with st.expander("Additional Information", expanded=True):
                            for add_text in additional_texts:
                                if add_text != message_data.get("main_text"):
                                    st.markdown(add_text)
                    
                    table_html = message_data.get("table_html")
                    if table_html:
                        with st.expander("Table View", expanded=True):
                            st.markdown(table_html, unsafe_allow_html=True)
                    
                    raw_data = message_data.get("raw_table_data")
                    if raw_data and isinstance(raw_data, dict):
                        display_charts_from_raw_data(raw_data)
                    
                    viz_info = message_data.get("visualization_info")
                    if viz_info:
                        with st.expander("Genie Visualization Output", expanded=False):
                            st.json(viz_info)
                    
                    # --- PDF Download Button for this specific assistant message ---
                    pdf_bytes_for_this_message = message_data.get("pdf_report_bytes")
                    is_welcome_message = (st.session_state.messages.index(message_data) == 0 and 
                                          message_data.get("main_text", "").startswith("Hi there!"))

                    if pdf_bytes_for_this_message and not is_welcome_message:
                        st.markdown('<div class="pdf-button-area">', unsafe_allow_html=True)
                        message_index = st.session_state.messages.index(message_data)
                        st.download_button(
                            label="Download Report", # Single button now
                            data=pdf_bytes_for_this_message,
                            file_name=f"genie_response_{message_index}.pdf",
                            mime="application/pdf",
                            key=f"dl_report_btn_{message_index}" # Unique key for the download button
                        )
                        st.markdown('</div>', unsafe_allow_html=True)

    # The chat input will remain outside the columns to be fixed at the bottom by its CSS
    if prompt := st.chat_input("What is your question for Genie?"):
        with col1: # Ensure user's prompt and thinking indicator are in the correct column
            if not GENIE_SPACE_ID or GENIE_SPACE_ID == 'YOUR_GENIE_SPACE_ID_ENV_NOT_SET':
                st.error("GENIE_SPACE_ID is not configured. Please set it in your environment or .env file.")
            elif not client_initialized or not w:
                st.error("Databricks Workspace Client is not initialized. Cannot send message.")
            else:
                # Append and display user message
                st.session_state.messages.append({"role": "user", "content": prompt})
                # No need to manually display user message here, the history loop will do it on rerun.
                
                # Show thinking indicator (will be replaced by history loop on rerun)
                with st.chat_message("assistant"): # Temporary context for thinking message
                    thinking_placeholder = st.empty()
                    thinking_html = """
                    <div style="display: flex; align-items: center;">
                        <div class="spinner"></div>
                        <div>Thinking...</div>
                    </div>
                    """
                    thinking_placeholder.markdown(thinking_html, unsafe_allow_html=True)
                
                genie_response = ask_genie_question(
                    w_client=w, 
                    space_id_to_use=GENIE_SPACE_ID, 
                    question_text=prompt
                )

                assistant_response_text = genie_response.get("text_response")
                table_html_content = genie_response.get("table_html")
                error_message = genie_response.get("error")
                visualization_info = genie_response.get("visualization_info") 
                additional_texts_from_attachments = genie_response.get("additional_texts", []) 
                query_description_text = genie_response.get("query_description") 
                raw_table_data_for_display = genie_response.get("raw_table_data")

                # Determine the main text for the chat bubble
                main_bubble_text = ""
                if error_message:
                    main_bubble_text = f"**An error occurred:** {error_message}"
                elif table_html_content and query_description_text:
                    main_bubble_text = query_description_text
                    # If original assistant response is different and useful, consider logging or adding to additional_texts
                    if assistant_response_text and assistant_response_text != query_description_text and assistant_response_text not in (additional_texts_from_attachments or []):
                        if not additional_texts_from_attachments: additional_texts_from_attachments = []
                        additional_texts_from_attachments.insert(0, f"Original Genie response: {assistant_response_text}")
                elif assistant_response_text:
                    main_bubble_text = assistant_response_text
                elif table_html_content or raw_table_data_for_display or additional_texts_from_attachments or visualization_info: # If there's some content but no specific text
                    main_bubble_text = "Genie processed your request and provided the following details:"
                else: # Fallback for no specific content at all
                    main_bubble_text = "Genie processed your request but returned no specific content."

                # Prepare data for PDF generation (from the current response)
                pdf_gen_data = {
                    "main_text": main_bubble_text,
                    "original_genie_text_response": assistant_response_text,
                    "query_description": query_description_text,
                    "raw_table_data": raw_table_data_for_display, # This is key for table and charts in PDF
                    # Add other fields if generate_report_pdf uses them directly from message_data
                }
                generated_pdf_bytes = None
                if raw_table_data_for_display: # Only generate PDF if there's actual data for it
                    try:
                        generated_pdf_bytes = generate_report_pdf(pdf_gen_data)
                    except Exception as e_pdf_gen:
                        print(f"[APP_ERROR] PDF generation failed for new message: {e_pdf_gen}")
                        # Optionally, store this error to display to user if PDF download is attempted

                assistant_entry = {
                    "role": "assistant",
                    "main_text": main_bubble_text,
                    "original_genie_text_response": assistant_response_text,
                    "query_description": query_description_text,
                    "table_html": table_html_content,
                    "raw_table_data": raw_table_data_for_display,
                    "additional_texts": additional_texts_from_attachments,
                    "visualization_info": visualization_info,
                    "error_message": error_message,
                    "pdf_report_bytes": generated_pdf_bytes # Store the pre-generated PDF bytes
                }
                st.session_state.messages.append(assistant_entry)
                
                # Clear the thinking placeholder. Streamlit will rerun and the history loop will render the new message.
                thinking_placeholder.empty()
                st.rerun() # Explicitly trigger a rerun to update the display with the new message

    with col2:
        #st.markdown("#### Dashboard") # Title for the dashboard column
        iframe_src = "https://e2-demo-field-eng.cloud.databricks.com/embed/dashboardsv3/01f035ae553919c793b7daba62ef129c?o=1444828305810485"
        # Wrap iframe in a styled container
        iframe_html = f'''<div class="dashboard-iframe-container">
            <iframe
                src="{iframe_src}"
                width="100%"
                height="100%"  # Changed to 100% to fill container
                frameborder="0"
                style="border: none;"> # Removed inline border, style with CSS if needed
            </iframe>
        </div>'''
        st.markdown(iframe_html, unsafe_allow_html=True)