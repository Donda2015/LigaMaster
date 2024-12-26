from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Equipo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    dt = db.Column(db.String(100), nullable=True)  # Director técnico
    balance = db.Column(db.Integer, default=0)
    jugadores = db.relationship('Jugador', backref='equipo', lazy=True, cascade="all, delete-orphan")
    movimientos = db.relationship('Movimiento', backref='equipo', lazy=True, cascade="all, delete-orphan")

class Jugador(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    salario = db.Column(db.Integer, nullable=False)
    posicion = db.Column(db.String(50), nullable=True)
    nacionalidad = db.Column(db.String(50), nullable=True)
    edad = db.Column(db.Integer, nullable=True)
    media = db.Column(db.Integer, nullable=True)
    temporadas = db.Column(db.Integer, nullable=True)
    equipo_id = db.Column(db.Integer, db.ForeignKey('equipo.id'), nullable=False)

class Movimiento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    monto = db.Column(db.Integer, nullable=False)
    motivo = db.Column(db.String(200), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)  # "ingreso" o "egreso"
    equipo_id = db.Column(db.Integer, db.ForeignKey('equipo.id'), nullable=False)
