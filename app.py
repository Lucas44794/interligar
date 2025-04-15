from flask import Flask, render_template, request, jsonify, redirect, url_for
import requests
import json
import os
from dotenv import load_dotenv

# Carregar variáveis do .env
load_dotenv()

app = Flask(__name__)

BASE_URL = os.getenv("BASE_URL", "https://evolutionapi.lrcreator.com.br/manager")
API_KEY = os.getenv("A6BHq7T3dUQnzvuAL91gx26Za2jcLye3")

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/create-instance", methods=["POST"])
def create_instance():
    data = request.json
    instance_name = data.get("instanceName")
    number = data.get("number")

    url = f"{BASE_URL}/instance/create"

    payload = json.dumps({
        "instanceName": instance_name,
        "token": "",
        "qrcode": True,
        "mobile": False,
        "number": number,
        "integration": "WHATSAPP-BAILEYS"
    })

    headers = {
        'Content-Type': 'application/json',
        'apikey': 'A6BHq7T3dUQnzvuAL91gx26Za2jcLye3'  # Usando a API Key real do .env
    }

    response = requests.post(url, headers=headers, data=payload)

    if response.status_code == 200:
        response_data = response.json()
        qr_code_link = response_data.get("qrcodeUrl")  # Supondo que a API retorne um link do QR Code
        
        if qr_code_link:
            return redirect(qr_code_link)  # Redireciona para a URL do QR Code
        
        return jsonify(response_data)  # Caso não haja QR Code, retorna a resposta da API
    else:
        return jsonify({"error": response.text}), response.status_code

if __name__ == "__main__":
    app.run(debug=True)