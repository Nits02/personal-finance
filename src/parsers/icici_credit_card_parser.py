from src.logger import get_logger
import re
import pandas as pd
from .base_parser import BaseParser

from src.standardizer import standardize_transactions

class ICICICreditCardParser(BaseParser):
    """Parser for ICICI Credit Card statements"""
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
            with pdfplumber.open(self.file_path) as pdf:
                all_text = ''
                for page in pdf.pages:
                    all_text += page.extract_text() + '\n'
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(all_text)
        with open(txt_path, 'r', encoding='utf-8') as f:
            text = f.read()
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        self.logger.info(f"[DEBUG] Total lines read: {len(lines)} from {txt_path}")
        for idx, line in enumerate(lines):
            self.logger.debug(f"Line {idx}: {line}")
        transactions = []
        i = 0
        while i < len(lines):
            tx_match = re.match(r'^(\d{2}-\d{2}-\d{4})\s+(.+?)\s+(\d+[,.]*\d*)\s*(Dr\.|Cr\.)\s*(\d{8,})$', lines[i])
            if tx_match:
                date = tx_match.group(1)
                description = tx_match.group(2)
                amount = float(tx_match.group(3).replace(',', ''))
                transaction_type = 'Credit' if tx_match.group(4) == 'Cr.' else 'Debit'
                if transaction_type == 'Credit':
                    amount = -amount
                ref_number = tx_match.group(5)
                desc_lines = [description]
                j = i + 1
                while j < len(lines) and not re.match(r'^(\d{2}-\d{2}-\d{2,4})', lines[j]):
                    desc_lines.append(lines[j])
                    j += 1
                full_description = ' '.join(desc_lines).strip()
                print(f"DEBUG: Matched transaction: date={date}, description={full_description}, amount={amount}, type={transaction_type}, reference={ref_number}")
                transactions.append({
                    'date': date,
                    'description': full_description,
                    'amount': amount,
                    'type': transaction_type,
                    'reference': ref_number
                })
                i = j
            else:
                i += 1
        df = pd.DataFrame(transactions)
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
            'source': 'ICICI_CreditCard',
            'is_credit_card': True,
            'parser': 'ICICICreditCardParser'
        }
        df = standardize_transactions(df, metadata)
        return df, metadata
