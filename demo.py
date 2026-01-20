import pandas as pd
import re

# Load your scraped CSV
df = pd.read_csv("location_data.csv")

IMPACT_KEYWORDS = [
    "road","metro","traffic","flyover","infrastructure","development","growth",
    "real estate","housing","apartment","office","commercial","it","tech",
    "company","startup","jobs","employment","investment","business",
    "hospital","health","school","college","education",
    "restaurant","mall","retail",
    "water","electricity","pollution","crime","flood","safety","civic"
]

def split_sentences(text):
    return re.split(r'(?<=[.!?])\s+', text)

def extract_relevant(text, location):
    text_l = text.lower()
    loc_l = location.lower()

    sentences = split_sentences(text)
    relevant = []

    for s in sentences:
        s_l = s.lower()
        if loc_l in s_l and any(k in s_l for k in IMPACT_KEYWORDS):
            relevant.append(s.strip())

    final = " ".join(relevant)
    return final if len(final) >= 150 else None

clean_rows = []

for _, row in df.iterrows():
    content = str(row["content"])
    location = str(row["location"])

    extracted = extract_relevant(content, location)
    if extracted:
        clean_rows.append({
            "location": location,
            "source": row["source"],
            "source_url": row["source_url"],
            "relevant_text": extracted
        })

clean_df = pd.DataFrame(clean_rows)

# Save clean output
clean_df.to_excel("location_sentence_level_data.xlsx", index=False)

print("✅ Clean sentence-level dataset created")
print("Rows:", len(clean_df))
