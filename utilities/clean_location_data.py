import pandas as pd
import re
from pathlib import Path
from tqdm import tqdm

# =========================
# PATH CONFIG
# =========================
SCRIPT_DIR = Path(__file__).resolve().parent
INPUT_EXCEL = SCRIPT_DIR / "raw_scraped_data.xlsx"
OUTPUT_EXCEL = SCRIPT_DIR / "cleaned_raw_scraped_data.xlsx"

TEXT_COLUMN = "content"

# =========================
# FRAGMENTS HUMANS IGNORE
# (about the WEBSITE, not the WORLD)
# =========================
WEBSITE_SIGNALS = [
    "subscribe",
    "sign up",
    "log in",
    "privacy policy",
    "terms and conditions",
    "cookie",
    "advertisement",
    "download our app",
    "follow us",
    "click here",
    "read more at",
    "all rights reserved",
    "©",
    "e-paper",
    "navigation",
    "share this",
]

def is_website_fragment(text: str) -> bool:
    t = text.lower()

    # strong website intent
    if any(signal in t for signal in WEBSITE_SIGNALS):
        return True

    # UI-like fragments
    if len(t) < 20 and not re.search(r"[a-zA-Z]{4,}", t):
        return True

    # menu-like casing
    if t.isupper() and len(t.split()) <= 4:
        return True

    return False

# =========================
# HUMAN-LIKE RECORD CLEANER
# =========================
def clean_record_human_style(text: str) -> str:
    if not isinstance(text, str):
        return ""

    # normalize spacing
    text = text.replace("\u00a0", " ")
    text = re.sub(r"\s+", " ", text)

    # split gently (like paragraphs / thought units)
    fragments = re.split(r"\n+| {3,}|[|•]", text)

    kept_fragments = []

    for frag in fragments:
        f = frag.strip()

        if not f:
            continue

        # THIS is the key human decision
        if is_website_fragment(f):
            continue

        kept_fragments.append(f)

    # reassemble preserving flow
    cleaned_text = ". ".join(kept_fragments)

    # final polish
    cleaned_text = re.sub(r"\.\s+\.", ".", cleaned_text)
    cleaned_text = re.sub(r"\s{2,}", " ", cleaned_text)

    return cleaned_text.strip()

# =========================
# MAIN
# =========================
def main():
    print("📥 Loading Excel...")
    df = pd.read_excel(INPUT_EXCEL)

    if TEXT_COLUMN not in df.columns:
        raise ValueError(f"Column '{TEXT_COLUMN}' not found")

    print(f"🧹 Human-style trimming {len(df)} records (record-wise)...")

    df[TEXT_COLUMN] = [
        clean_record_human_style(text)
        for text in tqdm(df[TEXT_COLUMN], total=len(df))
    ]

    df.to_excel(OUTPUT_EXCEL, index=False)

    print(f"✅ Cleaned file saved → {OUTPUT_EXCEL}")
    print("🧠 Trimmed like a human editor. Meaning preserved.")

if __name__ == "__main__":
    main()
