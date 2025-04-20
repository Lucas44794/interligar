from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_sqlalchemy import SQLAlchemy  # Para banco de dados
import requests
import json
from dotenv import load_dotenv
import os
from flask_migrate import Migrate
from models import db, User, ReceivedData
from flask_cors import CORS
from sqlalchemy.sql import text

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Gerar uma chave segura automaticamente
CORS(app)  # Habilitar CORS

# Configurar banco de dados SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
migrate = Migrate(app, db)

# Carregar variáveis do .env
load_dotenv()
webhookUrl = os.getenv("webhookUrl")
API_KEY = os.getenv("API_KEY")
BASE_URL = os.getenv("BASE_URL")
ENDPOINT = os.getenv("ENDPOINT")
URL = f'{BASE_URL}/{ENDPOINT}'


def verificar_banco_de_dados():
    """Verifica se o banco de dados existe e cria se necessário."""
    if not os.path.exists("users.db"):
        with app.app_context():
            db.create_all()
            print("Banco de dados criado com sucesso!")


# Inicializar o banco de dados
with app.app_context():
    db.create_all()


@app.route("/", methods=["GET", "POST"])
def login():
    """Página de login."""
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


@app.route("/dashboard", methods=["GET"])
def user_dashboard():
    """Painel único do usuário."""
    if "user_id" in session:
        user = User.query.get(session["user_id"])
        return render_template("dashboard.html", username=user.username)  # Exibe informações do usuário
    return redirect(url_for("login"))


@app.route("/logout", methods=["GET"])
def logout():
    """Fazer logout do sistema."""
    session.pop("user_id", None)
    return redirect(url_for("login"))


@app.route("/create-instance", methods=["GET", "POST"])
def create_instance():
    """
    Rota para criar instâncias. Suporta envio de dados via formulário (GET) e JSON (POST).
    """
    if request.method == "POST":
        # Aceita JSON ou dados enviados pelo formulário
        data = request.json if request.json else request.form.to_dict()

        instance_name = data.get("instanceName")
        

        payload = {
            "instanceName": instance_name,
            "token": "",
            "qrcode": True,
            "mobile": False,
            
            "integration": "WHATSAPP-BAILEYS",
            "reject_call": True,
            "msg_call": "Desculpe, não consigo aceitar ligações",
            "groups_ignore": True,
            "webhook": "{{webhookUrl}}",
            "webhook_by_events": False,
            "events": [
                "QRCODE_UPDATED"
                ]
        }

        headers = {
            'Content-Type': 'application/json',
            'apikey': f'{API_KEY}'
        }

        response = requests.post(URL, headers=headers, json=payload)

        if response.status_code == 201:
            response_data = response.json()
            qr_code_link = response_data.get("qr_code_link", None)
            if qr_code_link:
                return redirect(qr_code_link)  # Redireciona para a URL do QR Code
            return jsonify({"success": "Conectado com Sucesso", "data": response_data})
        else:
            return jsonify({"error": response.text}), response.status_code

    return render_template("instance_creator.html")


@app.route("/receber_dados", methods=["POST"])
def criar_resposta():
    """Receber dados e salvar no banco de dados."""
    data = request.json  # Captura os dados enviados pelo cliente

    if data:
        # Criar uma nova entrada no banco de dados
        received_entry = ReceivedData(content=json.dumps(data))  # Converte o JSON em string

        db.session.add(received_entry)  # Adiciona à sessão
        db.session.commit()  # Confirma a transação

        return jsonify({"success": "Dados salvos com sucesso!", "data": data}), 201
    return jsonify({"error": "Nenhum dado recebido"}), 400


@app.route("/admin/bancodedados")
def visualizar_banco():
    """Rota para visualizar os dados do banco de dados."""
    if "user_id" in session:  # Verifica se o usuário está logado
        tabelas = db.metadata.tables.keys()
        dados = {}

        for tabela in tabelas:
            query = db.session.execute(text(f"SELECT * FROM {tabela}")).fetchall()
            colunas = db.metadata.tables[tabela].columns.keys()
            dados[tabela] = [dict(zip(colunas, row)) for row in query]

        return render_template("admin_bancodedados.html", dados=dados)  # Exibe na página HTML
    return redirect(url_for("login"))



@app.route("/register", methods=["GET", "POST"])
def criar_usuario():
    """
    Rota para a criação de novos usuários.
    """
    if request.method == "POST":
        # Obtém os dados do formulário
        nickname = request.form.get("username")
        senha = request.form.get("password")
        role = request.form.get("role", "user").lower()
        
        if role not in ["admin", "user"]:  # Validação do papel
            flash("Papel inválido. Escolha 'admin' ou 'user'.", "danger")
            return redirect(url_for("criar_usuario"))
        
        with app.app_context():
            # Verificar se o usuário já existe
            existente = User.query.filter_by(username=nickname).first()
            if existente:
                flash(f"O usuário '{nickname}' já existe!", "danger")
                return redirect(url_for("criar_usuario"))
            
            # Criar novo usuário
            novo_usuario = User(username=nickname, password=senha, role=role)
            db.session.add(novo_usuario)
            db.session.commit()
            flash(f"Usuário '{nickname}' criado com sucesso!", "success")
            return redirect(url_for("login"))
    
    return render_template("register.html")

if __name__ == "__main__":
    verificar_banco_de_dados()
    app.run(debug=True)