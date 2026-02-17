import re
import json
from typing import Dict, Any, List, Tuple
from pathlib import Path

NUM = r"(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?"  

def normalize_number(s: str) -> float:
    return float(s.replace(",", ""))

def detect_year(pages: List[str], filename: str) -> int:
    """
    Try to detect a 4-digit year (2010-2100) from content or filename.
    Preference: FY patterns, then majority year occurrences, then filename.
    """
    content = "\n".join(pages)
    
    fy_match = re.search(r"\bFY\s*([2][0-1]\d{2})\b", content, flags=re.IGNORECASE)
    if fy_match:
        return int(fy_match.group(1))
    years = re.findall(r"\b(20\d{2})\b", content)
    years = [int(y) for y in years if 2010 <= int(y) <= 2100]
    if years:
        
        from collections import Counter
        return Counter(years).most_common(1)[0][0]
    
    fn_year = re.search(r"(20\d{2})", Path(filename).stem)
    if fn_year:
        return int(fn_year.group(1))
    return None 

def detect_company_name(filename: str) -> str:
    """
    Guess company from filename, e.g., ACME_2024_ESG.pdf -> ACME
    """
    stem = Path(filename).stem
    
    clean = re.sub(r"(ESG|Sustainability|Report|CSR|Annual|FY|20\d{2}|_|-)+", " ", stem, flags=re.IGNORECASE)
    clean = re.sub(r"\s{2,}", " ", clean).strip()
    return clean or stem

def compile_alias(alias: str) -> str:
    

    alias = re.escape(alias)
    alias = alias.replace(r"\ ", r"\s+").replace(r"\-", r"[-\s]?")
    return alias

def search_numeric_after_alias(text: str, alias: str) -> List[Tuple[str, str]]:
    """
    Return list of (value, unit) tuples found within 120 chars after alias.
    """
    pattern = compile_alias(alias) + r".{0,120}?" + rf"({NUM})\s*([%A-Za-z/$\-]*?)\b"
    hits = []
    for m in re.finditer(pattern, text, flags=re.IGNORECASE|re.DOTALL):
        val = m.group(1)
        unit = (m.group(2) or "").strip()
        unit = unit[:12]  
        hits.append((val, unit))
    return hits

def detect_boolean(text: str, aliases: List[str]) -> bool:
    
    for a in aliases:
        if re.search(compile_alias(a), text, flags=re.IGNORECASE):
            if re.search(r"(aligned|compliant|in\s+line\s+with|adopted|implemented)", text, flags=re.IGNORECASE):
                return True
    return False

def extract_from_pages(pages: List[str], config: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows = []
    for page_idx, text in enumerate(pages, start=1):
        for m in config["metrics"]:
            aliases = m["aliases"]
            if m.get("boolean"):
                val = detect_boolean(text, aliases)
                if val:
                    rows.append({
                        "metric_name": m["canonical_name"],
                        "unit": "boolean",
                        "value": True,
                        "year": None,
                        "source_page": page_idx,
                        "json_key": m["json_key"],
                        "category": m["category"]
                    })
                continue
            
            found = []
            for alias in aliases:
                found.extend(search_numeric_after_alias(text, alias))
            
            best = None
            for (v, u) in found:
                u_low = u.lower()
                if "%" in u_low or any(h.lower() in u_low for h in m["unit_hints"]):
                    best = (v, u)
                    break
            if not best and found:
                best = found[0]
            if best:
                v, u = best
                try:
                    value = normalize_number(v)
                except Exception:
                    continue
                unit = (u or (m["unit_hints"][0] if m["unit_hints"] else "")).strip() or (m["unit_hints"][0] if m["unit_hints"] else "")
                rows.append({
                    "metric_name": m["canonical_name"],
                    "unit": unit,
                    "value": value,
                    "year": None,
                    "source_page": page_idx,
                    "json_key": m["json_key"],
                    "category": m["category"]
                })
    return rows
