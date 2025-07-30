import os # Keep this import if you use os.environ elsewhere in your app, otherwise it can be removed if only used for the app.run() block

from app import create_app

# Create the Flask application instance
app = create_app()

# No if __name__ == '__main__': block here anymore.
# Gunicorn will directly import and run the 'app' instance.