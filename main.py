user_state = {}
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
import requests

app = FastAPI()

VERIFY_TOKEN = "vaishali123"

ACCESS_TOKEN = "EAAOdkFrIZC94BRoLSdTEuadBF26OvCZCIm4McelzFaodWmIjzwpdSZAMSf806gPTLOoNavySowsORC35PVm4mdGLAs0K9o4OmnFIjDsMfkKZBYs6M6at1JdIZBZAeSQAZCaVIYPghXZCMGQo4EL9CuD36JhtuVFML5nqnHAtWvaOWo6cQfaxflvEF7jmyZAvxrADOQ2xZBrZC8Rl4LdQKBdw8YsKbRhZBdJJAVerPWxEIrT0NCrIqURqADa7vSvBIhbEjLrp8uaybCTS6RHZC0o9AknYr"
PHONE_NUMBER_ID = "1160798840444641"


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
    url = f"https://graph.facebook.com/v20.0/1160798840444641/messages"

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

    response = requests.post(url, headers=headers, json=data)

    print("SEND STATUS:", response.status_code)
    print("SEND RESPONSE:", response.text)


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
            send_message(phone,
                "👋 Welcome to Vaishali Foods 🍬\n\nReply MENU to continue"
            )

        # ---------------- MENU ----------------
        elif text == "menu" or state == "MENU":
            user_state[phone] = "SELECT_ITEM"
            send_message(phone,
                "🍬 MENU:\n"
                "1. Besan Laddoo - ₹200/kg\n"
                "2. Til Laddoo - ₹250/kg\n\n"
                "Reply 1 or 2 to select"
            )

        # ---------------- ITEM SELECT ----------------
        elif state == "SELECT_ITEM":
            if text == "1":
                user_state[phone] = {"step": "QTY", "item": "Besan Laddoo"}
                send_message(phone, "How many kg do you want?")

            elif text == "2":
                user_state[phone] = {"step": "QTY", "item": "Til Laddoo"}
                send_message(phone, "How many kg do you want?")

            else:
                send_message(phone, "Please reply 1 or 2")

        # ---------------- QUANTITY ----------------
        elif isinstance(state, dict) and state.get("step") == "QTY":
            state["qty"] = text
            state["step"] = "ADDRESS"
            user_state[phone] = state

            send_message(phone, "📍 Send your delivery address")

        # ---------------- ADDRESS ----------------
        elif isinstance(state, dict) and state.get("step") == "ADDRESS":
            state["address"] = text
            user_state[phone] = state

            send_message(phone,
                f"🧾 Order Summary:\n"
                f"Item: {state['item']}\n"
                f"Qty: {state['qty']} kg\n"
                f"Address: {state['address']}\n\n"
                f"Reply CONFIRM to place order"
            )

            state["step"] = "CONFIRM"
            user_state[phone] = state

        # ---------------- CONFIRM ----------------
        elif text == "confirm":
            send_message(phone,
                "✅ Order placed successfully!\nWe will contact you soon 🍬"
            )
            user_state.pop(phone, None)

        else:
            send_message(phone, "Type MENU to start ordering 🍬")

    except Exception as e:
        print("ERROR:", e)

    return {"status": "ok"}