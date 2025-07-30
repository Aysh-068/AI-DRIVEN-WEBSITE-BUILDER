from flask import Blueprint, send_from_directory
import os

frontend_bp = Blueprint('frontend', __name__, static_folder='../../frontend')

@frontend_bp.route('/login.html')
def serve_login():
    return send_from_directory(frontend_bp.static_folder, 'login.html')

@frontend_bp.route('/signup.html')
def serve_signup():
    return send_from_directory(frontend_bp.static_folder, 'signup.html')

@frontend_bp.route('/dashboard.html')
def serve_dashboard():
    return send_from_directory(frontend_bp.static_folder, 'dashboard.html')

@frontend_bp.route('/scripts.js')
def serve_scripts():
    return send_from_directory(frontend_bp.static_folder, 'scripts.js')
