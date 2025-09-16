
from src.standardizer import standardize_transactions
from src.logger import get_logger

import re
import pandas as pd
from .base_parser import BaseParser

class AmexCreditCardParser(BaseParser):
    """Parser for American Express credit card statements"""
    def __init__(self, file_path):
        super().__init__(file_path)
        self.transactions = []
        self.logger = get_logger()
    def parse(self):
        import os
        file_ext = os.path.splitext(self.file_path)[-1].lower()
        txt_path = self.file_path
        if file_ext == '.pdf':
            import pdfplumber
            txt_path = self.file_path.replace('.pdf', '_extracted.txt')
            with pdfplumber.open(self.file_path) as pdf:
                all_text = ''
                for page in pdf.pages:
                    all_text += page.extract_text() + '\n'
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(all_text)
        with open(txt_path, 'r', encoding='utf-8') as f:
            text = f.read()
        lines = text.split('\n')
        self.logger.info(f"[DEBUG] Total lines read: {len(lines)} from {txt_path}")
        # Extract year from filename if possible
        import os
        year = None
        filename = os.path.basename(self.file_path)
        year_match = re.search(r'(\d{4})', filename)
        if year_match:
            year = year_match.group(1)
        else:
            year = str(pd.Timestamp.today().year)
        for line in lines:
            line = line.strip()
            date_match = re.match(r'^([A-Za-z]+) (\d{1,2})', line)
            if date_match:
                month_str = date_match.group(1)
                day_str = date_match.group(2)
                # Convert month name to month number
                try:
                    month_num = pd.to_datetime(month_str, format='%B').month
                except:
                    try:
                        month_num = pd.to_datetime(month_str, format='%b').month
                    except:
                        month_num = 8  # fallback to August
                date = f"{year}-{month_num:02d}-{int(day_str):02d}"
                parts = line.split()
                if len(parts) >= 3:
                    amount_match = re.search(r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(Cr\.?)?$', line)
                    if amount_match:
                        amount_str = amount_match.group(1).replace(',', '')
                        amount = float(amount_str)
                        if amount_match.group(2):
                            transaction_type = 'Credit'
                            amount = -amount
                        else:
                            transaction_type = 'Debit'
                        desc_start = len(date_match.group(0))
                        desc_end = line.rfind(amount_match.group(0))
                        description = line[desc_start:desc_end].strip()
                        self.transactions.append({
                            'date': date,
                            'description': description,
                            'amount': amount,
                            'type': transaction_type
                        })
        df = pd.DataFrame(self.transactions)
        # Defensive: ensure required columns exist
        required_cols = ['date', 'description', 'amount', 'type']
        for col in required_cols:
            if col not in df.columns:
                df[col] = '' if col in ['date', 'description', 'type'] else 0.0
        def clean_desc(desc):
            import re
            desc = str(desc).strip().lower()
            desc = re.sub(r'[^a-z0-9 ]', '', desc)
            return desc
        df['description_clean'] = df['description'].apply(clean_desc)
        def categorize(desc):
            if 'zomato' in desc:
                return 'Food'
            if 'uber' in desc:
                return 'Travel'
            if 'amazon' in desc:
                return 'Shopping'
            if 'fuel' in desc or 'petrol' in desc:
                return 'Fuel'
            if 'swiggy' in desc:
                return 'Food'
            if 'bookmyshow' in desc:
                return 'Entertainment'

            if 'bata' in desc:
                return 'Shopping'
            if 'gwalia sweets' in desc:
                return 'Food'
            if 'shoppers stop' in desc:
                return 'Shopping'
            if 'infiniti payment' in desc:
                return 'Payment'
            return 'Other'
        df['category'] = df['description_clean'].apply(categorize)
        metadata = {
            'source': 'Amex_CreditCard',
            'is_credit_card': True,
            'parser': 'AmexCreditCardParser'
        }

        df = standardize_transactions(df, metadata)
        return df, metadata
