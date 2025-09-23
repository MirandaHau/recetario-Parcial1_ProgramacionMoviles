from flask import Flask
import os
from dotenv import load_dotenv
from config.db import init_db
from flask_jwt_extended import JWTManager

# Importamos los blueprints
from routes.usuarios import usuarios_bp
from routes.recetas import recetas_bp

# Cargar variables de entorno
load_dotenv()

def create_app():
    app = Flask(__name__)

    # Inicializar la base de datos
    init_db(app)

    # Configuración de JWT
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET')
    jwt = JWTManager(app)

    # Registrar los blueprints
    app.register_blueprint(usuarios_bp, url_prefix='/usuarios')
    app.register_blueprint(recetas_bp, url_prefix='/recetas')

    return app

app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)