from flask import Blueprint, render_template, abort
from bson.objectid import ObjectId
from app import mongo # Import mongo from the app instance
from datetime import datetime # Import datetime to get the current year

# Create the blueprint for the public preview route
preview_bp = Blueprint('preview_bp', __name__)

@preview_bp.route('/preview/<website_id>')
def preview_website(website_id):
    """
    Renders a live preview of a generated website.
    Fetches the website's structured content from MongoDB and populates a basic HTML
    template.
    This route does NOT require authentication.
    """
    try:
        # Find the website by its ID
        website = mongo.db.websites.find_one({"_id": ObjectId(website_id)})

        if not website:
            abort(404, description="Website not found")

        # Extract the structured content. If 'content' key is missing or not a dict, default to empty.
        content_data = website.get('content', {})
        if not isinstance(content_data, dict):
            content_data = {} # Ensure it's a dictionary for template access

        # Get the current year to pass to the template for the footer
        current_year = datetime.utcnow().year

        # Pass the structured content and current year directly to the template
        return render_template('preview.html', website_data=content_data, current_year=current_year)

    except Exception as e:
        # Construct the full error message as a plain string first
        full_error_message = f"Internal Server Error: Could not generate preview. Details: {str(e)}"
        print(f"ERROR: Preview generation failed for ID {website_id}. Exception type: {type(e)}. Exception: {e}")
        # Pass the pre-formatted string directly to the description argument
        abort(500, description=full_error_message)

