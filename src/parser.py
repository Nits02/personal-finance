
# --- Imports and global variables ---
import os
import re
from src.logger import get_logger
from src.parsers.icici_credit_card_parser import ICICICreditCardParser
from src.parsers.icici_savings_bank_statement_parser import ICICISavingsBankStatementParser
from src.parsers.axis_bank_statement_parser import AxisBankStatementParser
from src.parsers.amex_credit_card_parser import AmexCreditCardParser
# from parsers.upi_statement_parser import UPIStatementParser  # Disabled: not available
# from parsers.hdfc_credit_card_parser import HDFCCreditCardParser  # Placeholder for future
# from parsers.sbi_bank_statement_parser import SBIBankStatementParser  # Placeholder for future

BANK_MAPPINGS = {
    "icici_credit_card": ICICICreditCardParser,
    "icici_savings": ICICISavingsBankStatementParser,
    "axis": AxisBankStatementParser,
    "amex": AmexCreditCardParser,
    # "upi": UPIStatementParser,  # Disabled: not available
    # "hdfc_credit_card": HDFCCreditCardParser,
    # "sbi": SBIBankStatementParser,
}

# --- Main function ---
def parse_statement(file_path):
    logger = get_logger()
    file_name = os.path.basename(file_path).lower().replace('_', ' ').replace('-', ' ')
    folder_parts = [re.sub(r'[_\-]', ' ', part.lower()) for part in os.path.normpath(os.path.dirname(file_path)).split(os.sep)]
    logger.info(f"[DEBUG] file_name: {file_name}")
    logger.info(f"[DEBUG] folder_parts: {folder_parts}")
    bank_key = None
    # Flexible ICICI detection using regex and substring matching
    icici_in_path = any(re.search(r'icici', part) for part in folder_parts) or re.search(r'icici', file_name)
    if icici_in_path:
        credit_card_in_path = any(re.search(r'credit\s*card', part) for part in folder_parts) or re.search(r'credit\s*card', file_name)
        bank_in_path = any(re.search(r'bank|savings|statement', part) for part in folder_parts) or re.search(r'bank|savings|statement', file_name)
        if credit_card_in_path:
            bank_key = "icici_credit_card"
        elif bank_in_path:
            bank_key = "icici_savings"
    # Fallback to original detection for other banks (flexible)
    if not bank_key:
        for key, parser_cls in BANK_MAPPINGS.items():
            key_pattern = re.sub(r'_', ' ', key)
            if re.search(key_pattern, file_name) or any(re.search(key_pattern, part) for part in folder_parts):
                bank_key = key
                break
    if bank_key and bank_key in BANK_MAPPINGS:
        parser_cls = BANK_MAPPINGS[bank_key]
        parser = parser_cls(file_path)
        try:
            result = parser.parse()
            if isinstance(result, tuple) and len(result) == 2:
                df, metadata = result
            else:
                df = result
                metadata = {
                    "source": bank_key,
                    "is_credit_card": "credit_card" in bank_key,
                    "parser": parser_cls.__name__
                }
            from src.standardizer import standardize_transactions
            df = standardize_transactions(df, metadata)
            logger.info(f"Parsed {len(df)} transactions from {file_path} using {parser_cls.__name__}")
            return df, metadata
        except Exception as e:
            logger.error(f"Failed to parse {file_path} with {parser_cls.__name__}: {e}")
            raise
    logger.error(f"Bank or statement type not supported or not detected in file name: {file_name} or folders: {folder_parts}")
    raise ValueError("Bank or statement type not supported or not detected in file name or folders.")

# --- CLI/test block ---
if __name__ == "__main__":
    import sys
    logger = get_logger()
    if len(sys.argv) < 2:
        logger.error("Usage: python src/parser.py <statement_file>")
        sys.exit(1)
    file_path = sys.argv[1]
    try:
        df, metadata = parse_statement(file_path)
        logger.info(f"Parsed {len(df)} transactions from {file_path}")
        logger.info(f"Metadata: {metadata}")
        print(df.head(10))
    except Exception as e:
        logger.error(f"Failed to parse statement: {e}")

