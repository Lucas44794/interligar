from flask import Flask
from models import User, db  # Importa o modelo e a instância do banco de dados
import os

# Aplicativo Flask para inicializar o banco
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Vincular a instância do banco ao Flask
db.init_app(app)

# Inicializar o banco de dados
with app.app_context():
    db.create_all()

def criar_usuario(nickname, senha, role="user"):
    """Função para criar um novo usuário com nível de acesso"""
    with app.app_context():
        # Verificar se o usuário já existe
        existente = User.query.filter_by(username=nickname).first()
        if existente:
            print(f"Erro: O usuário '{nickname}' já existe!")
            return

        # Criar novo usuário
        novo_usuario = User(username=nickname, password=senha, role=role)
        db.session.add(novo_usuario)
        db.session.commit()
        print(f"Usuário '{nickname}' com papel '{role}' criado com sucesso!")

if __name__ == "__main__":
    nickname = input("Digite o nickname para o login: ")
    senha = input("Digite a senha: ")
    role = input("Digite o papel (admin/user): ").lower()

    # Valida o papel para evitar valores inválidos
    if role not in ["admin", "user"]:
        print("Erro: Papel inválido. Escolha 'admin' ou 'user'.")
    else:
        criar_usuario(nickname, senha, role)