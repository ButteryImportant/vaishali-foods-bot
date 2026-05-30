from fastapi import FastAPI
import os
import json
import gspread
from google.oauth2.credentials import Credentials
from contextlib import asynccontextmanager

# Global variable to hold our sheet
sheet = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global sheet
    # This runs when the app starts
    print("--- Connecting to Google Sheets ---")
    try:
        creds_raw = os.environ.get("GSPREAD_AUTH_JSON")
        creds_dict = json.loads(creds_raw)
        creds = Credentials.from_authorized_user_info(creds_dict)
        client = gspread.authorize(creds)
        sheet = client.open("VaishaliOrders").sheet1
        print("SUCCESS: Google Sheets connected!")
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        # We don't raise here, so the web server can still start for debugging
    yield
    # This runs when the app stops

app = FastAPI(lifespan=lifespan)

@app.get("/")
def read_root():
    return {"message": "VaishaliBot is active!"}
