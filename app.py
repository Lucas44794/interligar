from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy  # Para banco de dados
import requests
import json
from dotenv import load_dotenv
import os
from flask_migrate import Migrate


app = Flask(__name__)
app.secret_key = "sua_chave_secreta"  # Necessário para a sessão

# Configurar banco de dados SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

migrate = Migrate(app, db)


# Carregar variáveis do .env
load_dotenv()

API_KEY = os.getenv("API_KEY")
BASE_URL = os.getenv("BASE_URL")
ENDPOINT = os.getenv("ENDPOINT")
URL = f'{BASE_URL}/{ENDPOINT}'

# Modelo de Usuário
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

# Inicializar o banco de dados
with app.app_context():
    db.create_all()

# Página de login
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Verificar usuário no banco de dados
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session["user_id"] = user.id  # Armazena o ID do usuário na sessão
            return redirect(url_for("user_dashboard"))
        else:
            return render_template("login.html", error="Usuário ou senha incorretos.")
    return render_template("login.html")


# Painel único do usuário
@app.route("/dashboard", methods=["GET"])
def user_dashboard():
    if "user_id" in session:
        user = User.query.get(session["user_id"])
        return render_template("dashboard.html", username=user.username)  # Exibe informações do usuário
    return redirect(url_for("login"))

# Logout
@app.route("/logout", methods=["GET"])
def logout():
    session.pop("user_id", None)
    return redirect(url_for("login"))


# Função existente de criação de instância
@app.route("/create-instance", methods=["POST"])
def create_instance():
    if "user_id" in session:  # Verifica se o usuário está logado
        data = request.json
        print("Dados recebidos:", data)
        instance_name = data.get("instanceName")

        payload = json.dumps({
            "instanceName": f"{instance_name}",
            "token": "",
            "qrcode": True,
            "mobile": False,
            "reject_call": True,
            "msg_call": "Desculpe, não consigo aceitar ligações",
            "groups_ignore": True,
            "integration": "WHATSAPP-BAILEYS"
        })
        headers = {
            'Content-Type': 'application/json',
            'apikey': f'{API_KEY}'  # Usando a API Key real do .env
        }
        print(f"Payload {payload}")
        print(f"Headers {headers}")
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
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)