
# Always import get_logger at module level, never conditionally assign
from logger import get_logger

import pandas as pd
import re
from datetime import datetime

def standardize_transactions(df, source, is_credit_card=False):

    logger = get_logger()
    # Accept options dict for compatibility
    if isinstance(source, dict):
        options = source
        source = options.get('source', None)
        is_credit_card = options.get('is_credit_card', False)
    # Defensive: if df is None, return empty DataFrame
    if df is None:
        logger.error("Input DataFrame is None in standardize_transactions.")
        return pd.DataFrame()
    # Defensive: ensure required columns exist
    required_cols = ['date', 'description', 'amount', 'type']
    for col in required_cols:
        if col not in df.columns:
            logger.warning(f"Missing column '{col}' in input DataFrame. Filling with default values.")
            df[col] = '' if col in ['date', 'description', 'type'] else 0.0

    # Standardize date format if possible
    if 'date' in df.columns:
        def parse_date_safe(val):
            try:
                return pd.to_datetime(val, errors='coerce', dayfirst=True).date()
            except Exception:
                return val
        df['date'] = df['date'].apply(parse_date_safe)

    # Parse amount as float and format as currency
    def parse_amount(val):
        try:
            # Remove commas and currency symbols
            val = str(val).replace(',', '').replace('₹', '').strip()
            return float(val)
        except Exception:
            return 0.0
    df['AmountValue'] = df['amount'].apply(parse_amount)
    df['Amount'] = df['AmountValue'].apply(lambda x: f"₹{x:,.2f}")

    # Map account type
    def map_account_type(row):
        if is_credit_card:
            return "CreditCard"
        # You can add more mappings if needed
        return "BankAccount"
    df['AccountType'] = df.apply(map_account_type, axis=1)

    # Add metadata columns
    df['source'] = source
    df['is_credit_card'] = is_credit_card

    logger.info(f"Standardized {len(df)} transactions for source={source}, is_credit_card={is_credit_card}")
    return df
