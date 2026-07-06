import requests
from dotenv import load_dotenv
import os

load_dotenv()

PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

# ==========================
# CONFIGURAÇÕES
# ==========================

API_VERSION = "v20.0"

PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

TO_NUMBER = "5511999999999"  # número do aluno (com DDI)

# ==========================
# URL DA API
# ==========================

url = f"https://graph.facebook.com/{API_VERSION}/{PHONE_NUMBER_ID}/messages"

# ==========================
# HEADERS
# ==========================

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json",
}

# ==========================
# DADOS DA MENSAGEM (TEMPLATE)
# ==========================

data = {
    "messaging_product": "whatsapp",
    "to": TO_NUMBER,
    "type": "template",
    "template": {
        "name": "hello_world",
        "language": {
            "code": "en_US"
        }
    }
}

# ==========================
# ENVIO
# ==========================

response = requests.post(url, headers=headers, json=data)

print("STATUS:", response.status_code)
print("RESPOSTA:", response.json())