import pdfplumber
from typing import List, Tuple

def read_pdf_text_by_page(path: str) -> List[str]:
    """
    Returns a list of strings, one per page, combining text + any detected tables as pipe-delimited rows.
    """
    texts = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            txt = page.extract_text() or ""
            
            try:
                tables = page.extract_tables() or []
            except Exception:
                tables = []
            for tb in tables:
                for row in tb:
                    row = [(c if c is not None else "") for c in row]
                    txt += "\n" + " | ".join(row)
            texts.append(txt)
    return texts
