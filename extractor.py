import fitz  
import pandas as pd
import os
import json


config_path = os.path.join(os.path.dirname(__file__), "config", "metrics_config.json")
with open(config_path, "r", encoding="utf-8") as f:
    METRIC_CONFIG = json.load(f)["metrics"]


from core_extraction import extract_from_pages, detect_year, detect_company_name


def pdf_to_pages(pdf_path):
    """
    Reads a PDF and returns a list of page texts.
    """
    doc = fitz.open(pdf_path)
    return [page.get_text() for page in doc]


def extract_esg(pdf_path):
    """
    Extract ESG metrics from a given PDF file using the configured metrics.
    Returns a pandas DataFrame with extracted data.
    """
    pages = pdf_to_pages(pdf_path)

   
    rows = extract_from_pages(pages, METRIC_CONFIG)

   
    company = detect_company_name(pdf_path)
    year = detect_year(pages, pdf_path)

    
    for r in rows:
        r["company_name"] = company
        if r.get("year") is None:
            r["year"] = year

    
    df = pd.DataFrame(rows)
    return df
