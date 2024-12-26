from flask import Flask, render_template, request, redirect, url_for
from flask_migrate import Migrate
from models import db, Equipo, Jugador, Movimiento
from sqlalchemy.sql import func
import os
import pandas as pd
from sqlalchemy import create_engine

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///tu_base_de_datos.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
migrate = Migrate(app, db)

# Ruta principal para la lista de equipos
@app.route("/")
def index():
    equipos = Equipo.query.all()
    return render_template("index.html", equipos=equipos)

# Agregar un equipo manualmente
@app.route("/agregar_equipo", methods=["POST"])
def agregar_equipo():
    nombre_equipo = request.form["nombre_equipo"]
    nombre_dt = request.form["nombre_dt"]
    nuevo_equipo = Equipo(nombre=nombre_equipo, dt=nombre_dt, balance=0)
    db.session.add(nuevo_equipo)
    db.session.commit()
    return redirect(url_for("index"))

# Ruta para cargar el archivo Excel y crear el equipo
@app.route("/subir_equipo", methods=["POST"])
def subir_equipo():
    archivo_excel = request.files.get('archivo_excel')
    nombre_equipo = request.form.get('nombre_equipo')
    nombre_dt = request.form.get('nombre_dt')

    print(f"Archivo recibido: {archivo_excel}")
    print(f"Nombre del equipo: {nombre_equipo}")
    print(f"Nombre del DT: {nombre_dt}")

    if archivo_excel and nombre_equipo and nombre_dt:
        try:
            cargar_datos_excel(archivo_excel, nombre_equipo, nombre_dt)
            print("Equipo y jugadores agregados exitosamente")
            return redirect(url_for("index"))
        except Exception as e:
            print(f"Error al procesar el archivo Excel: {e}")
            return redirect(url_for("index"))

    print("Faltan datos en el formulario.")
    return redirect(url_for("index"))

# Función para cargar datos desde Excel
def cargar_datos_excel(archivo_excel, nombre_equipo, nombre_dt):
    try:
        hoja_disponibles = pd.ExcelFile(archivo_excel).sheet_names
        print(f"Hojas disponibles en el archivo Excel: {hoja_disponibles}")
        hoja_a_leer = 'Plantillas' if 'Plantillas' in hoja_disponibles else hoja_disponibles[0]
        print(f"Usando la hoja: {hoja_a_leer}")
        dataframe = pd.read_excel(archivo_excel, sheet_name=hoja_a_leer)

        columnas_requeridas = ['Equipo', 'Nombre del Jugador', 'Sueldo', 'Posición', 'Nacionalidad', 'Edad', 'Media', 'Temporadas']
        for columna in columnas_requeridas:
            if columna not in dataframe.columns:
                raise ValueError(f"Falta la columna requerida: {columna}")
    except Exception as e:
        print(f"Error al leer el archivo Excel: {e}")
        raise e

    equipo_df = dataframe[dataframe['Equipo'].str.contains(nombre_equipo, na=False, case=False)]

    equipo = Equipo.query.filter_by(nombre=nombre_equipo).first()
    if not equipo:
        equipo = Equipo(nombre=nombre_equipo, dt=nombre_dt, balance=0)
        db.session.add(equipo)
        db.session.commit()

    for _, fila in equipo_df.iterrows():
        print(f"Procesando jugador: {fila['Nombre del Jugador']}")
        jugador = Jugador(
            nombre=fila['Nombre del Jugador'],
            salario=fila['Sueldo'],
            posicion=fila['Posición'],
            nacionalidad=fila['Nacionalidad'],
            edad=fila['Edad'],
            media=fila['Media'],
            temporadas=fila['Temporadas'],
            equipo_id=equipo.id
        )
        db.session.add(jugador)

    db.session.commit()

# Eliminar un equipo
@app.route("/eliminar_equipo/<int:id>")
def eliminar_equipo(id):
    equipo = db.session.get(Equipo, id)
    if equipo:
        db.session.delete(equipo)
        db.session.commit()
    return redirect(url_for("index"))

