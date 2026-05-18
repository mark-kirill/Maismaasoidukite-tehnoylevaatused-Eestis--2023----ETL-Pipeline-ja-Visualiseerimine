import os
import requests

API_URL = "https://andmed.eesti.ee/api/datasets/ae47fec7-63d0-4b7a-969b-fbdfed21d52a/files/1943aed4-8e53-4e70-9946-7fc8ad1f7dfe/download-s3"
OUTPUT_FILE = "data/raw/raw_file.csv"

os.makedirs("data/raw", exist_ok=True)

if os.path.exists(OUTPUT_FILE):
    print("File already exists.")
else:
    response = requests.get(API_URL)

    if response.status_code == 200:
        with open(OUTPUT_FILE, "wb") as f:
            f.write(response.content)

        print("CSV downloaded.")
    else:
        print(f"Download failed: {response.status_code}")