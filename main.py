from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
import requests
import json
import os
from datetime import datetime

app = FastAPI()

VERIFY_TOKEN = "vaishali123"
ACCESS_TOKEN = "YOUR_ACCESS_TOKEN_HERE"
PHONE_NUMBER_ID = "YOUR_PHONE_NUMBER_ID"

user_state = {}

# ---------------- HOME ----------------
@app.get("/")
def home():
    return {"status": "working"}

# ---------------- VERIFY WEBHOOK ----------------
@app.get("/webhook")
def verify(request: Request):
    params = request.query_params

    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    print("META HIT:", mode, token, challenge)

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return PlainTextResponse(content=challenge)

    return PlainTextResponse(content="error")


# ---------------- SEND MESSAGE ----------------
def send_message(to, text):
    url = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text}
    }

    requests.post(url, headers=headers, json=data)


# ---------------- ORDERS SYSTEM ----------------
ORDERS_FILE = "orders.json"

def load_orders():
    if not os.path.exists(ORDERS_FILE):
        return []
    with open(ORDERS_FILE, "r") as f:
        return json.load(f)

def save_orders(orders):
    with open(ORDERS_FILE, "w") as f:
        json.dump(orders, f, indent=2)

def create_order(phone, item, qty, address):
    orders = load_orders()

    order = {
        "phone": phone,
        "item": item,
        "qty": qty,
        "address": address,
        "status": "pending",
        "time": str(datetime.now())
    }

    orders.append(order)
    save_orders(orders)


# ---------------- WEBHOOK ----------------
@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()

    try:
        msg = data["entry"][0]["changes"][0]["value"]["messages"][0]
        phone = msg["from"]
        text = msg["text"]["body"].lower()

        state = user_state.get(phone, "START")

        print("STATE:", state, "USER:", phone, text)

        # ---------------- START ----------------
        if text in ["hi", "hello", "start"]:
            user_state[phone] = "MENU"
            send_message(phone, "👋 Welcome to Vaishali Foods 🍬\\nReply MENU to continue")

        # ---------------- MENU ----------------
        elif text == "menu" or state == "MENU":
            user_state[phone] = "SELECT_ITEM"
            send_message(phone,
                "🍬 MENU:\\n1. Besan Laddoo - ₹200/kg\\n2. Til Laddoo - ₹250/kg\\nReply 1 or 2"
            )

        # ---------------- ITEM ----------------
        elif state == "SELECT_ITEM":
            if text == "1":
                user_state[phone] = {"step": "QTY", "item": "Besan Laddoo"}
                send_message(phone, "How many kg?")

            elif text == "2":
                user_state[phone] = {"step": "QTY", "item": "Til Laddoo"}
                send_message(phone, "How many kg?")

            else:
                send_message(phone, "Reply 1 or 2")

        # ---------------- QTY ----------------
        elif isinstance(state, dict) and state.get("step") == "QTY":
            state["qty"] = text
            state["step"] = "ADDRESS"
            user_state[phone] = state
            send_message(phone, "Send address")

        # ---------------- ADDRESS ----------------
        elif isinstance(state, dict) and state.get("step") == "ADDRESS":
            state["address"] = text
            state["step"] = "CONFIRM"
            user_state[phone] = state

            send_message(phone,
                f"Order Summary:\\nItem: {state['item']}\\nQty: {state['qty']} kg\\nAddress: {state['address']}\\nReply CONFIRM"
            )

        # ---------------- CONFIRM ----------------
        elif text == "confirm":
            state = user_state.get(phone)

            if isinstance(state, dict):
                create_order(
                    phone,
                    state.get("item"),
                    state.get("qty"),
                    state.get("address")
                )

            send_message(phone, "✅ Order placed successfully!")
            user_state.pop(phone, None)

        else:
            send_message(phone, "Type MENU to start")

    except Exception as e:
        print("ERROR:", e)

    return {"status": "ok"}
