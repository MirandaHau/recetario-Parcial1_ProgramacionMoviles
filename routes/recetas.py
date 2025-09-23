from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from config.db import get_db_connection

# Creamos el Blueprint para las recetas
recetas_bp = Blueprint('recetas', __name__)

# --- RUTA PARA CREAR UNA NUEVA RECETA ---
@recetas_bp.route('/crear', methods=['POST'])
@jwt_required()
def crear_receta():
    # Obtenemos el ID del usuario del token JWT
    current_user = get_jwt_identity()
    data = request.get_json()

    # Obtenemos los datos de la receta del body de la petición
    titulo = data.get('titulo')
    descripcion = data.get('descripcion')
    ingredientes = data.get('ingredientes')
    instrucciones = data.get('instrucciones')

    # Validamos que los campos necesarios no estén vacíos
    if not titulo or not ingredientes or not instrucciones:
        return jsonify({"error": "El título, los ingredientes y las instrucciones son obligatorios"}), 400
    
    cursor = get_db_connection()
    try:
        # Insertamos la nueva receta en la base de datos, asociándola al usuario actual
        query = '''
            INSERT INTO Recetas (titulo, descripcion, ingredientes, instrucciones, id_usuario) 
            VALUES (%s, %s, %s, %s, %s)
        '''
        cursor.execute(query, (titulo, descripcion, ingredientes, instrucciones, current_user))
        cursor.connection.commit()
        return jsonify({"message": "Receta creada exitosamente"}), 201
    except Exception as e:
        # Manejo de errores
        return jsonify({"error": f"No se pudo crear la receta: {str(e)}"}), 500
    finally:
        cursor.close()

# --- RUTA PARA OBTENER TODAS LAS RECETAS (CATÁLOGO GENERAL) ---
@recetas_bp.route('/', methods=['GET'])
@jwt_required()
def obtener_recetas():
    cursor = get_db_connection()
    try:
        # Seleccionamos todas las recetas y unimos con la tabla de usuarios para obtener el nombre del autor
        query = '''
            SELECT r.id_receta, r.titulo, r.descripcion, u.nombre as autor
            FROM Recetas as r
            INNER JOIN Usuarios as u ON r.id_usuario = u.id_usuario
            ORDER BY r.creado_en DESC
        '''
        cursor.execute(query)
        recetas = cursor.fetchall()
        return jsonify({"recetas": recetas}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()

# --- RUTA PARA OBTENER LAS RECETAS DE UN USUARIO ESPECÍFICO ---
@recetas_bp.route('/mis-recetas', methods=['GET'])
@jwt_required()
def obtener_mis_recetas():
    current_user = get_jwt_identity()
    cursor = get_db_connection()
    try:
        # Seleccionamos solo las recetas del usuario que hace la petición
        query = "SELECT id_receta, titulo, descripcion FROM Recetas WHERE id_usuario = %s"
        cursor.execute(query, (current_user,))
        recetas = cursor.fetchall()
        
        if not recetas:
            return jsonify({"mensaje": "Aún no has creado ninguna receta"}), 404
            
        return jsonify({"recetas": recetas}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# --- RUTA PARA MODIFICAR UNA RECETA ---
@recetas_bp.route('/modificar/<int:id_receta>', methods=['PUT'])
@jwt_required()
def modificar_receta(id_receta):
    current_user = get_jwt_identity()
    data = request.get_json()

    # Obtenemos los nuevos datos
    titulo = data.get('titulo')
    descripcion = data.get('descripcion')
    ingredientes = data.get('ingredientes')
    instrucciones = data.get('instrucciones')

    if not titulo or not ingredientes or not instrucciones:
        return jsonify({"error": "Faltan campos obligatorios"}), 400

    cursor = get_db_connection()
    try:
        # Primero, verificamos que la receta exista y pertenezca al usuario
        cursor.execute("SELECT id_usuario FROM Recetas WHERE id_receta = %s", (id_receta,))
        receta = cursor.fetchone()

        if not receta:
            return jsonify({"error": "Esa receta no existe"}), 404
        
        # El id_usuario en la BD es un entero, lo comparamos con el del token (que es string)
        if receta[0] != int(current_user):
            return jsonify({"error": "No tienes permiso para modificar esta receta"}), 403

        # Si todo está bien, actualizamos la receta
        query = '''
            UPDATE Recetas SET titulo = %s, descripcion = %s, ingredientes = %s, instrucciones = %s
            WHERE id_receta = %s
        '''
        cursor.execute(query, (titulo, descripcion, ingredientes, instrucciones, id_receta))
        cursor.connection.commit()
        return jsonify({"mensaje": "Receta actualizada correctamente"}), 200
    except Exception as e:
        return jsonify({"error": f"Error al actualizar la receta: {str(e)}"}), 500
    finally:
        cursor.close()

# --- RUTA PARA ELIMINAR UNA RECETA ---
@recetas_bp.route('/eliminar/<int:id_receta>', methods=['DELETE'])
@jwt_required()
def eliminar_receta(id_receta):
    current_user = get_jwt_identity()
    cursor = get_db_connection()

    try:
        # Verificamos que la receta exista y pertenezca al usuario
        cursor.execute("SELECT id_usuario FROM Recetas WHERE id_receta = %s", (id_receta,))
        receta = cursor.fetchone()

        if not receta:
            return jsonify({"error": "Esa receta no existe"}), 404
        
        if receta[0] != int(current_user):
            return jsonify({"error": "No tienes permiso para eliminar esta receta"}), 403

        # Eliminamos la receta
        cursor.execute("DELETE FROM Recetas WHERE id_receta = %s", (id_receta,))
        cursor.connection.commit()
        return jsonify({"mensaje": "Receta eliminada correctamente"}), 200
    except Exception as e:
        return jsonify({"error": f"Error al eliminar la receta: {str(e)}"}), 500
    finally:
        cursor.close()