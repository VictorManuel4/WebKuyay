import os
import secrets
from flask import Flask, render_template, request, redirect, url_for, flash, session
from sqlalchemy import create_engine, text
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Configuración de la base de datos
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # Genera una clave aleatoria segura

# URL de conexión a la base de datos (con PyMySQL)
DATABASE_URL = os.getenv("DATABASE_URL").replace("mysql://", "mysql+pymysql://")

# Configuración de SQLAlchemy para Flask
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Crear el motor para conectar con la base de datos
engine = create_engine(DATABASE_URL)

# Modelo de la tabla `clientes`
class Clientes(db.Model):
    __tablename__ = 'clientes'
    id = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(255), nullable=False)
    nombre = db.Column(db.String(255), nullable=False)
    contrasena = db.Column(db.String(255), nullable=False)


@app.route('/')
def index():
    return redirect(url_for('login'))


# Ruta para iniciar sesión
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        contrasena = request.form['contrasena']

        # Verificar credenciales en la tabla clientes
        user = Clientes.query.filter_by(usuario=usuario, contrasena=contrasena).first()
        fecha_hora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        tipo = 'CLIENTE'
        ingreso = 'INGRESO' if user else 'NO INGRESO'

        # Registrar el intento de inicio de sesión en la tabla `registros_entrada`
        try:
            with engine.connect() as connection:
                query = """
                INSERT INTO registros_entrada (usuario, fecha_hora, tipo, ingreso)
                VALUES (:usuario, :fecha_hora, :tipo, :ingreso)
                """
                connection.execute(
                    text(query),
                    {
                        "usuario": usuario,
                        "fecha_hora": fecha_hora,
                        "tipo": tipo,
                        "ingreso": ingreso
                    }
                )
            print("Registro insertado correctamente en registros_entrada.")
        except Exception as e:
            print(f"Error al insertar en registros_entrada: {e}")

        if user:
            session['usuario'] = user.usuario
            session['nombre'] = user.nombre
            return redirect(url_for('mostrar_tabla'))
        else:
            flash('Usuario o contraseña incorrectos', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')


# Ruta para mostrar la tabla de clientes
@app.route('/mostrar_tabla')
def mostrar_tabla():
    if 'usuario' not in session:
        flash('Debes iniciar sesión para acceder a esta página.', 'danger')
        return redirect(url_for('login'))

    # Obtener el nombre del usuario logueado
    nombre_usuario = session['nombre']

    # Filtrar los datos de resumen_clientes donde CLIENTE coincide con el nombre del usuario
    try:
        with engine.connect() as connection:
            query = "SELECT * FROM resumen_clientes WHERE CLIENTE = :nombre_usuario"
            result = connection.execute(text(query), {"nombre_usuario": nombre_usuario})
            clientes = result.fetchall()
    except Exception as e:
        print(f"Error al leer la tabla resumen_clientes: {e}")
        clientes = []

    return render_template('tabla.html', clientes=clientes)


# Ruta para cerrar sesión
@app.route('/logout')
def logout():
    session.pop('usuario', None)
    session.pop('nombre', None)
    flash('Has cerrado sesión.', 'info')
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
