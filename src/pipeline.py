import argparse, json, os
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd
from tqdm import tqdm

from pdf_reader import read_pdf_text_by_page
from extract_metrics import extract_from_pages, detect_year, detect_company_name

def build_nested_json(company: str, report_year: int, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    env = {}
    soc = {}
    gov = {}
    # pick first occurrence per json_key
    seen = set()
    for r in rows:
        jk = r["json_key"]
        if jk in seen:
            continue
        seen.add(jk)
        if r["category"] == "environmental":
            env[jk] = r["value"] if r["unit"] != "boolean" else True
        elif r["category"] == "social":
            soc[jk] = r["value"] if r["unit"] != "boolean" else True
        else:
            gov[jk] = r["value"] if r["unit"] != "boolean" else True
    return {
        "company_name": company,
        "report_year": report_year,
        "environmental": env,
        "social": soc,
        "governance": gov
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Folder with PDFs")
    ap.add_argument("--output", required=True, help="Output folder")
    ap.add_argument("--config", default=str(Path(__file__).resolve().parent.parent / "config" / "metrics_config.json"))
    args = ap.parse_args()

    in_dir = Path(args.input)
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    with open(args.config, "r", encoding="utf-8") as f:
        config = json.load(f)

    pdfs = sorted([p for p in in_dir.glob("*.pdf")])
    all_rows = []

    for pdf in tqdm(pdfs, desc="Processing PDFs"):
        pages = read_pdf_text_by_page(str(pdf))
        if not pages or all((not t.strip()) for t in pages):
            print(f"WARNING: No text extracted from {pdf.name}. Is it scanned? (OCR needed)")
            continue

        rows = extract_from_pages(pages, config)
        # enrich rows with year and file info
        ry = detect_year(pages, str(pdf))
        company = detect_company_name(str(pdf))

        for r in rows:
            r["company_name"] = company
            r["report_year"] = ry
            if r["year"] is None:
                r["year"] = ry
            r["source_file"] = pdf.name
        all_rows.extend(rows)

        # write nested JSON per report
        nested = build_nested_json(company, ry, rows)
        json_path = out_dir / f"{company}_{ry}_extracted.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(nested, f, indent=2)

    if all_rows:
        df = pd.DataFrame(all_rows, columns=["company_name","report_year","metric_name","unit","value","year","source_page","source_file","category","json_key"])
        df.to_csv(out_dir / "metrics_extracted.csv", index=False, encoding="utf-8")
        print(f"Wrote {out_dir/'metrics_extracted.csv'}")
    else:
        print("No metrics found. Try adding more aliases/units in config or test with a different PDF.")

if __name__ == "__main__":
    main()
