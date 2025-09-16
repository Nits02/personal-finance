
import re
import pandas as pd
import os

try:
    from .base_parser import BaseParser
except ImportError:
    from src.parsers.base_parser import BaseParser

# Always import get_logger at module level, never conditionally assign
from src.logger import get_logger
from src.standardizer import standardize_transactions

class ICICISavingsBankStatementParser(BaseParser):
    """Parser for ICICI Savings Account statements"""
    def __init__(self, file_path):
        super().__init__(file_path)
        self.transactions = []
        self.logger = get_logger()

    def parse(self) -> pd.DataFrame:
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
            lines = [line.strip() for line in f if line.strip()]
        self.logger.info(f"[DEBUG] Total lines read: {len(lines)} from {txt_path}")
        # Group lines into transaction blocks
        transactions = []
        block = []
        for idx, line in enumerate(lines):
            self.logger.debug(f"Line {idx}: {line}")
            if re.match(r'^\d{2}-\d{2}-\d{4}', line):
                if block:
                    transactions.append(' '.join(block))
                    block = []
                block.append(line)
            else:
                if block:
                    block.append(line)
        if block:
            transactions.append(' '.join(block))
        print(f"[DEBUG] Total transaction blocks: {len(transactions)}")
        for idx, entry in enumerate(transactions[:10]):
            print(f"[DEBUG] Block {idx}: {entry}")
        # Parse each transaction block
        self.transactions = []
        for entry in transactions:
            print(f"[DEBUG] Parsing block: {entry}")
            parts = entry.split()
            date_match = re.match(r'^(\d{2}-\d{2}-\d{4})', entry)
            if not date_match:
                print(f"[DEBUG] No date match for block: {entry}")
                continue
            date = date_match.group(1)
            deposit = None
            withdrawal = None
            balance = None
            amounts = []
            for part in parts:
                clean_part = part.replace(',', '')
                if re.match(r'^\d+\.?\d*$', clean_part):
                    amounts.append(float(clean_part))
            print(f"[DEBUG] Amounts found: {amounts}")
            if len(amounts) >= 2:
                if len(amounts) == 3:
                    deposit, withdrawal, balance = amounts
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
            print(f"[DEBUG] Parsed: date={date}, description={description}, deposit={deposit}, withdrawal={withdrawal}, balance={balance}")
            if deposit and deposit > 0:
                self.transactions.append({
                    'date': date,
                    'description': description,
                    'amount': deposit,
                    'type': 'Credit',
                    'balance': balance
                })
            if withdrawal and withdrawal > 0:
                self.transactions.append({
                    'date': date,
                    'description': description,
                    'amount': -withdrawal,
                    'type': 'Debit',
                    'balance': balance
                })
        df = pd.DataFrame(self.transactions)
        # Defensive: ensure required columns exist
        required_cols = ['date', 'description', 'amount', 'type']
        for col in required_cols:
            if col not in df.columns:
                df[col] = '' if col in ['date', 'description', 'type'] else 0.0
        # Clean description
        def clean_desc(desc):
            import re
            desc = str(desc).strip().lower()
            desc = re.sub(r'[^a-z0-9 ]', '', desc)
            return desc
        df['description_clean'] = df['description'].apply(clean_desc)
        # Categorization rules
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
        # Standardize output schema
        try:

            metadata = {"source": "ICICI Bank", "is_credit_card": False}
            df = standardize_transactions(df, metadata)
        except ImportError:
            pass
        return df

if __name__ == "__main__":
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        from base_parser import BaseParser
    except ImportError:
        pass
    test_file = "data/raw/2025/08/icici/bank/icici_bank_extracted.txt"
    parser = ICICISavingsBankStatementParser(test_file)
    df = parser.parse()
    print(df)
    # Print one full row with all columns for validation
    if not df.empty:
        print("\nSample row with all columns:")
        print(df.iloc[0].to_dict())
