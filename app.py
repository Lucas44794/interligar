from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_sqlalchemy import SQLAlchemy  # Para banco de dados
import requests
import json
from dotenv import load_dotenv
import os
import base64
import os
import time
from PIL import Image
from io import BytesIO
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


def configurar_webhook(api_url, api_key, instance_name, webhook_url):
    """Função para configurar um webhook via API."""
    
    url = f"{api_url}/webhook/set/{instance_name}"
    
    headers = {
        "Content-Type": "application/json",
        "apikey": api_key
    }
    
    data = {
        "url": webhook_url,
        "webhook_by_events": False,
        "webhook_base64": False,
        "events": [
            "QRCODE_UPDATED",
            "MESSAGES_UPSERT",
            "MESSAGES_UPDATE",
            "MESSAGES_DELETE",
            "SEND_MESSAGE",
            "CONNECTION_UPDATE",
            "CALL"
        ]
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": response.text, "status_code": response.status_code}



@app.route("/create-instance", methods=["GET", "POST"])
def create_instance():
    """
    Rota para criar instâncias. Suporta envio de dados via formulário (GET) e JSON (POST).
    """
    if request.method == "POST":
        # Aceita JSON ou dados enviados pelo formulário
        data = request.json if request.json else request.form.to_dict()

        instance_name = data.get("instanceName")
        token = instance_name + "+150"  
        webhook_url = "https://sistema.lrcreator.com.br/receber_dados"
        

        payload = {
            "instanceName": instance_name,
            "token": token,
            "qrcode": True,
            "integration": "WHATSAPP-BAILEYS",
            "reject_call": True,
            "msg_call": "Desculpe, não consigo aceitar ligações",
            "groups_ignore": True,
        }

        headers = {
            'Content-Type': 'application/json',
            'apikey': f'{API_KEY}'
        }

        response = requests.post(URL, headers=headers, json=payload)


        if response.status_code == 201:
            response_data = response.json()
            qr_code_base64 = response_data.get("data", {}).get("qrcode", {}).get("base64")

            if webhook_url:
                webhook_response = configurar_webhook(BASE_URL, API_KEY, instance_name, webhook_url)
                response_data["webhook_setup"] = webhook_response

            if qr_code_base64 and qr_code_base64.startswith("data:image/png;base64,"):
                qr_code_base64 = qr_code_base64.replace("data:image/png;base64,", "")

                # Criar a imagem temporária
                nome_arquivo = "static/qrcode_temp.png"
                criar_imagem(qr_code_base64, nome_arquivo)

                return render_template("exibir_qrcode.html", qr_code=nome_arquivo)

  # Redireciona para a URL do QR Code
            return jsonify({"success": "Conectado com Sucesso", "data": response_data})
        else:
            return jsonify({"error": response.text}), response.status_code

    return render_template("instance_creator.html")


@app.route("/receber_dados", methods=["POST"])
def criar_resposta():
    """Recebe dados e salva no banco de dados, gerando uma imagem se necessário."""
    data = request.json  # Captura os dados enviados pelo cliente

    if not data:
        return jsonify({"error": "Nenhum dado recebido"}), 400

    # Verifica se o evento é "qrcode.updated"
    if data.get("event") == "qrcode.updated":
        # Obtém o base64 da imagem dentro do JSON
        base64_str = data.get("data", {}).get("qrcode", {}).get("base64")

        if base64_str and base64_str.startswith("data:image/png;base64,"):
            base64_str = base64_str.replace("data:image/png;base64,", "")  # Remove o prefixo

            # Cria a imagem
            nome_arquivo = "qrcode_temp.png"
            criar_imagem(base64_str, nome_arquivo)

        else:
            return jsonify({"error": "Base64 inválido ou ausente"}), 400

    # Salva os dados no banco de dados
    received_entry = ReceivedData(content=json.dumps(data))
    db.session.add(received_entry)
    db.session.commit()

    return jsonify({"success": "Dados salvos com sucesso!", "data": data}), 201

def criar_imagem(base64_str, nome_arquivo, tempo_expiracao=30):
    """Cria uma imagem a partir do código base64 e a exclui após o tempo determinado."""
    try:
        img_data = base64.b64decode(base64_str)

        # Criar a imagem
        imagem = Image.open(BytesIO(img_data))
        imagem.save(nome_arquivo)

        print(f"Imagem salva como {nome_arquivo}. Será apagada em {tempo_expiracao} segundos.")

        # Aguarda o tempo de expiração e exclui a imagem
        time.sleep(tempo_expiracao)
        os.remove(nome_arquivo)
        print(f"Imagem {nome_arquivo} removida.")

    except Exception as e:
        print(f"Erro ao criar a imagem: {e}")



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