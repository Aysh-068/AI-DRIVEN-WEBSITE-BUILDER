import os # <--- ADD THIS LINE TO IMPORT OS MODULE

from app import create_app

# Create the Flask application instance
app = create_app()

# Run the application if this script is executed directly
if __name__ == '__main__':
    # Get the port from the environment variable provided by Render, default to 5000 for local development
    port = int(os.environ.get("PORT", 5000))

    # app.run() will start the development server.
    # host='0.0.0.0' makes the server accessible from outside the local machine, essential for Render.
    # debug=True enables debug mode, which provides helpful error messages
    # and automatically reloads the server on code changes.
    app.run(host='0.0.0.0', port=port, debug=True)