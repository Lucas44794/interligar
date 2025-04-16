from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


# Modelo de Usuário
class User(db.Model):
    __tablename__ = 'user'
    __table_args__ = {'extend_existing': True}  # Permite reusar a tabela existente

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="user")