from flask import Blueprint, request, jsonify
from app import mongo, bcrypt # Import mongo and bcrypt from the app instance
from flask_jwt_extended import create_access_token # Import create_access_token
from bson import ObjectId # For working with MongoDB ObjectIds
from datetime import datetime # For timestamps

# Create an authentication blueprint with a URL prefix '/auth'
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/signup', methods=['POST'])
def signup():
    """
    Handles user registration.
    Expects JSON body with 'email' and 'password'.
    """
    data = request.get_json() # Use get_json() to parse JSON body
    email = data.get('email')
    password = data.get('password')

    # Basic input validation
    if not email or not password:
        return jsonify({'msg': 'Email and password are required'}), 400

    # Hash the password for secure storage
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    # Check if a user with the given email already exists
    if mongo.db.users.find_one({'email': email}):
        return jsonify({'msg': 'Email already exists'}), 400

    # Insert the new user into the 'users' collection
    # Default role is 'Viewer'
    user_data = {
        'email': email,
        'password': hashed_password,
        'role': 'Viewer', # Default role for new sign-ups
        'created_at': datetime.utcnow(),
        'last_login': datetime.utcnow()
    }
    result = mongo.db.users.insert_one(user_data)

    return jsonify({'msg': 'User created successfully', 'user_id': str(result.inserted_id)}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Handles user login.
    Expects JSON body with 'email' and 'password'.
    Returns a JWT access token upon successful authentication.
    """
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    # Basic input validation
    if not email or not password:
        return jsonify({'msg': 'Email and password are required'}), 400

    # Find the user by email
    user = mongo.db.users.find_one({'email': email})

    # Verify user existence and password
    if user and bcrypt.check_password_hash(user['password'], password):
        # Create a JWT access token
        # The identity payload will be a dictionary containing user's ID and role
        access_token = create_access_token(identity={
            'id': str(user['_id']), # Convert ObjectId to string for JWT
            'role': user['role']
        })

        # Update last login timestamp
        mongo.db.users.update_one(
            {'_id': user['_id']},
            {'$set': {'last_login': datetime.utcnow()}}
        )

        return jsonify(access_token=access_token), 200
    else:
        return jsonify({'msg': 'Invalid credentials'}), 401