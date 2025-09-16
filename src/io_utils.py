
import os
import pandas as pd
import json
from datetime import datetime
from src.logger import get_logger


def save_to_processed(df, source, filename, format='csv', processed_dir=None, original_path=None):
    """
    Save DataFrame to processed dir as CSV or Parquet, log, and append manifest entry.
    Args:
        df (pd.DataFrame): DataFrame to save
        source (str): Source identifier
        filename (str): Desired filename (spaces replaced, lowercased)
        format (str): 'csv' or 'parquet'
        processed_dir (str): Optional base dir for processed files
        original_path (str): Optional original file path
    Returns:
        str: Path to saved file
    """
    logger = get_logger()
    # Configurable processed dir
    if processed_dir is None:
        processed_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed')
    os.makedirs(processed_dir, exist_ok=True)
    safe_filename = filename.replace(' ', '_').lower() + ('.parquet' if format == 'parquet' else '.csv')
    save_path = os.path.join(processed_dir, safe_filename)
    # Ensure all columns, including AccountType, are saved
    if 'AccountType' in df.columns:
        cols = [col for col in df.columns if col != 'AccountType'] + ['AccountType']
        df = df[cols]
    if format == 'parquet':
        df.to_parquet(save_path, index=False)
    else:
        df.to_csv(save_path, index=False)
    logger.info(f"Saved processed file: {save_path}")

    # Manifest metadata
    manifest_path = os.path.join(processed_dir, 'manifest.json')
    metadata = {
        'filename': safe_filename,
        'source': source,
        'rows': int(df.shape[0]),
        'amount_sum': float(df['AmountValue'].sum()) if 'AmountValue' in df.columns else None,
        'date_min': str(df['Date'].min()) if 'Date' in df.columns else None,
        'date_max': str(df['Date'].max()) if 'Date' in df.columns else None,
        'saved_at': datetime.now().isoformat(),
        'original_path': original_path
    }
    # Append to manifest.json
    try:
        if os.path.exists(manifest_path):
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
        else:
            manifest = []
        manifest.append(metadata)
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)
        logger.info(f"Appended metadata to manifest: {metadata}")
    except Exception as e:
        logger.error(f"Failed to update manifest.json: {e}")
    return save_path
