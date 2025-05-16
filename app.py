from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import json
import re
import os
from pathlib import Path
from dotenv import load_dotenv


from flask_mail import Mail, Message
# Load environment variables
load_dotenv()

# Initialize Flask application
app = Flask(__name__)

# Check for Gemini API key
api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    print("Warning: GEMINI_API_KEY not found in environment variables.")
    print("Setting a placeholder API key for development. This will not work for actual API calls.")
    # Setting a placeholder API key to allow the application to start
    # This won't work for actual API calls but prevents immediate exit
    api_key = "AIzaSyDwS-kM0t0LwrOtkKwnCVgX5t6P6ptgsuc"

# Import Google GenerativeAI after checking API key
try:
    import google.generativeai as genai
    from PIL import Image
    from io import BytesIO
    
    # Configure Gemini API
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    vision_model = genai.GenerativeModel('gemini-1.5-flash')
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Please install the required packages with: pip install google-generativeai pillow")
except Exception as e:
    print(f"Error initializing Gemini API: {e}")
    # Continue execution - the routes using these will handle the errors

def clean_json_response(response_text):
    """Clean JSON response from Gemini API"""
    # Remove triple backticks if present (common in code block responses)
    text = re.sub(r'^```json\s*', '', response_text, flags=re.MULTILINE)
    text = re.sub(r'^```\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'```$', '', text, flags=re.MULTILINE)
    
    # Remove any leading/trailing whitespace
    cleaned_text = text.strip()
    return cleaned_text


@app.route('/')
def food():
    return render_template('food.html')

@app.route('/morerecipe.html')
def more_recipes():
    return render_template('morerecipe.html')

@app.route('/about.html')
def about():
    return render_template('about.html')

@app.route('/altrecp')
def altrecp():
    return render_template('altrecp.html')

@app.route('/recipe.html')
def recipe():
    return render_template('recipe.html')

@app.route('/avoidfoods')
def avoidfoods():
    return render_template('avoidfoods.html')

@app.route('/nutrical.html')
def nutrical():
    return render_template('nutrical.html')

@app.route('/AI')
def AI():
    return render_template('AI.html')

@app.route('/foodswap')
def foodswap():
    return render_template('foodswap.html')

@app.route('/get_nutrition_info', methods=['POST'])
def get_nutrition_info():
    """Get detailed nutrition information for a food item"""
    try:
        if api_key == "PLACEHOLDER_API_KEY":
            return jsonify({"success": False, "error": "Gemini API key not configured. Please set GEMINI_API_KEY environment variable."})
        
        # Get food name from request
        data = request.get_json()
        food_name = data.get('food_name', '')
        
        if not food_name:
            return jsonify({'success': False, 'error': 'No food name provided'})
        
        # Prepare prompt for Gemini API
        prompt = f"""
        Provide detailed nutritional information for {food_name}.
        
        Return the response as a JSON object with exactly this structure:
        {{
            "name": "{food_name}",
            "serving_size": "1 medium (e.g.)",
            "serving_weight": 100,
            "calories": 100,
            "protein": 2,
            "carbohydrates": 25,
            "fat": 0.5,
            "fiber": 4,
            "sugar": 20,
            "sodium": 2,
            "potassium": 200,
            "image_url": "placeholder-food.jpg",
            "benefits": [
                "Benefit 1",
                "Benefit 2",
                "Benefit 3"
            ],
            "when_to_consume": "Morning, afternoon, etc.",
            "how_to_consume": "Raw, cooked, etc.",
            "daily_recommendation": "1-2 servings per day"
        }}
        
        All nutritional values should be numbers, not strings. Include at least 3 specific health benefits.
        Return ONLY the JSON object with no additional text or formatting.
        """
        
        # Generate response from Gemini
        response = model.generate_content(prompt)
        cleaned_text = clean_json_response(response.text)
        
        try:
            nutrition_info = json.loads(cleaned_text)
            
            # Basic validation of required fields
            required_fields = [
                "name", "serving_size", "serving_weight", "calories", "protein",
                "carbohydrates", "fat", "fiber", "sugar", "sodium", "potassium",
                "benefits", "when_to_consume", "how_to_consume", "daily_recommendation"
            ]
            
            for field in required_fields:
                if field not in nutrition_info:
                    return jsonify({"success": False, "error": f"Missing required field: {field}"})
            
            # Convert numerical values to numbers if they're strings
            numeric_fields = ["serving_weight", "calories", "protein", "carbohydrates", 
                            "fat", "fiber", "sugar", "sodium", "potassium"]
            
            for field in numeric_fields:
                try:
                    nutrition_info[field] = float(str(nutrition_info[field]).strip())
                except (ValueError, TypeError):
                    nutrition_info[field] = 0
            
            return jsonify({"success": True, "nutrition_info": nutrition_info})
            
        except json.JSONDecodeError as e:
            return jsonify({"success": False, "error": f"Failed to parse nutrition data: {str(e)}"})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)})
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/generate_recipe', methods=['POST'])
def generate_recipe():
    """Generate recipes based on user ingredients"""
    try:
        if api_key == "PLACEHOLDER_API_KEY":
            return jsonify({"success": False, "error": "Gemini API key not configured. Please set GEMINI_API_KEY environment variable."})
        
        food_name = request.json.get('food', '')
        if not food_name:
            return jsonify({"success": False, "error": "No food name provided"})

        prompt = f"""
Generate 3 recipes using the food item: {food_name}.
The response should be a JSON array in the following format:

[
    {{
        "name": "Recipe Name Here",
        "additionalIngredients": ["ingredient1", "ingredient2"],
        "instructions": ["step1", "step2"]
    }},
    {{
        "name": "Second Recipe Name",
        "additionalIngredients": ["ingredient1", "ingredient2"],
        "instructions": ["step1", "step2"]
    }},
    {{
        "name": "Third Recipe Name",
        "additionalIngredients": ["ingredient1", "ingredient2"],
        "instructions": ["step1", "step2"]
    }}
]

Return ONLY the JSON array with no additional text or formatting.
"""

        response = model.generate_content(prompt)
        cleaned_text = clean_json_response(response.text)

        try:
            recipes = json.loads(cleaned_text)
            return jsonify({"success": True, "recipes": recipes})
        except json.JSONDecodeError as e:
            return jsonify({"success": False, "error": "Failed to parse recipe data", "error_type": "JSONDecodeError"})
        except Exception as e:
            return jsonify({"success": False, "error": str(e), "error_type": type(e).__name__})
    except Exception as e:  # Catch any unexpected errors
        return jsonify({"success": False, "error": str(e), "error_type": type(e).__name__})

@app.route('/find_alternatives', methods=['POST'])
def find_food_alternatives():
    """Find healthy alternatives for a given food item"""
    try:
        if api_key == "PLACEHOLDER_API_KEY":
            return jsonify({"success": False, "error": "Gemini API key not configured. Please set GEMINI_API_KEY environment variable."})
        
        food_item = request.json.get('food_item', '')
        if not food_item:
            return jsonify({"success": False, "error": "No food item provided"})

        prompt = f"""
Generate 2 healthy alternative food items for {food_item} with accurate nutritional information.
Provide the response as a JSON array with exactly this structure, ensuring all values are numbers:

[
    {{
        "name": "Alternative Food 1",
        "nutritionalInfo": {{
            "calories": 100,
            "protein": 10,
            "carbs": 20,
            "fats": 5,
            "energy": 200
        }},
        "description": "A detailed description of why this is a healthy alternative to {food_item}, including key health benefits."
    }},
    {{
        "name": "Alternative Food 2",
        "nutritionalInfo": {{
            "calories": 120,
            "protein": 8,
            "carbs": 15,
            "fats": 6,
            "energy": 250
        }},
        "description": "A detailed description of why this is a healthy alternative to {food_item}, including key health benefits."
    }}
]

Return ONLY the JSON array with no additional text or formatting.
"""

        response = model.generate_content(prompt)
        cleaned_text = clean_json_response(response.text)

        try:
            alternatives = json.loads(cleaned_text)
            # Validate response structure
            if not isinstance(alternatives, list) or len(alternatives) != 2:
                raise ValueError("Invalid response format - expected array of 2 alternatives")

            # Convert nutritional values to numbers and validate structure
            for alt in alternatives:
                if not all(key in alt for key in ["name", "nutritionalInfo", "description"]):
                    raise ValueError("Missing required fields in alternative")
                for key, value in alt["nutritionalInfo"].items():
                    try:
                        alt["nutritionalInfo"][key] = float(str(value).strip())
                    except (ValueError, TypeError):
                        alt["nutritionalInfo"][key] = 0

            return jsonify({"success": True, "alternatives": alternatives})
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error processing alternatives: {e}")
            return jsonify({
                "success": False,
                "error": f"Failed to process response: {str(e)}",
                "error_type": type(e).__name__
            })
        except Exception as e:
            print(f"Unexpected error in find_alternatives: {str(e)}")
            return jsonify({
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            })
    except Exception as e:  # Catch any unexpected errors
        return jsonify({"success": False, "error": str(e), "error_type": type(e).__name__})

# ---  Updated Health Recommendations Route (Search Bar) ---
@app.route('/get_health_recommendations', methods=['POST'])
def get_health_recommendations():
    try:
        if api_key == "PLACEHOLDER_API_KEY":
            return jsonify({"success": False, "error": "Gemini API key not configured. Please set GEMINI_API_KEY environment variable."})
        
        # Get health conditions from request
        data = request.get_json()
        health_conditions = data.get('health_conditions', '')
        
        if not health_conditions:
            return jsonify({'success': False, 'error': 'No health conditions provided'})
        
        # Prepare prompt for Gemini API
        prompt = f"""
        Provide detailed dietary recommendations for someone with the following health condition: {health_conditions}
        
        Please format your response in JSON with the following structure:
        {{
            "{health_conditions}": {{
                "foods_to_avoid": [list of specific foods to avoid],
                "recommended_foods": [list of specific foods that are beneficial],
                "description": "Detailed description of the dietary approach for this condition"
            }}
        }}
        
        Include at least 10 specific foods in each list (foods_to_avoid and recommended_foods).
        The description should be comprehensive and explain why certain foods are recommended or should be avoided.
        """
        
        # Generate response from Gemini
        response = model.generate_content(prompt)
        
        # Extract the JSON from the response
        try:
            # First try to parse the entire response as JSON
            recommendations = json.loads(response.text)
        except json.JSONDecodeError:
            # If that fails, try to extract JSON from the text
            try:
                # Look for JSON-like structure in the response
                json_start = response.text.find('{')
                json_end = response.text.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = response.text[json_start:json_end]
                    recommendations = json.loads(json_str)
                else:
                    raise Exception("Could not find valid JSON in response")
            except Exception as e:
                return jsonify({'success': False, 'error': f'Failed to parse response: {str(e)}'})
        
        return jsonify({'success': True, 'recommendations': recommendations})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    
@app.route('/identify_food', methods=['POST'])
def identify_food():
    try:
        if api_key == "PLACEHOLDER_API_KEY":
            return jsonify({"success": False, "error": "Gemini API key not configured. Please set GEMINI_API_KEY environment variable."})
        
        if 'food_image' not in request.files:
            return jsonify({'success': False, 'error': 'No image file provided'})
        
        file = request.files['food_image']
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No image selected'})
        
        # Read and process the image
        image_data = file.read()
        image = Image.open(BytesIO(image_data))
        
        # Prepare prompt for vision model
        prompt = "Identify the food item in this image. Give just the name of the food, nothing else."
        
        # Generate response from Gemini vision model
        response = vision_model.generate_content([prompt, image])
        
        # Extract the food name from the response
        food_name = response.text.strip()
        
        if food_name:
            return jsonify({'success': True, 'food_name': food_name})
        else:
            return jsonify({'success': False, 'error': 'Could not identify food in the image'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# --- App execution ---
if __name__ == '__main__':
    # Create necessary directories if they don't exist
    Path("static/css").mkdir(parents=True, exist_ok=True)
    Path("static/js").mkdir(parents=True, exist_ok=True)
    Path("templates").mkdir(parents=True, exist_ok=True)
    
    # Start the Flask app
    app.run(debug=True)