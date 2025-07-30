from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import mongo, bcrypt # Import mongo and bcrypt
from app.middleware.acl import permission_required
from bson import ObjectId # For working with MongoDB ObjectIds

# Create an admin blueprint with a URL prefix '/admin'
admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/users', methods=['GET'])
@jwt_required()
@permission_required('read_user')
def list_users():
    """
    Lists all users in the system. Only accessible by Admins.
    """
    try:
        users_cursor = mongo.db.users.find({})
        users_list = []
        for user in users_cursor:
            user['_id'] = str(user['_id']) # Convert ObjectId to string
            # Exclude sensitive information like password hash
            users_list.append({
                '_id': user['_id'],
                'email': user['email'],
                'role': user['role'],
                'created_at': user['created_at'].isoformat() if 'created_at' in user else None,
                'last_login': user['last_login'].isoformat() if 'last_login' in user else None
            })
        return jsonify(users_list), 200
    except Exception as e:
        print(f"ERROR in list_users: {e}")
        return jsonify({'msg': 'Internal Server Error listing users', 'error_details': str(e)}), 500

@admin_bp.route('/assign-role', methods=['PUT'])
@jwt_required()
@permission_required('assign_role')
def assign_role():
    """
    Assigns a new role to a specified user. Only accessible by Admins.
    Expects JSON body with 'user_id' and 'role'.
    """
    data = request.get_json()
    user_id = data.get('user_id')
    new_role = data.get('role')

    if not user_id or not new_role:
        return jsonify({'msg': 'User ID and new role are required'}), 400

    # Define allowed roles
    allowed_roles = ['Admin', 'Editor', 'Viewer']
    if new_role not in allowed_roles:
        return jsonify({'msg': f'Invalid role. Allowed roles are: {", ".join(allowed_roles)}'}), 400

    try:
        # Prevent an admin from changing their own role via this endpoint (optional, but good practice)
        current_user_identity = get_jwt_identity()
        if str(current_user_identity['id']) == user_id:
            return jsonify({'msg': 'Cannot change your own role via this interface'}), 403

        # Update the user's role in the database
        result = mongo.db.users.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': {'role': new_role}}
        )

        if result.matched_count == 0:
            return jsonify({'msg': 'User not found'}), 404
        elif result.modified_count == 0:
            return jsonify({'msg': 'Role already set to this value or no changes made'}), 200 # No change needed
        else:
            return jsonify({'msg': 'User role updated successfully'}), 200
    except Exception as e:
        print(f"ERROR in assign_role: {e}")
        return jsonify({'msg': 'Internal Server Error assigning role', 'error_details': str(e)}), 500

@admin_bp.route('/users/<id>', methods=['DELETE'])
@jwt_required()
@permission_required('delete_user')
def delete_user(id):
    """
    Deletes a user by ID. Only accessible by Admins.
    """
    current_user_identity = get_jwt_identity()
    current_user_id = current_user_identity['id']

    if current_user_id == id:
        return jsonify({'msg': 'Cannot delete your own user account via this interface'}), 403

    try:
        result = mongo.db.users.delete_one({'_id': ObjectId(id)})

        if result.deleted_count == 1:
            return jsonify({'msg': 'User deleted successfully'}), 200
        else:
            return jsonify({'msg': 'User not found'}), 404
    except Exception as e:
        print(f"ERROR in delete_user: {e}")
        return jsonify({'msg': 'Internal Server Error deleting user', 'error_details': str(e)}), 500