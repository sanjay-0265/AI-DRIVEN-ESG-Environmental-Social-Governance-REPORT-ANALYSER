
import re
from pathlib import Path

NUM = r"(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?"  

def normalize_number(s: str) -> float:
    """Convert a string number to float (removes commas)."""
    return float(s.replace(",", ""))

def detect_year(pages, pdf_path):
    """
    Detect reporting year from first pages or filename.
    Returns int year or None.
    """
    year_pattern = r"(20\d{2})"
   

    for text in pages[:2]:
        match = re.search(year_pattern, text)
        if match:
            return int(match.group(1))
    
    fn_match = re.search(year_pattern, Path(pdf_path).stem)
    if fn_match:
        return int(fn_match.group(1))
    return None

def detect_company_name(pdf_path):
    """
    Guess company name from filename.
    Strips common words like ESG, Sustainability, FY, Report, etc.
    """
    stem = Path(pdf_path).stem
    clean = re.sub(r"(ESG|Sustainability|Report|CSR|Annual|FY|20\d{2}|_|-)+", " ", stem, flags=re.IGNORECASE)
    clean = re.sub(r"\s{2,}", " ", clean).strip()
    return clean or stem

def compile_alias(alias: str) -> str:
    """
    Convert alias to regex pattern that tolerates spaces/hyphens.
    """
    alias = re.escape(alias)
    alias = alias.replace(r"\ ", r"\s+").replace(r"\-", r"[-\s]?")
    return alias

def search_numeric_after_alias(text: str, alias: str):
    """
    Look for a number (optionally with unit) within 120 chars after alias.
    Returns (value, unit) or (None, None)
    """
    alias_pattern = compile_alias(alias)
    pattern = alias_pattern + r".{0,120}?(" + NUM + r")\s*([%A-Za-z/$\-]*)"
    match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
    if match:
        value = match.group(1)
        unit = match.group(2) or ""
        try:
            value = normalize_number(value)
        except:
            return None, None
        return value, unit.strip()
    return None, None

def detect_boolean(text: str, aliases):
    """
    Simple heuristic for boolean metrics.
    Returns True if alias is mentioned along with keywords.
    """
    for a in aliases:
        if re.search(compile_alias(a), text, flags=re.IGNORECASE):
            if re.search(r"(aligned|compliant|in\s+line\s+with|adopted|implemented)", text, flags=re.IGNORECASE):
                return True
    return False

def extract_from_pages(pages, metric_config):
    """
    Scan each page's text for defined ESG metrics.
    Returns list of dicts with metric, value, unit, source_page, year.
    """
    results = []
    for page_num, page_text in enumerate(pages, start=1):
        text_lower = page_text.lower()
        for metric in metric_config:
            # Boolean metrics
            if metric.get("boolean"):
                if detect_boolean(page_text, metric["aliases"]):
                    results.append({
                        "metric": metric["canonical_name"],
                        "value": True,
                        "unit": "boolean",
                        "source_page": page_num,
                        "year": None
                    })
                continue

            found = False
            for alias in metric["aliases"]:
                if alias.lower() in text_lower:
                    value, unit = search_numeric_after_alias(page_text, alias)
                    if value is not None:
                        results.append({
                            "metric": metric["canonical_name"],
                            "value": value,
                            "unit": unit or (metric.get("unit_hints") or [""])[0],
                            "source_page": page_num,
                            "year": None
                        })
                        found = True
                        break
            
            if not found:
                continue
    return results
