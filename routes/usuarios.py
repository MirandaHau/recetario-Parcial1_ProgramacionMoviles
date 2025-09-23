from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from flask_bcrypt import Bcrypt
import datetime
from config.db import get_db_connection

usuarios_bp = Blueprint('usuarios', __name__)
bcrypt = Bcrypt()

@usuarios_bp.route('/registrar', methods=['POST'])
def registrar():
    data = request.get_json()
    nombre = data.get('nombre')
    email = data.get('email')
    password = data.get('password')

    if not nombre or not email or not password:
        return jsonify({"error": "Faltan datos"}), 400
    
    cursor = get_db_connection()
    try:
        cursor.execute("SELECT * FROM Usuarios WHERE email = %s", (email,))
        if cursor.fetchone():
            return jsonify({"error": "Ese usuario ya existe"}), 400
        
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        cursor.execute('INSERT INTO Usuarios (nombre, email, password) VALUES (%s, %s, %s)',
                       (nombre, email, hashed_password))
        cursor.connection.commit()
        return jsonify({"mensaje": "El usuario se creo correctamente"}), 201
    except Exception as e:
        return jsonify({"error": f"Error al registrar al usuario: {str(e)}"}), 500
    finally:
        cursor.close()

@usuarios_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Faltan datos"}), 400
    
    cursor = get_db_connection()
    try:
        cursor.execute("SELECT password, id_usuario FROM Usuarios WHERE email = %s", (email,))
        usuario = cursor.fetchone()

        if usuario and bcrypt.check_password_hash(usuario[0], password):
            expires = datetime.timedelta(minutes=60)
            access_token = create_access_token(identity=str(usuario[1]), expires_delta=expires)
            return jsonify({"access_token": access_token})
        else:
            return jsonify({"error": "Credenciales incorrectas"}), 401
    except Exception as e:
        return jsonify({"error": f"Error en el login: {str(e)}"}), 500
    finally:
        cursor.close()