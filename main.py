from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
import requests
import json
import os
import gspread

app = FastAPI()

# Configuration
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN")
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID")
ADMIN_PHONE = os.environ.get("ADMIN_PHONE")

# Google Sheets Setup
# Ensure your Render Environment Variable 'GSPREAD_AUTH_JSON' 
# contains the merged JSON (client_id, client_secret, refresh_token, token_uri)
creds_raw = os.environ.get("GSPREAD_AUTH_JSON")

if not creds_raw:
    raise ValueError("FATAL ERROR: GSPREAD_AUTH_JSON environment variable is not set!")

try:
    creds_dict = json.loads(creds_raw)
    # This authenticates using the combined credentials and token
    client = gspread.oauth_from_dict(creds_dict)
    sheet = client.open("VaishaliOrders").sheet1
    print("Successfully connected to Google Sheets!")
except Exception as e:
    print(f"Error connecting to Google Sheets: {e}")
    raise e

user_state = {}

# --- Add your FastAPI routes/logic below ---

def send_message(to, text, interactive=None):
    url = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}
    
    data = {"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": text}}
    if interactive:
        data["type"] = "interactive"
        data["interactive"] = interactive
    
    response = requests.post(url, headers=headers, json=data)
    print(f"DEBUG: API Response: {response.status_code} - {response.text}")
    return response

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    try:
        value = data.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {})
        if "messages" in value:
            msg = value["messages"][0]
            phone = msg["from"]
            
            # Handle Buttons OR Text
            if msg.get("type") == "interactive":
                text = msg["interactive"]["button_reply"]["id"]
            else:
                text = msg["text"]["body"].lower()

            state = user_state.get(phone, "START")

            if text in ["hi", "hello", "start"]:
                user_state[phone] = "MENU"
                send_message(phone, "👋 Welcome to Vaishali Foods!")
            elif text == "menu" or state == "MENU":
                user_state[phone] = "SELECT_ITEM"
                menu = {
                    "type": "button",
                    "body": {"text": "Select your Laddoo:"},
                    "action": {"buttons": [
                        {"type": "reply", "reply": {"id": "1", "title": "Besan Laddoo"}},
                        {"type": "reply", "reply": {"id": "2", "title": "Til Laddoo"}}
                    ]}
                }
                send_message(phone, "", interactive=menu)
            elif isinstance(state, str) and state == "SELECT_ITEM":
                item = "Besan Laddoo" if text == "1" else "Til Laddoo"
                user_state[phone] = {"step": "QTY", "item": item}
                send_message(phone, "How many kg?")
            elif isinstance(state, dict) and state.get("step") == "QTY":
                state.update({"qty": text, "step": "ADDRESS"})
                user_state[phone] = state
                send_message(phone, "Please send your delivery address.")
            elif isinstance(state, dict) and state.get("step") == "ADDRESS":
                state.update({"address": text, "step": "CONFIRM"})
                user_state[phone] = state
                send_message(phone, f"Confirm order: {state['item']} ({state['qty']}kg) to {text}? Reply CONFIRM")
            elif text == "confirm" and isinstance(state, dict):
                # Save to Google Sheets
                sheet.append_row([phone, state['item'], state['qty'], state['address']])
                send_message(phone, "✅ Order placed!")
                send_message(ADMIN_PHONE, f"🔔 NEW ORDER: {state['item']}, {state['qty']}kg to {state['address']}")
                user_state.pop(phone, None)
    except Exception as e: print(f"ERROR: {e}")
    return {"status": "ok"}
