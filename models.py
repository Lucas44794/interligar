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

    # Relacionamento: Um usuário pode ter várias instâncias
    instances = db.relationship("Instance", backref="user", lazy=True)


# Modelo para armazenar dados recebidos
class ReceivedData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)  # Armazena os dados recebidos como texto
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())


# Modelo para armazenar instâncias criadas pelos usuários
class Instance(db.Model):
    __tablename__ = 'instance'

    id = db.Column(db.Integer, primary_key=True)
    instance_name = db.Column(db.String(100), unique=True, nullable=False)
    token = db.Column(db.String(255), nullable=True)

    # Relacionamento com o usuário que criou a instância
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)