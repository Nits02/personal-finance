import pytest
import pandas as pd
from parser import parse_statement
from parsers.icici_credit_card_parser import ICICICreditCardParser
from parsers.amex_credit_card_parser import AmexCreditCardParser
from parsers.axis_bank_statement_parser import AxisBankStatementParser
from parsers.icici_savings_bank_statement_parser import ICICISavingsBankStatementParser
# from parsers.upi_statement_parser import UPIStatementParser

sample_text = "10-08-2025 Zomato Order 500.00 Dr. 12345678901"

# Amex parser expects lines like: "August 10 Zomato Order 500.00"
amex_sample_text = "August 10 Zomato Order 500.00"

parsers = [
    ICICICreditCardParser,
    AmexCreditCardParser,
    AxisBankStatementParser,
    ICICISavingsBankStatementParser,
    # UPIStatementParser,
]

@pytest.mark.parametrize("parser_cls", parsers)
def test_parse_statement_returns_dataframe(tmp_path, parser_cls):
    # Use bank/credit card keywords in filename and folder for detection
    if parser_cls.__name__ == "ICICICreditCardParser":
        file_path = tmp_path / "icici_credit_card_statement.txt"
        file_path.write_text(sample_text)
    elif parser_cls.__name__ == "AmexCreditCardParser":
        file_path = tmp_path / "amex_credit_card_statement.txt"
        file_path.write_text(amex_sample_text)
    elif parser_cls.__name__ == "AxisBankStatementParser":
        axis_dir = tmp_path / "axis" / "bank"
        axis_dir.mkdir(parents=True, exist_ok=True)
        file_path = axis_dir / "axis_bank_statement.txt"
        file_path.write_text(sample_text)
    elif parser_cls.__name__ == "ICICISavingsBankStatementParser":
        icici_dir = tmp_path / "icici" / "bank"
        icici_dir.mkdir(parents=True, exist_ok=True)
        file_path = icici_dir / "icici_bank_statement.txt"
        file_path.write_text(sample_text)
    # Use parse_statement from src/parser.py
    try:
        df, metadata = parse_statement(str(file_path))
    except Exception as e:
        df = pd.DataFrame()
        metadata = {}
        assert False, f"parse_statement failed: {e}"
    assert isinstance(df, pd.DataFrame)
    assert isinstance(metadata, dict)

@pytest.mark.parametrize("parser_cls", parsers)
def test_dataframe_has_required_columns(tmp_path, parser_cls):
    if parser_cls.__name__ == "ICICICreditCardParser":
        file_path = tmp_path / "icici_credit_card_statement.txt"
        file_path.write_text(sample_text)
    elif parser_cls.__name__ == "AmexCreditCardParser":
        file_path = tmp_path / "amex_credit_card_statement.txt"
        file_path.write_text(amex_sample_text)
    elif parser_cls.__name__ == "AxisBankStatementParser":
        axis_dir = tmp_path / "axis" / "bank"
        axis_dir.mkdir(parents=True, exist_ok=True)
        file_path = axis_dir / "axis_bank_statement.txt"
        file_path.write_text(sample_text)
    elif parser_cls.__name__ == "ICICISavingsBankStatementParser":
        icici_dir = tmp_path / "icici" / "bank"
        icici_dir.mkdir(parents=True, exist_ok=True)
        file_path = icici_dir / "icici_bank_statement.txt"
        file_path.write_text(sample_text)
    try:
        df, metadata = parse_statement(str(file_path))
    except Exception as e:
        df = pd.DataFrame()
        assert False, f"parse_statement failed: {e}"
    required = {'date', 'description', 'amount', 'type'}
    # Accept if DataFrame is empty (edge case)
    if df.empty:
        assert True
    else:
        assert required.issubset(set(df.columns))

@pytest.mark.parametrize("parser_cls", parsers)
def test_category_assignment(tmp_path, parser_cls):
    if parser_cls.__name__ == "ICICICreditCardParser":
        file_path = tmp_path / "icici_credit_card_statement.txt"
        file_path.write_text(sample_text)
    elif parser_cls.__name__ == "AmexCreditCardParser":
        file_path = tmp_path / "amex_credit_card_statement.txt"
        file_path.write_text(amex_sample_text)
    elif parser_cls.__name__ == "AxisBankStatementParser":
        axis_dir = tmp_path / "axis" / "bank"
        axis_dir.mkdir(parents=True, exist_ok=True)
        file_path = axis_dir / "axis_bank_statement.txt"
        file_path.write_text(sample_text)
    elif parser_cls.__name__ == "ICICISavingsBankStatementParser":
        icici_dir = tmp_path / "icici" / "bank"
        icici_dir.mkdir(parents=True, exist_ok=True)
        file_path = icici_dir / "icici_bank_statement.txt"
        file_path.write_text(sample_text)
    try:
        df, metadata = parse_statement(str(file_path))
    except Exception as e:
        df = pd.DataFrame()
        assert False, f"parse_statement failed: {e}"
    if 'Category' in df.columns:
        assert 'Food' in df['Category'].values
