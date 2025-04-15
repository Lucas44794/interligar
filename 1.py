from flask import Flask, render_template, request, jsonify, redirect, url_for
import requests
import json
from dotenv import load_dotenv
import os

app = Flask(__name__)

# Carregar variáveis do .env
load_dotenv()

API_KEY = os.getenv("API_KEY")
BASE_URL = os.getenv("BASE_URL")
ENDPOINT = os.getenv("ENDPOINT")
URL = f'{BASE_URL}/{ENDPOINT}'
print(URL)
print(API_KEY)


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")




@app.route("/create-instance", methods=["POST"])
def create_instance():

    data = request.json
    print("Dados recebidos:", data)
    instance_name = data.get("instanceName")
    number = data.get("number")

    payload = json.dumps({
    "instanceName": f"{instance_name}",
    "token": "",
    "qrcode": True,
    "mobile": False,
    "number": f"{number}",
    "integration": "WHATSAPP-BAILEYS"
    })
    headers = {
    'Content-Type': 'application/json',
    'apikey': f'{API_KEY}'  # Usando a API Key real do .env
    }

    response = requests.request("POST", URL, headers=headers, data=payload)

    print(response)

    if response.status_code == 201:
        response_data = response.json()
        qr_code_link = "Seu Qr Code"  # Supondo que a API retorne um link do QR Code
        
        if qr_code_link:
            return redirect(qr_code_link)  # Redireciona para a URL do QR Code
        
        return jsonify("Conectado com Sucesso")  # Caso não haja QR Code, retorna a resposta da API
    else:
        return jsonify({"error": response.text}), response.status_code
    

if __name__ == "__main__":
    app.run(debug=True)
