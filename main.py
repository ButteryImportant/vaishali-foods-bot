from fastapi import FastAPI
import os
import json
import gspread
from google.oauth2.credentials import Credentials

app = FastAPI()

print("--- Starting Initialization ---")

# 1. Load the Environment Variable
creds_raw = os.environ.get("GSPREAD_AUTH_JSON")

if not creds_raw:
    print("FATAL ERROR: GSPREAD_AUTH_JSON environment variable is not set!")
    raise ValueError("GSPREAD_AUTH_JSON environment variable is not set!")

# 2. Initialize Google Sheets
try:
    print("Attempting to parse JSON...")
    creds_dict = json.loads(creds_raw)
    
    print("Attempting to create Credentials object...")
    # This expects client_id, client_secret, refresh_token, token_uri
    creds = Credentials.from_authorized_user_info(creds_dict)
    
    print("Attempting to authorize gspread...")
    client = gspread.authorize(creds)
    
    print("Attempting to open 'VaishaliOrders'...")
    sheet = client.open("VaishaliOrders").sheet1
    print("SUCCESS: Google Sheets connected!")

except Exception as e:
    print(f"CRITICAL ERROR: {str(e)}")
    raise e

print("--- Initialization Complete ---")

@app.get("/")
def read_root():
    return {"message": "VaishaliBot is active and connected to Sheets!"}
