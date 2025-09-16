src/
data/
tests/

# Personal Finance AI (Local)

## Overview
This project parses, standardizes, and analyzes personal finance statements from multiple banks and credit cards. It generates processed CSVs and detailed reports (JSON, CSV, PNG) for financial insights.

## Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Features
- Parse PDF/text statements from ICICI Savings, ICICI Credit Card, Axis Bank, Amex Credit Card
- Standardize transactions to a unified schema
- Save processed CSVs for each statement
- Automated financial analysis: monthly breakdowns, top categories, income/expense trends
- Output JSON, CSV, and PNG reports for each statement and combined data
- CLI for batch processing and analysis
- Unit tests for all parsers

## Usage
### Parse and Analyze a Statement
```bash
.venv/bin/python src/run_parser.py <statement_path> --analyze
```
Example:
```bash
.venv/bin/python src/run_parser.py data/raw/2025/08/amex/credit_card/Amex\ Credit\ Card\ Statement\ 2025-08-28.pdf --analyze
```

### CLI Options
- `--analyze`: Run financial analysis and save reports
- `--combined`: Combine multiple statements and analyze together

### Output Files
- Processed CSV: `data/processed/<bank>_<statement>.csv`
- Reports: `data/processed/reports/<bank>_<month>.json`, `<bank>_<month>_monthly.csv`, `<bank>_<month>_top_categories.csv`, `<bank>_<month>_monthly_trend.png`

## Directory Structure
```
src/
  parsers/                  # Individual bank/credit card parsers
  standardizer.py           # Transaction schema normalization
  analyzer.py               # Financial analysis/reporting
  io_utils.py, logger.py, extract_utils.py
data/
  raw/                      # Original PDFs/texts (organized by year/month/bank)
  processed/                # Processed CSVs and reports
    reports/                # JSON, CSV, PNG analysis outputs
tests/
  test_parser.py            # Unit tests (pytest)
  test_parsers.py           # Manual parser demo
  test_*.py                 # Individual parser tests
README.md
requirements.txt
```

## Testing
Run all unit tests:
```bash
PYTHONPATH=src .venv/bin/pytest tests/test_parser.py
```

## Example Workflow
1. Place statement PDFs in `data/raw/<year>/<month>/<bank>/<type>/`
2. Run the parser CLI with `--analyze` to process and analyze
3. Find processed CSVs in `data/processed/` and reports in `data/processed/reports/`
4. Run unit tests to validate parser logic

## Logging
Logs are printed to console and can be customized in `logger.py`.

## Extending
- To add a new bank, create a parser in `src/parsers/` and update `run_parser.py` detection logic.
- Follow the standardizer schema for output compatibility.

## Contact
For questions or contributions, open an issue or pull request.
