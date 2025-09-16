import re
import pandas as pd
from .base_parser import BaseParser
from src.logger import get_logger

from src.standardizer import standardize_transactions

class AxisBankStatementParser(BaseParser):
    """Parser for Axis Bank statements"""
    def __init__(self, file_path):
        super().__init__(file_path)
        self.transactions = []
        self.logger = get_logger()

    def parse(self) -> pd.DataFrame:
        import os
        file_ext = os.path.splitext(self.file_path)[-1].lower()
        txt_path = self.file_path
        if file_ext == '.pdf':
            import pdfplumber
            txt_path = self.file_path.replace('.pdf', '_extracted.txt')
            all_text = ''
            with pdfplumber.open(self.file_path) as pdf:
                for page in pdf.pages:
                    all_text += page.extract_text() + '\n'
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(all_text)
        with open(txt_path, 'r', encoding='utf-8') as f:
            text = f.read()
        lines = text.split('\n')
        self.logger.info(f"[DEBUG] Total lines read: {len(lines)} from {txt_path}")
        for line in lines:
            line = line.strip()
            date_match = re.match(r'^(\d{2}-\d{2}-\d{4})', line)
            if date_match:
                date = date_match.group(1)
                parts = line.split()
                withdrawal = None
                deposit = None
                balance = None
                amounts = []
                for part in parts:
                    clean_part = part.replace(',', '')
                    if re.match(r'^\d+\.?\d*$', clean_part):
                        amounts.append(float(clean_part))
                if len(amounts) >= 2:
                    if len(amounts) == 3:
                        withdrawal, deposit, balance = amounts
                    elif len(amounts) == 2:
                        deposit, balance = amounts
                    else:
                        balance = amounts[-1]
                desc_parts = []
                for part in parts[1:]:
                    if not re.match(r'^\d{1,3}(?:,\d{3})*\.?\d*$', part.replace(',', '')):
                        desc_parts.append(part)
                    else:
                        break
                description = ' '.join(desc_parts)
                if withdrawal and withdrawal > 0:
                    self.transactions.append({
                        'date': date,
                        'description': description,
                        'amount': -withdrawal,
                        'type': 'Debit',
                        'balance': balance
                    })
                if deposit and deposit > 0:
                    self.transactions.append({
                        'date': date,
                        'description': description,
                        'amount': deposit,
                        'type': 'Credit',
                        'balance': balance
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
        df = standardize_transactions(df, source="Axis Bank", is_credit_card=False)
        return df
