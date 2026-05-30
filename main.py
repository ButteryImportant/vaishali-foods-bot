from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
import requests
import os

app = FastAPI()

# Configuration from Environment Variables
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "vaishali123")
ACCESS_TOKEN = os.environ.get("EAAOdkFrIZC94BRqp6ZBX1DgxXSbxOnt2lvTmGAD5UkhwITyOZAtfHQzNgHp8yqB5kVuxZAhVnYrGo1GWbg6FpHO8cHR1E2CXTj1AUWaa2UeT5PJ6UShGItRmp9nZBNAJVOJOvqbPCEZB44sVZBCTBN5UNFWBul9Ael3n7BoWmUY9RCnHrJXEzk6HhExscEUYFbjdw83T7wdiQGvPah4lqUOR0ZCGkMuZANPO9NUaayoSZAyHwbQmpuKXMVDdYVdl8ifeMl0YOpv9O24CyvNBntxmyqUwZDZD")
PHONE_NUMBER_ID = os.environ.get("1160798840444641")
BIN_ID = os.environ.get("6a1b019b21f9ee59d29e12ba")
BIN_KEY = os.environ.get("$2a$10$y8QumvRZDDHMyd6UbaPuPevzKEXPnZ9v53hsY5COpN09OEc8SlFuO")

user_state = {}

# --- CLOUD DATABASE FUNCTIONS ---
def get_orders_from_cloud():
    try:
        url = f"https://api.jsonbin.io/v3/b/{BIN_ID}/latest"
        headers = {"X-Master-Key": BIN_KEY}
        response = requests.get(url, headers=headers)
        return response.json().get("record", [])
    except Exception as e:
        print(f"DEBUG: Cloud Load Error: {e}")
        return []

def save_order_to_cloud(new_order):
    try:
        orders = get_orders_from_cloud()
        orders.append(new_order)
        url = f"https://api.jsonbin.io/v3/b/6a1b019b21f9ee59d29e12ba"
        headers = {"X-Master-Key": BIN_KEY, "Content-Type": "application/json"}
        requests.put(url, headers=headers, json=orders)
    except Exception as e:
        print(f"DEBUG: Cloud Save Error: {e}")

# --- SEND MESSAGE (DEBUGGED) ---
def send_message(to, text):
    url = f"https://graph.facebook.com/v20.0/1160798840444641/messages"
    headers = {
        "Authorization": f"Bearer EAAOdkFrIZC94BRqp6ZBX1DgxXSbxOnt2lvTmGAD5UkhwITyOZAtfHQzNgHp8yqB5kVuxZAhVnYrGo1GWbg6FpHO8cHR1E2CXTj1AUWaa2UeT5PJ6UShGItRmp9nZBNAJVOJOvqbPCEZB44sVZBCTBN5UNFWBul9Ael3n7BoWmUY9RCnHrJXEzk6HhExscEUYFbjdw83T7wdiQGvPah4lqUOR0ZCGkMuZANPO9NUaayoSZAyHwbQmpuKXMVDdYVdl8ifeMl0YOpv9O24CyvNBntxmyqUwZDZD",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text}
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    # DEBUG: This will show in your Render logs if Meta rejects the message
    print(f"DEBUG: WhatsApp API Response: {response.status_code} - {response.text}")
    return response

# --- WEBHOOK ---
@app.get("/webhook")
def verify(request: Request):
    params = request.query_params
    if params.get("hub.mode") == "subscribe" and params.get("hub.verify_token") == VERIFY_TOKEN:
        return PlainTextResponse(content=params.get("hub.challenge"))
    return PlainTextResponse(content="error")

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
                save_order_to_cloud(state)
                send_message(phone, "✅ Order placed!")
                send_message(ADMIN_PHONE, f"🔔 NEW ORDER from {phone}: {state['item']}, {state['qty']}kg")
                user_state.pop(phone, None)
    except Exception as e: print(f"ERROR: {e}")
    return {"status": "ok"}
