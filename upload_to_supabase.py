#!/usr/bin/env python3
"""
Upload large files to Supabase Storage
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase client
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

if not url or not key:
    print("❌ Error: SUPABASE_URL and SUPABASE_KEY must be set in .env file")
    exit(1)

supabase: Client = create_client(url, key)

# Bucket name
BUCKET_NAME = "map-assets"

# Files to upload
files_to_upload = [
    {
        "local_path": "frontend/data/hmda_test_300dpi.png",
        "storage_path": "hmda_test_300dpi.png"
    },
    {
        "local_path": "frontend/data/hmda_masterplan_450dpi.png",
        "storage_path": "hmda_masterplan_450dpi.png"
    },
    {
        "local_path": "frontend/maptiles/bangalore_water_accumulation.pmtiles",
        "storage_path": "bangalore_water_accumulation.pmtiles"
    }
]

def create_bucket_if_not_exists():
    """Create the bucket if it doesn't exist"""
    try:
        # Try to get bucket info
        supabase.storage.get_bucket(BUCKET_NAME)
        print(f"✅ Bucket '{BUCKET_NAME}' already exists")
    except:
        # Create bucket if it doesn't exist
        try:
            supabase.storage.create_bucket(BUCKET_NAME, options={"public": True})
            print(f"✅ Created bucket '{BUCKET_NAME}'")
        except Exception as e:
            print(f"❌ Error creating bucket: {e}")
            exit(1)

def upload_file(local_path, storage_path):
    """Upload a single file to Supabase Storage"""
    if not os.path.exists(local_path):
        print(f"❌ File not found: {local_path}")
        return None
    
    file_size_mb = os.path.getsize(local_path) / (1024 * 1024)
    print(f"\n📤 Uploading {local_path} ({file_size_mb:.2f} MB)...")
    
    try:
        with open(local_path, 'rb') as f:
            file_data = f.read()
            
        # Upload file
        result = supabase.storage.from_(BUCKET_NAME).upload(
            storage_path,
            file_data,
            file_options={"content-type": "application/octet-stream"}
        )
        
        # Get public URL
        public_url = supabase.storage.from_(BUCKET_NAME).get_public_url(storage_path)
        
        print(f"✅ Uploaded successfully!")
        print(f"📍 Public URL: {public_url}")
        
        return public_url
        
    except Exception as e:
        print(f"❌ Error uploading {local_path}: {e}")
        return None

def main():
    print("🚀 Starting upload to Supabase Storage...\n")
    
    # Create bucket if needed
    create_bucket_if_not_exists()
    
    # Upload all files
    urls = {}
    for file_info in files_to_upload:
        url = upload_file(file_info["local_path"], file_info["storage_path"])
        if url:
            urls[file_info["storage_path"]] = url
    
    # Print summary
    print("\n" + "="*60)
    print("📋 UPLOAD SUMMARY")
    print("="*60)
    for storage_path, url in urls.items():
        print(f"\n{storage_path}:")
        print(f"  {url}")
    
    print("\n✅ All uploads complete!")
    print("\n💡 Copy these URLs and share them to update the code.")

if __name__ == "__main__":
    main()
