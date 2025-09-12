from flask import Flask, render_template, request, redirect, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# Database setup
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///products.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Uploads setup
UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db = SQLAlchemy(app)

# Product model
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(300), nullable=False)
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(200), nullable=False)

# Home page
@app.route('/')
def index():
    return render_template('index.html')

# API endpoint to get products
@app.route('/api/products')
def get_products():
    products = Product.query.all()
    return jsonify([
        {
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "price": p.price,
            "image_url": p.image_url
        }
        for p in products
    ])

# Admin page (add + view products)
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = float(request.form['price'])
        image = request.files['image']

        # Save uploaded image
        filename = image.filename
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(filepath)

        # Save product to database
        new_product = Product(
            name=name,
            description=description,
            price=price,
            image_url=f"/uploads/{filename}"
        )
        db.session.add(new_product)
        db.session.commit()

        return redirect('/admin')

    products = Product.query.all()
    return render_template('admin.html', products=products)

# Serve uploaded images
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Initialize database
with app.app_context():
    db.create_all()

# Run server
if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)