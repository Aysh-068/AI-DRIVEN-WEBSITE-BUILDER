from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import mongo
from app.middleware.acl import permission_required
from bson import ObjectId
from datetime import datetime
import os
import json

import google.generativeai as genai
from google.api_core.exceptions import GoogleAPIError, InvalidArgument, ResourceExhausted

website_bp = Blueprint('website', __name__)
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def generate_gemini_content(business_type, industry):
    model = genai.GenerativeModel('gemini-1.5-flash')

    prompt_text = (
        f"Generate a detailed JSON structure for a website for a '{business_type}' business "
        f"in the '{industry}' industry. The JSON should follow this exact schema for easy parsing. "
        f"The 'services_section.items' array must contain at least 3 service items. Each item must include a 'title' and a 'description'. "
        f"Do not return an empty array. If unsure, make up relevant sample services based on the business type. "
        f"Make the content engaging and relevant to the business and industry. "
        f"Additionally, generate a 'theme' object with distinct color palettes and a suitable font family "
        f"for this type of business. The colors should be in hexadecimal format (e.g., '#RRGGBB'). "
        f"The entire response MUST be a valid JSON object."
    )

    response_schema = {
        "type": "OBJECT",
        "properties": {
            "title": {"type": "STRING"},
            "hero_section": {
                "type": "OBJECT",
                "properties": {
                    "heading": {"type": "STRING"},
                    "subheading": {"type": "STRING"},
                    "image_description": {"type": "STRING"}
                }
            },
            "about_section": {
                "type": "OBJECT",
                "properties": {
                    "heading": {"type": "STRING"},
                    "text": {"type": "STRING"}
                }
            },
            "services_section": {
                "type": "OBJECT",
                "properties": {
                    "heading": {"type": "STRING"},
                    "items": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "title": {"type": "STRING"},
                                "description": {"type": "STRING"}
                            }
                        }
                    }
                }
            },
            "contact_section": {
                "type": "OBJECT",
                "properties": {
                    "heading": {"type": "STRING"},
                    "email": {"type": "STRING"},
                    "phone": {"type": "STRING"},
                    "address": {"type": "STRING"}
                }
            },
            "theme": {
                "type": "OBJECT",
                "properties": {
                    "primary_color": {"type": "STRING"},
                    "secondary_color": {"type": "STRING"},
                    "background_color": {"type": "STRING"},
                    "text_color": {"type": "STRING"},
                    "heading_color": {"type": "STRING"},
                    "font_family": {"type": "STRING"},
                    "section_bg_color": {"type": "STRING"},
                    "service_item_bg_color": {"type": "STRING"},
                    "border_color": {"type": "STRING"},
                    "shadow_color": {"type": "STRING"}
                },
                "required": [
                    "primary_color", "secondary_color", "background_color", "text_color",
                    "heading_color", "font_family", "section_bg_color", "service_item_bg_color",
                    "border_color", "shadow_color"
                ]
            }
        },
        "required": [
            "title", "hero_section", "about_section", "services_section", "contact_section", "theme"
        ]
    }

    try:
        response = model.generate_content(
            prompt_text,
            generation_config={
                "response_mime_type": "application/json",
                "response_schema": response_schema,
                "temperature": 0.7,
                "max_output_tokens": 1500
            }
        )
        generated_json_str = response.text
        print("🔎 Gemini JSON Response (raw):")
        print(generated_json_str)
        return json.loads(generated_json_str)

    except (InvalidArgument, ResourceExhausted, GoogleAPIError) as e:
        print(f"Gemini API Error: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from Gemini API: {e}. Raw response: {generated_json_str}")
        return None
    except Exception as e:
        print(f"Unexpected error during Gemini content generation: {e}")
        return None

@website_bp.route('/generate', methods=['POST'])
@jwt_required()
@permission_required('create_site')
def generate_website():
    data = request.get_json()
    business_type = data.get('business_type')
    industry = data.get('industry')

    if not business_type or not industry:
        return jsonify({'msg': 'Business type and industry are required'}), 400

    current_user_identity = get_jwt_identity()
    owner_id = current_user_identity['id']

    generated_content = generate_gemini_content(business_type, industry)

    if generated_content and \
       'services_section' in generated_content and \
       isinstance(generated_content['services_section'].get('items'), list) and \
       len(generated_content['services_section']['items']) > 0:

        site_data = {
            'owner': owner_id,
            'business_type': business_type,
            'industry': industry,
            'content': generated_content,
            'created_at': datetime.utcnow(),
            'last_updated': datetime.utcnow()
        }
        result = mongo.db.websites.insert_one(site_data)
        return jsonify({'msg': 'Website created successfully', 'id': str(result.inserted_id)}), 201
    else:
        return jsonify({'msg': 'AI failed to generate valid services. Please try again or retry with different inputs.'}), 500

