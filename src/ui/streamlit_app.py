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


# Enhanced Custom CSS for modern look
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        letter-spacing: 2px;
    }
    .sidebar-logo {
        text-align: center;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background: linear-gradient(90deg, #e3f2fd 0%, #f0f2f6 100%);
        padding: 1.2rem;
        border-radius: 0.7rem;
        border-left: 6px solid #1f77b4;
        box-shadow: 0 2px 8px rgba(31,119,180,0.07);
        margin-bottom: 1rem;
    }
    .trend-positive {
        color: #28a745;
        font-weight: bold;
    }
    .trend-negative {
        color: #dc3545;
        font-weight: bold;
    }
    .sidebar-section {
        margin-bottom: 2rem;
    }
    .stExpander > div[role='button'] {
        background: #e3f2fd;
        color: #1f77b4;
        font-weight: bold;
        border-radius: 0.5rem;
    }
    .stExpander > div[role='button']:hover {
        background: #bbdefb;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-header">💰 Personal Finance Analyzer</h1>', unsafe_allow_html=True)

# Welcome message with instructions
st.markdown("""
## 🚀 Welcome to Personal Finance Analyzer

This enhanced application helps you analyze your financial statements with advanced trend visualization and insights.

### 📋 Features:
- **Multi-format Support**: Upload PDF, TXT, or CSV files
- **Trend Analysis**: Interactive charts and visualizations
- **Smart Filtering**: Filter by date range and categories
- **AI Insights**: Get intelligent financial insights
- **Export Options**: Download processed data and reports

### 🎯 Getting Started:
1. Configure your analysis options in the sidebar
2. Upload your bank/credit card statements
3. View real-time processing and analysis
4. Explore trends and download reports

**Ready to analyze your finances? Upload your statements ! 📈**
""")
st.sidebar.markdown('<div class="sidebar-logo"><img src="https://img.icons8.com/color/96/000000/money.png" width="64"/><br><b>Personal Finance</b></div>', unsafe_allow_html=True)

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
        st.markdown(f'<div class="metric-card"><span style="font-size:1.2rem;">🧾</span><br><b>Total Transactions</b><br><span style="font-size:1.5rem;">{total_transactions}</span></div>', unsafe_allow_html=True)
    with col2:
        if 'AmountValue' in df.columns:
            total_amount = df['AmountValue'].sum()
            st.markdown(f'<div class="metric-card"><span style="font-size:1.2rem;">💸</span><br><b>Total Amount</b><br><span style="font-size:1.5rem;">₹{total_amount:,.2f}</span></div>', unsafe_allow_html=True)
    with col3:
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            date_range = df['date'].max() - df['date'].min()
            st.markdown(f'<div class="metric-card"><span style="font-size:1.2rem;">📅</span><br><b>Date Range</b><br><span style="font-size:1.5rem;">{date_range.days} days</span></div>', unsafe_allow_html=True)
    with col4:
        if 'AmountValue' in df.columns:
            avg_transaction = df['AmountValue'].mean()
            st.markdown(f'<div class="metric-card"><span style="font-size:1.2rem;">📊</span><br><b>Avg Transaction</b><br><span style="font-size:1.5rem;">₹{avg_transaction:,.2f}</span></div>', unsafe_allow_html=True)

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

    # --- Trend Analysis Section ---
    if all_processed_dfs:
        st.header("📈 Trend Analysis & Insights")
        trend_df = pd.concat(all_processed_dfs, ignore_index=True)
        trend_df = apply_filters(trend_df)
        if not trend_df.empty:
            st.subheader("🎯 Key Metrics")
            display_key_metrics(trend_df)
            col1, col2 = st.columns(2)
            with col1:
                spending_chart = create_spending_trend_chart(trend_df)
                if spending_chart:
                    st.plotly_chart(spending_chart, use_container_width=True)
                monthly_chart = create_monthly_comparison_chart(trend_df)
                if monthly_chart:
                    st.plotly_chart(monthly_chart, use_container_width=True)
            with col2:
                category_chart = create_category_pie_chart(trend_df)
                if category_chart:
                    st.plotly_chart(category_chart, use_container_width=True)
                income_expense_chart = create_income_vs_expense_chart(trend_df)
                if income_expense_chart:
                    st.plotly_chart(income_expense_chart, use_container_width=True)
            st.subheader("💡 AI-Powered Insights")
            if 'category' in trend_df.columns and 'AmountValue' in trend_df.columns:
                top_category = trend_df.groupby('category')['AmountValue'].sum().idxmax()
                top_amount = trend_df.groupby('category')['AmountValue'].sum().max()
                avg_daily = trend_df['AmountValue'].sum() / max(1, len(trend_df['date'].dt.date.unique()) if 'date' in trend_df.columns else 1)
                recent_trend = None
                if len(trend_df) > 1:
                    recent_trend = "📈 <span class='trend-positive'>Increasing</span>" if trend_df['AmountValue'].tail(10).mean() > trend_df['AmountValue'].head(10).mean() else "📉 <span class='trend-negative'>Decreasing</span>"
                st.markdown(f"""
                <div style='display:flex;gap:1rem;'>
                    <div class='metric-card' style='flex:1;'>🏆 <b>Top Category</b><br>{top_category}: ₹{top_amount:,.2f}</div>
                    <div class='metric-card' style='flex:1;'>📊 <b>Avg Daily Spend</b><br>₹{avg_daily:,.2f}</div>
                    <div class='metric-card' style='flex:1;'>📈 <b>Recent Trend</b><br>{recent_trend if recent_trend else ''}</div>
                </div>
                """, unsafe_allow_html=True)

    # --- Combine Statements --- 
    if run_combine and all_processed_dfs:
        st.subheader("Combined Statement Analysis")
        combined_df = pd.concat(all_processed_dfs, ignore_index=True)
        if 'transaction_id' in combined_df.columns:
            combined_df = combined_df.drop_duplicates(subset=['transaction_id'])
        combined_filename = f"combined_statements.{output_format}"
        combined_save_path = save_to_processed(combined_df, "Combined", combined_filename, format=output_format, processed_dir=PROCESSED_DIR)
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
                st.download_button(label=f"Download {report_name}.json", data=open(report_json_path, "rb").read(), file_name=f"{report_name}.json", mime="application/json")
                report_file_paths.append(report_json_path)
            generated_files = [f for f in os.listdir(REPORTS_DIR) if f.startswith(report_name) and (f.endswith('.csv') or f.endswith('.png'))]
            for gen_file in generated_files:
                file_path = os.path.join(REPORTS_DIR, gen_file)
                mime_type = "text/csv" if gen_file.endswith('.csv') else "image/png"
                st.download_button(label=f"Download {gen_file}", data=open(file_path, "rb").read(), file_name=gen_file, mime=mime_type)
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
    st.subheader("📈 Example Trend Analysis")
    # Show a placeholder chart for trend analysis before upload
    import numpy as np
    import plotly.express as px
    dates = pd.date_range(datetime.now() - timedelta(days=30), periods=30)
    amounts = np.random.normal(loc=5000, scale=1500, size=30).clip(0)
    example_df = pd.DataFrame({"Date": dates, "Amount": amounts})
    fig = px.line(example_df, x="Date", y="Amount", title="Example Daily Spending Trend", labels={"Amount": "Amount (₹)", "Date": "Date"})
    fig.update_layout(xaxis_title="Date", yaxis_title="Amount (₹)", hovermode='x unified', showlegend=False)
    st.plotly_chart(fig, use_container_width=True)


