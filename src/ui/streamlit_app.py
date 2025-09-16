import streamlit as st
import os
import pandas as pd
import json
import shutil
from datetime import datetime, timedelta
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)))
from src.logger import get_logger
from src.config_loader import get_config
from src.parser import parse_statement
from src.standardizer import standardize_transactions
from src.io_utils import save_to_processed
from src.analyzer import analyze_finances
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

logger = get_logger()
config = get_config()

PROCESSED_DIR = config['data']['processed_dir']
REPORTS_DIR = os.path.join(PROCESSED_DIR, 'reports')
TEMP_RAW_DIR = 'data/temp_raw'

os.makedirs(TEMP_RAW_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

st.set_page_config(layout="wide", page_title="Personal Finance Analyzer", page_icon="💰")

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .trend-positive {
        color: #28a745;
    }
    .trend-negative {
        color: #dc3545;
    }
    .sidebar-section {
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-header">💰 Personal Finance Analyzer</h1>', unsafe_allow_html=True)

# --- Sidebar Options ---
st.sidebar.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
st.sidebar.header("📊 Analysis Options")
run_analysis = st.sidebar.checkbox("Run Analysis", value=True, help="Generate financial reports and plots.")
run_combine = st.sidebar.checkbox("Combine Statements", value=False, help="Combine all uploaded statements into one processed file.")
show_trends = st.sidebar.checkbox("Show Trend Analysis", value=True, help="Display advanced trend visualizations and insights.")
output_format = st.sidebar.radio("Output Format", ("csv", "parquet"), help="Choose the format for processed transaction files.")
st.sidebar.markdown('</div>', unsafe_allow_html=True)

# --- Date Range Filter ---
st.sidebar.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
st.sidebar.header("📅 Date Range Filter")
date_filter_enabled = st.sidebar.checkbox("Enable Date Filter", value=False)
if date_filter_enabled:
    start_date = st.sidebar.date_input("Start Date", value=datetime.now() - timedelta(days=90))
    end_date = st.sidebar.date_input("End Date", value=datetime.now())
st.sidebar.markdown('</div>', unsafe_allow_html=True)

# --- Category Filter ---
st.sidebar.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
st.sidebar.header("🏷️ Category Filter")
category_filter_enabled = st.sidebar.checkbox("Enable Category Filter", value=False)
if category_filter_enabled:
    selected_categories = st.sidebar.multiselect(
        "Select Categories",
        ["Food", "Travel", "Shopping", "Entertainment", "Fuel", "Bills", "Other"],
        default=["Food", "Travel", "Shopping", "Entertainment", "Fuel", "Bills", "Other"]
    )
st.sidebar.markdown('</div>', unsafe_allow_html=True)

def create_spending_trend_chart(df):
    if df.empty or 'date' not in df.columns or 'AmountValue' not in df.columns:
        return None
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.dropna(subset=['date'])
    daily_spending = df.groupby(df['date'].dt.date)['AmountValue'].sum().reset_index()
    daily_spending.columns = ['Date', 'Amount']
    fig = px.line(daily_spending, x='Date', y='Amount', title='Daily Spending Trend', labels={'Amount': 'Amount (₹)', 'Date': 'Date'})
    fig.update_layout(xaxis_title="Date", yaxis_title="Amount (₹)", hovermode='x unified', showlegend=False)
    return fig

def create_category_pie_chart(df):
    if df.empty or 'category' not in df.columns or 'AmountValue' not in df.columns:
        return None
    category_spending = df.groupby('category')['AmountValue'].sum().reset_index()
    category_spending = category_spending[category_spending['AmountValue'] > 0]
    fig = px.pie(category_spending, values='AmountValue', names='category', title='Spending by Category')
    fig.update_traces(textposition='inside', textinfo='percent+label')
    return fig

def create_monthly_comparison_chart(df):
    if df.empty or 'date' not in df.columns or 'AmountValue' not in df.columns:
        return None
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.dropna(subset=['date'])
    df['month'] = df['date'].dt.to_period('M')
    monthly_spending = df.groupby('month')['AmountValue'].sum().reset_index()
    monthly_spending['month_str'] = monthly_spending['month'].astype(str)
    fig = px.bar(monthly_spending, x='month_str', y='AmountValue', title='Monthly Spending Comparison', labels={'AmountValue': 'Amount (₹)', 'month_str': 'Month'})
    fig.update_layout(xaxis_title="Month", yaxis_title="Amount (₹)")
    return fig

def create_income_vs_expense_chart(df):
    if df.empty or 'type' not in df.columns or 'AmountValue' not in df.columns:
        return None
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.dropna(subset=['date'])
    income_df = df[df['type'].str.contains('Credit|Deposit', case=False, na=False)]
    expense_df = df[df['type'].str.contains('Debit|Withdrawal', case=False, na=False)]
    income_df['month'] = income_df['date'].dt.to_period('M')
    expense_df['month'] = expense_df['date'].dt.to_period('M')
    monthly_income = income_df.groupby('month')['AmountValue'].sum().reset_index()
    monthly_expense = expense_df.groupby('month')['AmountValue'].sum().reset_index()
    fig = make_subplots(rows=1, cols=1, subplot_titles=['Income vs Expenses'])
    if not monthly_income.empty:
        fig.add_trace(go.Bar(x=monthly_income['month'].astype(str), y=monthly_income['AmountValue'], name='Income', marker_color='green'))
    if not monthly_expense.empty:
        fig.add_trace(go.Bar(x=monthly_expense['month'].astype(str), y=monthly_expense['AmountValue'], name='Expenses', marker_color='red'))
    fig.update_layout(title='Monthly Income vs Expenses', xaxis_title='Month', yaxis_title='Amount (₹)', barmode='group')
    return fig

def display_key_metrics(df):
    if df.empty:
        return
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        total_transactions = len(df)
        st.metric("Total Transactions", total_transactions)
    with col2:
        if 'AmountValue' in df.columns:
            total_amount = df['AmountValue'].sum()
            st.metric("Total Amount", f"₹{total_amount:,.2f}")
    with col3:
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            date_range = df['date'].max() - df['date'].min()
            st.metric("Date Range", f"{date_range.days} days")
    with col4:
        if 'AmountValue' in df.columns:
            avg_transaction = df['AmountValue'].mean()
            st.metric("Avg Transaction", f"₹{avg_transaction:,.2f}")

def apply_filters(df):
    filtered_df = df.copy()
    if date_filter_enabled and 'date' in filtered_df.columns:
        filtered_df['date'] = pd.to_datetime(filtered_df['date'], errors='coerce')
        filtered_df = filtered_df[(filtered_df['date'].dt.date >= start_date) & (filtered_df['date'].dt.date <= end_date)]
    if category_filter_enabled and 'category' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['category'].isin(selected_categories)]
    return filtered_df

# --- File Uploader ---
st.header("📁 Upload Statements")
uploaded_files = st.file_uploader("Upload your bank/credit card statements (PDF, TXT, CSV)", type=["pdf", "txt", "csv"], accept_multiple_files=True)

if uploaded_files:
    st.subheader("⚙️ Processing Uploaded Files...")
    all_processed_dfs = []
    processed_file_paths = []
    report_file_paths = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    for idx, uploaded_file in enumerate(uploaded_files):
        file_name = uploaded_file.name
        temp_file_path = os.path.join(TEMP_RAW_DIR, file_name)
        progress = (idx + 1) / len(uploaded_files)
        progress_bar.progress(progress)
        status_text.text(f"Processing {file_name}...")
        try:
            with open(temp_file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.info(f"Saved {file_name} to temporary path: {temp_file_path}")
            df = None
            metadata = {}
            if file_name.lower().endswith('.csv'):
                df = pd.read_csv(temp_file_path)
                metadata = {"source": "CSV_Upload", "is_credit_card": False, "parser": "CSVParser"}
                df = standardize_transactions(df, metadata)
            elif file_name.lower().endswith(('.pdf', '.txt')):
                parsed_df, parsed_metadata = parse_statement(temp_file_path)
                df = parsed_df
                metadata = parsed_metadata
            if df is not None and not df.empty:
                processed_save_path = save_to_processed(df, metadata.get('source', 'Unknown'), file_name, format=output_format, processed_dir=PROCESSED_DIR, original_path=temp_file_path)
                processed_file_paths.append(processed_save_path)
                all_processed_dfs.append(df)
                st.success(f"✅ Successfully processed: {file_name}")
                if run_analysis:
                    bank = metadata.get('source', 'unknown').lower().replace(' ', '_')
                    month = datetime.now().strftime('%m')
                    if 'date' in df.columns and not df['date'].empty:
                        try:
                            df['date'] = pd.to_datetime(df['date'], errors='coerce')
                            earliest_date = df['date'].min()
                            if pd.notna(earliest_date):
                                month = earliest_date.strftime('%m')
                        except Exception as e:
                            logger.warning(f"Could not determine month from dates for {file_name}: {e}")
                    report_name = f"{bank}_{month}"
                    summary = analyze_finances(df, output_dir=REPORTS_DIR, save_plots=True, name=report_name)
                    with st.expander(f"📊 Analysis Results for {file_name}"):
                        st.json(summary)
                        report_json_path = os.path.join(REPORTS_DIR, f"{report_name}.json")
                        if os.path.exists(report_json_path):
                            st.download_button(label=f"Download {report_name}.json", data=open(report_json_path, "rb").read(), file_name=f"{report_name}.json", mime="application/json")
                            report_file_paths.append(report_json_path)
                        generated_files = [f for f in os.listdir(REPORTS_DIR) if f.startswith(report_name) and (f.endswith('.csv') or f.endswith('.png'))]
                        for gen_file in generated_files:
                            file_path = os.path.join(REPORTS_DIR, gen_file)
                            mime_type = "text/csv" if gen_file.endswith('.csv') else "image/png"
                            st.download_button(label=f"Download {gen_file}", data=open(file_path, "rb").read(), file_name=gen_file, mime=mime_type)
                            report_file_paths.append(file_path)
            else:
                st.warning(f"⚠️ No transactions found for {file_name}")
        except Exception as e:
            logger.exception(f"Error processing {file_name}")
            st.error(f"❌ Failed to process {file_name}: {e}")
    progress_bar.empty()
    status_text.empty()

            


    # --- Combine Statements --- 
    if run_combine and all_processed_dfs:
        st.subheader("Combined Statement Analysis")
        combined_df = pd.concat(all_processed_dfs, ignore_index=True)
        # Dedupe by transaction id if present (assuming 'transaction_id' is a column after standardization)
        if 'transaction_id' in combined_df.columns:
            combined_df = combined_df.drop_duplicates(subset=['transaction_id'])
        
        combined_filename = f"combined_statements.{output_format}"
        combined_save_path = save_to_processed(combined_df, "Combined", 
                                                combined_filename, format=output_format, 
                                                processed_dir=PROCESSED_DIR)
        processed_file_paths.append(combined_save_path)
        st.success(f"All statements combined and saved to: {combined_save_path}")

        if run_analysis:
            report_name = "combined_all_statements"
            combined_summary = analyze_finances(combined_df, output_dir=REPORTS_DIR, save_plots=True, name=report_name)
            st.json(combined_summary)
            st.success("Combined analysis report generated.")

            st.markdown("**Downloadable Reports for Combined Statements:**")
            report_json_path = os.path.join(REPORTS_DIR, f"{report_name}.json")
            if os.path.exists(report_json_path):
                st.download_button(label=f"Download {report_name}.json", 
                                   data=open(report_json_path, "rb").read(), 
                                   file_name=f"{report_name}.json", 
                                   mime="application/json")
                report_file_paths.append(report_json_path)
            
            generated_files = [f for f in os.listdir(REPORTS_DIR) if f.startswith(report_name) and (f.endswith('.csv') or f.endswith('.png'))]
            for gen_file in generated_files:
                file_path = os.path.join(REPORTS_DIR, gen_file)
                mime_type = "text/csv" if gen_file.endswith('.csv') else "image/png"
                st.download_button(label=f"Download {gen_file}", 
                                   data=open(file_path, "rb").read(), 
                                   file_name=gen_file, 
                                   mime=mime_type)
                report_file_paths.append(file_path)

    # --- Show Processed Preview ---
    if all_processed_dfs:
        st.subheader("Processed Transactions Preview")
        preview_df = pd.concat(all_processed_dfs, ignore_index=True)
        st.dataframe(preview_df)

    st.subheader("Summary of Processed Files")
    if processed_file_paths:
        st.markdown("**Processed Transaction Files:**")
        for pfp in processed_file_paths:
            st.markdown(f"- `{pfp}`")
    if report_file_paths:
        st.markdown("**Generated Report Files:**")
        for rfp in report_file_paths:
            st.markdown(f"- `{rfp}`")

    # Clean up temporary raw files
    st.subheader("Cleanup")
    if st.button("Clean up temporary uploaded files"):
        shutil.rmtree(TEMP_RAW_DIR)
        os.makedirs(TEMP_RAW_DIR, exist_ok=True)
        st.success("Temporary uploaded files cleaned up.")

else:
    st.info("Please upload your financial statements to get started.")