@website_bp.route('/', methods=['GET'])
@jwt_required()
@permission_required('list_all_sites')
def list_websites():
    try:
        current_user_identity = get_jwt_identity()
        user_role = current_user_identity['role']
        current_user_id = current_user_identity['id']

        if user_role == 'Admin':
            websites_cursor = mongo.db.websites.find({})
        else:
            websites_cursor = mongo.db.websites.find({})

        websites_list = []
        for site in websites_cursor:
            site['_id'] = str(site['_id'])
            websites_list.append({
                '_id': site['_id'],
                'business_type': site.get('business_type', 'N/A'),
                'industry': site.get('industry', 'N/A'),
                'owner_id': site.get('owner', 'N/A')
            })
        return jsonify(websites_list), 200

    except Exception as e:
        print(f"ERROR in list_websites: {e}")
        return jsonify({"msg": "Internal Server Error loading websites", "error_details": str(e)}), 500

@website_bp.route('/<id>', methods=['GET'])
@jwt_required()
@permission_required('read_site')
def get_website(id):
    try:
        site = mongo.db.websites.find_one({'_id': ObjectId(id)})
        if not site:
            return jsonify({'msg': 'Website not found'}), 404

        site['_id'] = str(site['_id'])
        site['created_at'] = site['created_at'].isoformat() if 'created_at' in site else None
        site['last_updated'] = site['last_updated'].isoformat() if 'last_updated' in site else None

        return jsonify(site), 200
    except Exception as e:
        print(f"ERROR in get_website: {e}")
        return jsonify({'msg': 'Internal Server Error retrieving website', 'error_details': str(e)}), 500

@website_bp.route('/<id>', methods=['PUT'])
@jwt_required()
@permission_required('update_site')
def update_website(id):
    data = request.get_json()
    if not data:
        return jsonify({'msg': 'No data provided for update'}), 400

    current_user_identity = get_jwt_identity()
    user_id = current_user_identity['id']
    user_role = current_user_identity['role']

    try:
        site = mongo.db.websites.find_one({'_id': ObjectId(id)})
        if not site:
            return jsonify({'msg': 'Website not found'}), 404

        if user_role == 'Editor' and site.get('owner') != user_id:
            return jsonify({'msg': 'Permission denied'}), 403

        update_fields = {}
        if 'content' in data and isinstance(data['content'], dict):
            for key, value in data['content'].items():
                update_fields[f"content.{key}"] = value
        else:
            for key, value in data.items():
                if key != '_id':
                    update_fields[key] = value

        if not update_fields:
            return jsonify({'msg': 'No valid fields to update'}), 400

        update_fields['last_updated'] = datetime.utcnow()

        mongo.db.websites.update_one(
            {'_id': ObjectId(id)},
            {'$set': update_fields}
        )
        return jsonify({'msg': 'Website updated successfully'}), 200

    except Exception as e:
        print(f"ERROR in update_website: {e}")
        return jsonify({'msg': 'Internal Server Error updating website', 'error_details': str(e)}), 500

@website_bp.route('/<id>', methods=['DELETE'])
@jwt_required()
@permission_required('delete_site')
def delete_website(id):
    current_user_identity = get_jwt_identity()
    user_id = current_user_identity['id']
    user_role = current_user_identity['role']

    try:
        site = mongo.db.websites.find_one({'_id': ObjectId(id)})
        if not site:
            return jsonify({'msg': 'Website not found'}), 404

        if user_role == 'Editor' and site.get('owner') != user_id:
            return jsonify({'msg': 'Permission denied'}), 403

        result = mongo.db.websites.delete_one({'_id': ObjectId(id)})

        if result.deleted_count == 1:
            return jsonify({'msg': 'Website deleted successfully'}), 200
        else:
            return jsonify({'msg': 'Website not found or already deleted'}), 404

    except Exception as e:
        print(f"ERROR in delete_website: {e}")
        return jsonify({'msg': 'Internal Server Error deleting website', 'error_details': str(e)}), 500
