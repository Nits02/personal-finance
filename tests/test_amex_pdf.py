import pandas as pd
from src.parsers.amex_credit_card_parser import AmexCreditCardParser
from src.standardizer import standardize_transactions
import pdfplumber
from src.extract_utils import save_extracted_text
import os

def extract_text_from_pdf(pdf_path):
	text = ""
	with pdfplumber.open(pdf_path) as pdf:
		for page in pdf.pages:
			page_text = page.extract_text()
			if page_text:
				text += page_text + "\n"
	return text

def main():
	pdf_path = "data/raw/2025/08/amex/credit_card/Amex Credit Card Statement 2025-08-28.pdf"
	if not os.path.exists(pdf_path):
		print(f"File not found: {pdf_path}")
		return
	text = extract_text_from_pdf(pdf_path)
	temp_txt_path = save_extracted_text(pdf_path, text)
	parser = AmexCreditCardParser(temp_txt_path)
	df = parser.parse()
	df_std = standardize_transactions(df, source="Amex Credit Card", is_credit_card=True)
	print(df_std.to_string(index=False))

if __name__ == "__main__":
	main()
