from dotenv import load_dotenv
import os
from supabase import create_client

load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
sb = create_client(url, key)

res = sb.table("news_balanced_corpus_1").select("location_name, location_id").ilike("location_name", "B%").limit(10).execute()
print("SB result data length:", len(res.data))
if len(res.data) > 0:
    print(res.data[0])
