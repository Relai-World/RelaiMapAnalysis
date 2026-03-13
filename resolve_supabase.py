
import socket

ref = "ihraowxbduhlichzszgk"
patterns = [
    f"db.{ref}.supabase.co",
    f"{ref}.supabase.co",
    f"aws-0-ap-south-1.pooler.supabase.com"
]

for p in patterns:
    try:
        ip = socket.gethostbyname(p)
        print(f"✅ {p} resolves to {ip}")
    except:
        print(f"❌ {p} does not resolve")
