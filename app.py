import os
import json
from flask import Flask, request, jsonify, render_template_string
import cloudinary
import cloudinary.uploader

app = Flask(__name__)

# ------------------------
# Cloudinary configuration
# ------------------------
cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_URL").split("@")[1],
    api_key=os.environ.get("CLOUDINARY_URL").split(":")[1].replace("//", ""),
    api_secret=os.environ.get("CLOUDINARY_URL").split(":")[2].split("@")[0],
    secure=True
)

# ------------------------
# JSON file to store products
# ------------------------
PRODUCTS_FILE = "products.json"

# Initialize products file if it doesn't exist
if not os.path.exists(PRODUCTS_FILE):
    with open(PRODUCTS_FILE, "w") as f:
        json.dump([], f)

def load_products():
    with open(PRODUCTS_FILE, "r") as f:
        return json.load(f)

def save_products(products):
    with open(PRODUCTS_FILE, "w") as f:
        json.dump(products, f, indent=2)

# ------------------------
# User page
# ------------------------
USER_HTML = """[same as previous USER_HTML, unchanged]"""
ADMIN_HTML = """[same as previous ADMIN_HTML, unchanged]"""

# ------------------------
# Routes
# ------------------------
@app.route('/')
def user_page():
    return render_template_string(USER_HTML)

@app.route('/admin')
def admin_page():
    return render_template_string(ADMIN_HTML)

@app.route('/api/products', methods=['GET'])
def get_products():
    return jsonify(load_products())

@app.route('/api/products', methods=['POST'])
def add_product():
    name = request.form['name']
    price = float(request.form['price'])
    description = request.form.get('description', '')

    file = request.files['image']
    upload_result = cloudinary.uploader.upload(file)
    image_url = upload_result['secure_url']

    product = {"name": name, "price": price, "description": description, "image_url": image_url}
    
    products = load_products()
    products.append(product)
    save_products(products)

    return jsonify({"message": "Product added successfully!"})

# ------------------------
# Run
# ------------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
