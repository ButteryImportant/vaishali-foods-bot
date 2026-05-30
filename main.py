from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
import requests
import os
import json
import gspread
from google.oauth2.credentials import Credentials
from contextlib import asynccontextmanager

# Global variables
sheet = None
user_state = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    global sheet
    try:
        creds_raw = os.environ.get("GSPREAD_AUTH_JSON")
        creds_dict = json.loads(creds_raw)
        creds = Credentials.from_authorized_user_info(creds_dict)
        client = gspread.authorize(creds)
        sheet = client.open("VaishaliOrders").sheet1
        print("SUCCESS: Google Sheets connected!")
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
    yield

app = FastAPI(lifespan=lifespan)

# Webhook Verification (Meta)
@app.get("/webhook")
async def verify_webhook(request: Request):
    if request.query_params.get("hub.verify_token") == os.environ.get("VERIFY_TOKEN"):
        return PlainTextResponse(request.query_params.get("hub.challenge"))
    return PlainTextResponse("Forbidden", status_code=403)

# Webhook Receiver (Handles Messages & Buttons)
@app.post("/webhook")
async def handle_message(request: Request):
    data = await request.json()
    
    # Extract sender and text/button info safely
    try:
        value = data["entry"][0]["changes"][0]["value"]
        message = value["messages"][0]
        sender = message["from"]
        
        if message["type"] == "interactive":
            text = message["interactive"]["button_reply"]["id"]
        else:
            # We use .lower() to make sure "Hi" and "hi" both work
            text = message["text"]["body"].lower()
            
        print(f"DEBUG: Processing text: {text} from {sender}")

        # The Logic
        if text in ["hi", "hello"]:
            print(f"DEBUG: Triggering buttons for {sender}")
            send_buttons(sender)
            user_state[sender] = "WAITING"
        
        elif text == "menu_view":
            # Add logic for what happens when they click 'View Menu'
            pass

    except Exception as e:
        print(f"DEBUG: Error in handle_message: {e}")
        
    return {"status": "ok"}

# Helper to send buttons back to user
def send_buttons(recipient):
    url = f"https://graph.facebook.com/v21.0/{os.environ.get('PHONE_NUMBER_ID')}/messages"
    headers = {"Authorization": f"Bearer {os.environ.get('ACCESS_TOKEN')}"}
    payload = {
        "messaging_product": "whatsapp",
        "to": recipient,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": "Welcome to Vaishali Orders! What would you like to do?"},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": "menu_view", "title": "View Menu"}},
                    {"type": "reply", "reply": {"id": "order_start", "title": "Place Order"}}
                ]
            }
        }
    }
    requests.post(url, json=payload, headers=headers)