# Detalle de un equipo
@app.route("/equipo/<int:id>")
def detalle_equipo(id):
    equipo = db.session.get(Equipo, id)
    if equipo:
        suma_salarios = db.session.query(func.sum(Jugador.salario)).filter_by(equipo_id=id).scalar() or 0
        suma_ingresos = db.session.query(func.sum(Movimiento.monto)).filter_by(equipo_id=id, tipo="ingreso").scalar() or 0
        suma_egresos = db.session.query(func.sum(Movimiento.monto)).filter_by(equipo_id=id, tipo="egreso").scalar() or 0

        # Balance ajustado según la suma de sueldos
        balance_ajustado = (suma_ingresos - suma_egresos) - suma_salarios
        equipo.balance = balance_ajustado

        print(f"Ingresos: {suma_ingresos}, Egresos: {suma_egresos}, Sueldos: {suma_salarios}, Balance ajustado: {balance_ajustado}")

        db.session.commit()
    else:
        suma_salarios = 0
        balance_ajustado = 0

    return render_template("detalle_equipo.html", equipo=equipo, suma_salarios=suma_salarios, balance_ajustado=balance_ajustado)

# Agregar un jugador
@app.route("/agregar_jugador/<int:equipo_id>", methods=["POST"])
def agregar_jugador(equipo_id):
    nombre_jugador = request.form["nombre_jugador"]
    salario_jugador = int(request.form["salario_jugador"])
    posicion_jugador = request.form["posicion_jugador"]
    nacionalidad = request.form["nacionalidad"]
    edad = int(request.form["edad"])
    media = int(request.form["media"])
    temporadas = int(request.form["temporadas"])

    nuevo_jugador = Jugador(
        nombre=nombre_jugador,
        salario=salario_jugador,
        posicion=posicion_jugador,
        nacionalidad=nacionalidad,
        edad=edad,
        media=media,
        temporadas=temporadas,
        equipo_id=equipo_id
    )
    db.session.add(nuevo_jugador)
    db.session.commit()
    return redirect(url_for("detalle_equipo", id=equipo_id))

# Eliminar un jugador
@app.route("/eliminar_jugador/<int:id>")
def eliminar_jugador(id):
    jugador = db.session.get(Jugador, id)
    equipo_id = jugador.equipo_id
    if jugador:
        db.session.delete(jugador)

        db.session.commit()
    return redirect(url_for("detalle_equipo", id=equipo_id))

# Actualizar balance financiero
@app.route("/actualizar_balance/<int:equipo_id>", methods=["POST"])
def actualizar_balance(equipo_id):
    monto = int(request.form["monto"])
    motivo = request.form["motivo"]
    operacion = request.form["operacion"]

    equipo = db.session.get(Equipo, equipo_id)
    if operacion == "ingreso":
        equipo.balance += monto
        tipo = "ingreso"
    elif operacion == "egreso":
        equipo.balance -= monto
        tipo = "egreso"

    nuevo_movimiento = Movimiento(
        monto=monto,
        motivo=motivo,
        tipo=tipo,
        equipo_id=equipo_id
    )
    db.session.add(nuevo_movimiento)
    db.session.commit()

    return redirect(url_for("detalle_equipo", id=equipo_id))

# Resetear balance
@app.route("/resetear_balance/<int:id>")
def resetear_balance(id):
    equipo = db.session.get(Equipo, id)
    if equipo:
        equipo.balance = 0
        Movimiento.query.filter_by(equipo_id=id).delete()
        db.session.commit()
    return redirect(url_for("detalle_equipo", id=id))

# Eliminar un movimiento financiero
@app.route("/eliminar_movimiento/<int:id>")
def eliminar_movimiento(id):
    movimiento = db.session.get(Movimiento, id)
    if movimiento:
        equipo_id = movimiento.equipo_id
        db.session.delete(movimiento)
        db.session.commit()
    return redirect(url_for("detalle_equipo", id=equipo_id))

if __name__ == "__main__":
    with app.app_context():
        # Ejecuta migraciones automáticamente
        from flask_migrate import upgrade
        upgrade()

    app.run(debug=True)
