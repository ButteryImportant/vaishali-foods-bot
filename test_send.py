import requests

ACCESS_TOKEN = "EAAOdkFrIZC94BRtORbqeEYHYUTRZCW1R5maLlQxLYAjRok2pOa6wdZCAu4JCkmRFxX8XNUHZAh7YQahIlS84uKzmhOsPisMxIogmO790WgtvjNsRr1WUIQZBMAbMxLKW35VmKLiTY9GuLqR7co6PfFAZCZAadyqlPdIPlr4HfnUlFnp9ZBPWoc3ZCd6mRgcYkJWJgLvlxdXlzV1JkEZA2MVhhYvq8ZB7D850OWJzf2qaXIwrevZCvpMzvbVUOYKPcv8Cu8g7XZCVINK1KjxqHNBPoRvZCT"
PHONE_NUMBER_ID = "1160798840444641"

def send_message():
    url = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    data = {
        "messaging_product": "whatsapp",
        "to": "918433779505",
        "type": "text",
        "text": {
            "body": "Hello from Vaishali Foods 🍬"
        }
    }

    response = requests.post(url, headers=headers, json=data)

    print("STATUS CODE:", response.status_code)
    print("RESPONSE:", response.text)

send_message()