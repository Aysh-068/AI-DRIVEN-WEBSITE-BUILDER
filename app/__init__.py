from flask import Flask, jsonify, send_from_directory
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from dotenv import load_dotenv
import os

# Load environment variables from .env file at the very start
load_dotenv()

# Initialize extensions globally (they will be initialized with the app later)
mongo = PyMongo()
bcrypt = Bcrypt()
jwt = JWTManager()

def create_app():
    """
    Creates and configures the Flask application.
    This uses the Application Factory pattern.
    """
    app = Flask(__name__)

    # --- Configuration ---
    # MongoDB URI for database connection
    app.config['MONGO_URI'] = os.getenv('MONGO_URI')
    # Secret key for JWT token signing (must be a strong, random string)
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
    # Configure JWT to store identity as a dictionary (user_id, role)
    app.config['JWT_IDENTITY_CLAIM'] = 'user' # The key in the JWT payload for identity
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 3600 # Token expires in 1 hour (3600 seconds)

    # --- Initialize Extensions with the app instance ---
    # Enable Cross-Origin Resource Sharing for all origins by default.
    # This is important for frontend running on a different origin (e.g., file:// or different port).
    CORS(app)
    # Initialize PyMongo with the Flask app
    mongo.init_app(app)
    
    # Initialize Bcrypt for password hashing
    bcrypt.init_app(app)
    # Initialize JWTManager for JWT handling
    jwt.init_app(app)

    # --- Register Blueprints ---
    # Blueprints organize your application into modular components.
    # Each blueprint handles a specific set of routes.

    # Import blueprints from the routes package
    from .routes.auth import auth_bp
    from .routes.website import website_bp
    from .routes.admin import admin_bp
    from .routes.preview import preview_bp

    # Register authentication blueprint with a URL prefix '/auth'
    app.register_blueprint(auth_bp, url_prefix='/auth')
    # Register website management blueprint with a URL prefix '/api'
    app.register_blueprint(website_bp, url_prefix='/api')
    # Register admin management blueprint with a URL prefix '/admin'
    app.register_blueprint(admin_bp, url_prefix='/admin')
    # Register preview blueprint without a URL prefix, so it's directly accessible at '/preview/<id>'
    app.register_blueprint(preview_bp)

    # --- Root Route to serve frontend/index.html ---
    @app.route('/')
    def serve_index():
        """
        Serves the index.html file from the frontend directory when the root URL is accessed.
        """
        root_dir = os.path.dirname(os.path.abspath(__file__))
        frontend_dir = os.path.join(root_dir, '..', 'frontend')
        return send_from_directory(frontend_dir, 'index.html')

    # --- Serve other static frontend files (HTML, CSS, JS) ---
    # This route will catch requests for files like /login.html, /signup.html, /scripts.js etc.
    @app.route('/<path:filename>')
    def serve_frontend_static(filename):
        """
        Serves other static files (HTML, CSS, JS) from the frontend directory.
        """
        root_dir = os.path.dirname(os.path.abspath(__file__))
        frontend_dir = os.path.join(root_dir, '..', 'frontend')
        return send_from_directory(frontend_dir, filename)

    # --- JWT Error Handlers ---
    # These handlers provide custom responses for JWT-related errors.

    @jwt.unauthorized_loader
    def unauthorized_response(callback):
        """Callback for when a user tries to access a protected endpoint without a token."""
        return jsonify({"msg": "Missing Authorization Header or Token"}), 401

    @jwt.invalid_token_loader
    def invalid_token_response(callback):
        """Callback for when a token is invalid (e.g., malformed, bad signature)."""
        return jsonify({"msg": "Signature verification failed or token is malformed"}), 401

    @jwt.expired_token_loader
    def expired_token_response(callback):
        """Callback for when a token has expired."""
        return jsonify({"msg": "Token has expired"}), 401

    @jwt.needs_fresh_token_loader
    def needs_fresh_token_response(callback):
        """Callback for when a token is not fresh but fresh token is required."""
        return jsonify({"msg": "Fresh token required"}), 401

    @jwt.revoked_token_loader
    def revoked_token_response(callback):
        """Callback for when a token has been revoked."""
        return jsonify({"msg": "Token has been revoked"}), 401

    return app
