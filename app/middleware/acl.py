from functools import wraps
from flask import jsonify, current_app, request
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from pymongo.errors import PyMongoError
# Import the global mongo instance directly
from app import mongo # <--- MODIFIED: Import mongo directly from app

# Default permissions if database is empty or connection fails
DEFAULT_ROLE_PERMISSIONS = {
    "Admin": [
        "create_user", "read_user", "update_user", "delete_user", "assign_role",
        "create_site", "read_site", "update_site", "delete_site", "list_all_sites",
        "manage_roles_permissions" # New permission for managing roles dynamically
    ],
    "Editor": [
        "create_site", "read_site", "update_site", "delete_site", "list_all_sites"
    ],
    "Viewer": [
        "read_site", "list_all_sites"
    ]
}

# Modify get_permissions_from_db to accept mongo_instance as an argument
def get_permissions_from_db(mongo_instance=None):
    """
    Fetches role permissions from the database. If not found, uses default.
    Accepts an optional mongo_instance to ensure it's available.
    """
    # Use the provided mongo_instance or fallback to the global mongo.db
    # This is safer than current_app.mongo.db in decorator context
    db_instance = mongo_instance if mongo_instance is not None else mongo.db # <--- MODIFIED: Use global mongo.db

    try:
        roles_collection = db_instance.roles_permissions # New collection for roles and permissions

        # Try to find the single document that stores all role permissions
        # We assume one document stores all role-permission mappings for simplicity
        db_permissions = roles_collection.find_one({"_id": "role_mappings"})

        if db_permissions and db_permissions.get("permissions"):
            print("ACL: Loaded permissions from DB.")
            return db_permissions["permissions"]
        else:
            print("ACL: No permissions found in DB, using default and inserting.")
            # If no permissions found, insert defaults
            roles_collection.insert_one({
                "_id": "role_mappings",
                "permissions": DEFAULT_ROLE_PERMISSIONS
            })
            return DEFAULT_ROLE_PERMISSIONS
    except PyMongoError as e:
        print(f"ACL Error: Could not connect to MongoDB or fetch permissions: {e}")
        print("ACL: Falling back to default permissions.")
        return DEFAULT_ROLE_PERMISSIONS
    except Exception as e:
        print(f"ACL Error: An unexpected error occurred while fetching permissions: {e}")
        print("ACL: Falling back to default permissions.")
        return DEFAULT_ROLE_PERMISSIONS

def permission_required(permission):
    """
    Decorator to check if the current user has the required permission.
    Permissions are fetched dynamically from the database.
    """
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            current_user = get_jwt_identity()
            user_role = current_user.get('role')

            # Get permissions dynamically, passing the globally imported mongo.db instance
            all_permissions = get_permissions_from_db(mongo.db) # <--- MODIFIED: Use global mongo.db
            
            # Check if the user's role exists in our defined permissions
            if user_role not in all_permissions:
                return jsonify({"msg": f"Role '{user_role}' not recognized or has no defined permissions."}), 403

            # Check if the role has the required permission
            if permission not in all_permissions[user_role]:
                return jsonify({"msg": f"Permission denied: Missing '{permission}' permission for role '{user_role}'"}), 403

            return fn(*args, **kwargs)
        return decorator
    return wrapper

# This function can be called once during app startup to ensure default permissions are in DB
# It now explicitly passes the mongo instance.
def initialize_permissions(mongo_instance):
    """
    Initializes default permissions in the database if they don't exist.
    This should be called after the Flask app and MongoDB are initialized.
    """
    print("Initializing default permissions...")
    get_permissions_from_db(mongo_instance)
    print("Default permissions initialization complete.")
