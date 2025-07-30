from app import create_app

# Create the Flask application instance
app = create_app()

# Run the application if this script is executed directly
if __name__ == '__main__':
    # app.run() will start the development server.
    # debug=True enables debug mode, which provides helpful error messages
    # and automatically reloads the server on code changes.
    app.run(debug=True)