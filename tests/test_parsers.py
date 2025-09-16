# Moved from src/test_parsers.py
import pandas as pd
# from src.parsers.upi_statement_parser import UPIStatementParser
from src.parsers.amex_credit_card_parser import AmexCreditCardParser
from src.parsers.axis_bank_statement_parser import AxisBankStatementParser
from src.parsers.icici_credit_card_parser import ICICICreditCardParser
from src.parsers.icici_savings_bank_statement_parser import ICICISavingsBankStatementParser

def main():
    """Main function to demonstrate usage of all parsers"""
    sample_texts = {
        'upi': """31 Aug
11:31 AM
Money sent to Nandani Sagar Birade
UPI ID: nandinipatil2803-1@okicici on
UPI Ref No: 388668698794
Tag:
# Transfers
Axis Bank -
24
- Rs.1,898""",
        'amex': """August 2 Paytm*UBERINDIASYSTEMSP Noida 159.93
August 2 IRCTC DELHI 1,390.00 Cr
August 3 Billdesk*AMAZON MUM 2,504.00""",
        'axis': """01-08-2025 UPI/P2M/521303531178/JASODA KALUDAS VAISHN/Sent u/YES BANK LIMITED YBS 161.00 3,493.42""",
        'icici_credit_card': """10-08-2025 Fuel Trxn Onus 21.25 Cr. 11760327291
09-08-2025 CHOUDHARY AISHI RAM BA, DELHI, IND 2124.78 Dr. 11760327288""",
        'icici_savings': """01-08-2025 ACH/INDIAN CLEARING CORP/ICIC7013011210000326/O7291393250731207025212 1589704 10,500.00 95,507.37"""
    }

    # print("=== UPI STATEMENT PARSER ===")
    # upi_parser = UPIStatementParser("sample.txt")
    # upi_parser.text = sample_texts['upi']
    # upi_df = upi_parser.parse()
    # print(upi_df.to_string(index=False))
    # print()

    print("=== AMEX CREDIT CARD PARSER ===")
    amex_parser = AmexCreditCardParser("dummy.txt")
    amex_parser.text = sample_texts['amex']
    amex_df = amex_parser.parse()
    print(amex_df.to_string(index=False))
    print()

    print("=== AXIS BANK STATEMENT PARSER ===")
    axis_parser = AxisBankStatementParser("dummy.txt")
    axis_parser.text = sample_texts['axis']
    axis_df = axis_parser.parse()
    print(axis_df.to_string(index=False))
    print()

    print("=== ICICI CREDIT CARD PARSER ===")
    icici_credit_parser = ICICICreditCardParser("dummy.txt")
    icici_credit_parser.text = sample_texts['icici_credit_card']
    icici_credit_df = icici_credit_parser.parse()
    print(icici_credit_df.to_string(index=False))
    print()

    print("=== ICICI SAVINGS BANK STATEMENT PARSER ===")
    icici_savings_parser = ICICISavingsBankStatementParser("dummy.txt")
    icici_savings_parser.text = sample_texts['icici_savings']
    icici_savings_df = icici_savings_parser.parse()
    print(icici_savings_df.to_string(index=False))

if __name__ == "__main__":
    main()

# Function to read and parse your actual files
# def parse_bank_statements(file_paths):
#     results = {}
#     for bank, file_path in file_paths.items():
#         try:
#             with open(file_path, 'r', encoding='utf-8') as f:
#                 ...existing code...
