
import pandas as pd
import matplotlib.pyplot as plt
import os

def analyze_finances(df, output_dir=None, save_plots=True, name="report"):

    # Accept base_name param for output naming
    if name is None:
        name = "report"

    # Use AccountType column to separate
    bank_df = df[df.get('AccountType', '') == 'BankAccount'] if 'AccountType' in df.columns else df
    cc_df = df[df.get('AccountType', '') == 'CreditCard'] if 'AccountType' in df.columns else pd.DataFrame()

    # --- Bank analysis ---
    bank_income = bank_df[bank_df['type'].str.lower().isin(['credit', 'refund/payment', 'in'])]['amount'].sum() if not bank_df.empty else 0.0
    bank_expenses = bank_df[bank_df['type'].str.lower().isin(['debit', 'expense', 'out'])]['amount'].sum() if not bank_df.empty else 0.0
    bank_savings = bank_income - bank_expenses
    bank_net_cash_flow = bank_income - bank_expenses
    # Monthly breakdown
    if not bank_df.empty:
        bank_df['month'] = pd.to_datetime(bank_df['date'], errors='coerce').dt.to_period('M')
        monthly = bank_df.groupby('month').agg({'amount': ['sum'], 'type': lambda x: (x.str.lower() == 'debit').sum()})
        # Top 5 spending categories
        top_categories = bank_df[bank_df['type'].str.lower().isin(['debit', 'expense', 'out'])].groupby('category')['amount'].sum().sort_values(ascending=False).head(5)
        # Recurring payments
        recurring = bank_df[bank_df['type'].str.lower().isin(['debit', 'expense', 'out'])].groupby(['description', 'category']).size()
        recurring = recurring[recurring > 2].sort_values(ascending=False)
        # Monthly trend plot
        df_monthly = bank_df.copy()
        df_monthly['income'] = df_monthly['amount'].where(df_monthly['type'].str.lower().isin(['credit', 'refund/payment', 'in']), 0)
        df_monthly['expense'] = df_monthly['amount'].where(df_monthly['type'].str.lower().isin(['debit', 'expense', 'out']), 0)
        monthly_trend = df_monthly.groupby('month').agg({'income': 'sum', 'expense': 'sum'})
    else:
        monthly = pd.DataFrame()
        top_categories = pd.Series(dtype=float)
        recurring = pd.Series(dtype=int)
        monthly_trend = pd.DataFrame()

    # --- Credit Card analysis ---
    if not cc_df.empty:
        cc_df['month'] = pd.to_datetime(cc_df['date'], errors='coerce').dt.to_period('M')
        total_spend_by_category = cc_df.groupby('category')['amount'].sum().sort_values(ascending=False)
        payments = cc_df[cc_df['type'].str.lower().isin(['credit', 'refund/payment', 'in'])]['amount'].sum()
        expenses = cc_df[cc_df['type'].str.lower().isin(['debit', 'expense', 'out'])]['amount'].sum()
        average_monthly_spend = expenses / max(1, len(cc_df['month'].unique()))
    else:
        total_spend_by_category = pd.Series(dtype=float)
        payments = 0.0
        expenses = 0.0
        average_monthly_spend = 0.0

    # Save outputs if output_dir is provided
    if output_dir is not None:
        os.makedirs(output_dir, exist_ok=True)
        # Bank outputs
        if not monthly_trend.empty:
            monthly_trend.to_csv(os.path.join(output_dir, f"{name}_bank_monthly.csv"))
        if not top_categories.empty:
            top_categories.to_frame().to_csv(os.path.join(output_dir, f"{name}_bank_top_categories.csv"))
        if not monthly_trend.empty:
            plt.figure(figsize=(10,5))
            plt.plot(monthly_trend.index.astype(str), monthly_trend['income'], label='Income', marker='o')
            plt.plot(monthly_trend.index.astype(str), monthly_trend['expense'], label='Expense', marker='o')
            plt.title('Bank Monthly Income vs Expense')
            plt.xlabel('Month')
            plt.ylabel('Amount (INR)')
            plt.legend()
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, f"{name}_bank_monthly_trend.png"))
            plt.close()
        # Credit card outputs
        if not total_spend_by_category.empty:
            total_spend_by_category.to_frame().to_csv(os.path.join(output_dir, f"{name}_cc_spend_by_category.csv"))
        if not cc_df.empty:
            cc_monthly = cc_df.groupby('month').agg({'amount': 'sum'})
            cc_monthly.to_csv(os.path.join(output_dir, f"{name}_cc_monthly.csv"))
            plt.figure(figsize=(10,5))
            plt.plot(cc_monthly.index.astype(str), cc_monthly['amount'], label='CC Spend', marker='o')
            plt.title('Credit Card Monthly Spend')
            plt.xlabel('Month')
            plt.ylabel('Amount (INR)')
            plt.legend()
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, f"{name}_cc_monthly_trend.png"))
            plt.close()

    # Always return JSON-serializable dict
    def convert_keys_to_str(obj):
        if isinstance(obj, dict):
            return {str(k): convert_keys_to_str(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_keys_to_str(v) for v in obj]
        else:
            return obj

    def df_to_dict_safe(df):
        if hasattr(df, 'to_dict'):
            d = df.to_dict()
            return convert_keys_to_str(d)
        return convert_keys_to_str(df)

    summary = {
        'bank': {
            'total_income': round(bank_income, 2),
            'total_expenses': round(bank_expenses, 2),
            'total_savings': round(bank_savings, 2),
            'net_cash_flow': round(bank_net_cash_flow, 2),
            'monthly_breakdown': df_to_dict_safe(monthly_trend),
            'top_5_spending_categories': df_to_dict_safe(top_categories),
            'recurring_payments': df_to_dict_safe(recurring)
        },
        'credit_card': {
            'total_spend_by_category': df_to_dict_safe(total_spend_by_category),
            'payments': round(payments, 2),
            'average_monthly_spend': round(average_monthly_spend, 2)
        }
    }
    return summary
