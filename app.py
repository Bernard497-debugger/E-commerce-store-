import os
from flask import Flask, request, redirect, jsonify, render_template_string
from flask_sqlalchemy import SQLAlchemy
import cloudinary
import cloudinary.uploader
from werkzeug.utils import secure_filename

app = Flask(__name__)

# ==========================
# 1️⃣ Database Configuration (PostgreSQL via env vars)
# ==========================
DB_USERNAME = os.environ.get("DB_USERNAME")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_HOST     = os.environ.get("DB_HOST")
DB_PORT     = os.environ.get("DB_PORT")
DB_NAME     = os.environ.get("DB_NAME")

app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ==========================
# 2️⃣ Cloudinary Configuration via env var
# ==========================
cloudinary.config(cloudinary_url=os.environ.get("CLOUDINARY_URL"))

# ==========================
# 3️⃣ Database Model
# ==========================
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(300), nullable=False)
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(500), nullable=False)

# ==========================
# 4️⃣ HTML Templates (Inline)
# ==========================
# Paste your previous INDEX_HTML and ADMIN_HTML here
INDEX_HTML = """[PASTE YOUR INDEX_HTML HERE]"""
ADMIN_HTML = """[PASTE YOUR ADMIN_HTML HERE]"""

# ==========================
# 5️⃣ Routes
# ==========================
@app.route('/')
def index():
    return render_template_string(INDEX_HTML)

@app.route('/api/products')
def get_products():
    products = Product.query.all()
    return jsonify([{
        "id": p.id,
        "name": p.name,
        "description": p.description,
        "price": p.price,
        "image_url": p.image_url
    } for p in products])

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST' and 'image' in request.files:
        name = request.form['name']
        description = request.form['description']
        price = float(request.form['price'])
        image = request.files['image']

        # Upload to Cloudinary
        upload_result = cloudinary.uploader.upload(image)
        image_url = upload_result['secure_url']

        # Save product in DB
        new_product = Product(
            name=name,
            description=description,
            price=price,
            image_url=image_url
        )
        db.session.add(new_product)
        db.session.commit()
        return redirect('/admin')

    products = Product.query.all()
    return render_template_string(ADMIN_HTML, products=products)

@app.route('/delete/<int:id>', methods=['POST'])
def delete_product(id):
    product = Product.query.get(id)
    if product:
        # Optionally delete image from Cloudinary
        try:
            public_id = product.image_url.split('/')[-1].split('.')[0]
            cloudinary.uploader.destroy(public_id)
        except Exception as e:
            print(f"Cloudinary delete error: {e}")
        db.session.delete(product)
        db.session.commit()
    return redirect('/admin')

# ==========================
# 6️⃣ Initialize DB
# ==========================
with app.app_context():
    db.create_all()

# ==========================
# 7️⃣ Run App
# ==========================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)