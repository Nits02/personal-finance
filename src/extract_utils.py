import os
import re

def get_extracted_txt_path(pdf_path):
    base_dir, pdf_filename = os.path.split(pdf_path)
    txt_filename = re.sub(r'\.pdf$', '_extracted.txt', pdf_filename, flags=re.IGNORECASE)
    txt_path = os.path.join(base_dir, txt_filename)
    return txt_path

def save_extracted_text(pdf_path, text):
    txt_path = get_extracted_txt_path(pdf_path)
    os.makedirs(os.path.dirname(txt_path), exist_ok=True)
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(text)
    return txt_path
