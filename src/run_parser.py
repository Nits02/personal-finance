
import os
from src.logger import get_logger
from src.config_loader import get_config
from src.io_utils import save_to_processed
import json
import src.analyzer as analyzer

# Folder-based mapping: (bank/type) -> parser class

# FOLDER_PARSER_MAP can be dynamically loaded from config if needed

def parse_statement(file_path):
    # This function is now deprecated; use src/parser.py:parse_statement instead
    from src.parser import parse_statement as main_parse_statement
    from src.parser import parse_statement as main_parse_statement
    return main_parse_statement(file_path)

if __name__ == "__main__":
    import sys
    logger = get_logger()
    import argparse

    parser = argparse.ArgumentParser(
        description="CLI entry-point: parse -> standardize -> save -> (optional) analyze\n\nUsage examples:\n  python src/run_parser.py data/raw/ICICI\\ August\\ Statement.pdf --analyze\n  python src/run_parser.py data/raw/2025/08/ --analyze --combined --fmt parquet"
    )
    parser.add_argument("statement_file", help="Path to the bank/credit card statement PDF or directory of statements")
    parser.add_argument("--analyze", action="store_true", help="Run financial analysis and save JSON report")
    parser.add_argument("--combined", action="store_true", help="Create combined CSV across processed files in directory")
    parser.add_argument("--fmt", choices=["csv", "parquet"], default="csv", help="Output format for processed files")
    args = parser.parse_args()

    file_path = args.statement_file
    run_analysis = args.analyze
    run_combined = args.combined
    output_fmt = args.fmt
    import pandas as pd
    pd.set_option('display.max_columns', None)

    def analyze_and_save_report(df, filename, bank=None, month=None):
        try:
            config = get_config()
            processed_dir = config['data']['processed_dir']
            output_dir = os.path.join(processed_dir, 'reports')
            os.makedirs(output_dir, exist_ok=True)
            # Compose name: <bank>_<month> (lowercase, underscores)
            name = None
            if bank and month:
                name = f"{bank.lower()}_{month.lower()}"
            else:
                # Fallback: use filename without extension
                name = os.path.splitext(filename)[0].lower().replace(' ', '_')
            # Run analyzer and save CSV/PNG files
            summary = analyzer.analyze_finances(df, output_dir=output_dir, save_plots=True, name=name)
            # Save JSON summary report as before
            report_path = os.path.join(output_dir, name + '.json')
            with open(report_path, 'w') as f:
                json.dump({k: (v.to_dict() if hasattr(v, 'to_dict') else v) for k, v in summary.items()}, f, indent=2, default=str)
            print(f"Saved analysis report: {report_path}")
            print(f"Saved monthly breakdown CSV: {os.path.join(output_dir, name + '_monthly.csv')}")
            print(f"Saved top categories CSV: {os.path.join(output_dir, name + '_top_categories.csv')}")
            print(f"Saved monthly trend PNG: {os.path.join(output_dir, name + '_monthly_trend.png')}")
        except Exception as e:
            logger.error(f"Failed to analyze and save report: {e}")

    def find_statement_files(directory):
        # Recursively find all PDF files in directory
        statement_files = []
        for root, _, files in os.walk(directory):
            for file in files:
                if file.lower().endswith('.pdf'):
                    statement_files.append(os.path.join(root, file))
        return statement_files

    try:
        if run_combined and os.path.isdir(file_path):
            # Parse all statement files in directory, combine, save
            statement_files = find_statement_files(file_path)
            dfs = []
            for f in statement_files:
                try:
                    df, metadata = parse_statement(f)
                    if df is not None and not df.empty:
                        # Standardize before saving
                        from src.standardizer import standardize_transactions
                        df = standardize_transactions(df, metadata)
                        dfs.append(df)
                        logger.info(f"Parsed and standardized {len(df)} transactions from {f} | Metadata: {metadata}")
                except Exception as e:
                    logger.error(f"Failed to parse {f}: {e}")
            if dfs:
                combined_df = pd.concat(dfs, ignore_index=True)
                # Dedupe by transaction id if present
                if 'transaction_id' in combined_df.columns:
                    combined_df = combined_df.drop_duplicates(subset=['transaction_id'])
                combined_filename = os.path.basename(os.path.normpath(file_path)) + "_combined.{}".format(output_fmt)
                config = get_config()
                processed_dir = config['data']['processed_dir']
                save_to_processed(combined_df, "Combined", combined_filename, format=output_fmt, processed_dir=processed_dir)
                print(f"Saved combined processed file: {os.path.join(processed_dir, combined_filename)}")
                if run_analysis:
                    # Try to extract bank and month from directory name
                    dir_name = os.path.basename(os.path.normpath(file_path)).lower()
                    bank = 'combined'
                    month = dir_name
                    analyze_and_save_report(combined_df, combined_filename, bank=bank, month=month)
                print("First full row (combined):")
                print(combined_df.iloc[0].to_dict())
                print("Columns:", list(combined_df.columns))
            else:
                print("No valid statement files found or parsed in directory.")
        else:
            # Single file mode
            df, metadata = parse_statement(file_path)
            if df is None:
                logger.error("Parser returned None. No DataFrame generated.")
            elif df.empty:
                logger.warning(f"Parsed DataFrame is empty. No transactions found in {file_path}.")
                print(df)
            else:
                # Standardize before saving
                from src.standardizer import standardize_transactions
                df = standardize_transactions(df, metadata)
                logger.info(f"Parsed and standardized {len(df)} transactions from {file_path} | Metadata: {metadata}")
                source = metadata.get('source', 'Unknown')
                filename = os.path.basename(file_path)
                config = get_config()
                processed_dir = config['data']['processed_dir']
                save_to_processed(df, source, filename, format=output_fmt, processed_dir=processed_dir)
                if run_analysis:
                    # Extract bank and month from metadata and filename
                    folder_parts = os.path.normpath(os.path.dirname(file_path)).split(os.sep)
                    bank = metadata.get('source', None)
                    month = None
                    if 'icici' in filename.lower():
                        if 'credit card' in filename.lower():
                            bank = 'icici_credit_card'
                        elif 'statement' in filename.lower() or 'august' in filename.lower():
                            bank = 'icici_savings'
                    for part in folder_parts:
                        if part.lower() in ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"] or part.isdigit():
                            month = part
                    if not month:
                        import re
                        m = re.search(r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|\d{2})', filename.lower())
                        if m:
                            month = m.group(1)
                    analyze_and_save_report(df, filename, bank=bank, month=month)
                print("First full row:")
                print(df.iloc[0].to_dict())
                print("Columns:", list(df.columns))
    except Exception as e:
        logger.error(f"Failed to parse statement: {e}")
