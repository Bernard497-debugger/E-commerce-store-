from flask import Flask, request, redirect, jsonify, send_from_directory, render_template_string
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

# Inline HTML templates
INDEX_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Khali Store</title>
<style>
body {margin:0;font-family:Arial,sans-serif;background:#f4f4f4;color:#333;}
header {background:#111;color:#fff;padding:1rem;text-align:center;font-family:'Brush Script MT',cursive;font-size:2.5rem;}
#cart-toggle{position:fixed;top:1rem;right:1rem;background:#ff4757;color:#fff;border:none;padding:0.5rem 1rem;cursor:pointer;border-radius:8px;z-index:1001;}
#cart{position:fixed;top:0;right:0;width:300px;height:100%;background:#fff;box-shadow:-2px 0 5px rgba(0,0,0,0.2);padding:1rem;display:none;flex-direction:column;z-index:1000;}
#cart h2{margin-top:0;}
.products{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:1rem;padding:2rem;}
.product{background:#fff;padding:1rem;border-radius:8px;box-shadow:0 2px 5px rgba(0,0,0,0.1);text-align:center;transition:transform 0.2s;}
.product:hover{transform:translateY(-5px);}
.product img{max-width:100%;height:200px;object-fit:contain;border-radius:6px;}
footer{background:#111;color:#fff;text-align:center;padding:1rem;margin-top:2rem;}
button{background:#111;color:#fff;border:none;padding:0.5rem 1rem;cursor:pointer;border-radius:6px;}
button:hover{background:#ff4757;}
</style>
</head>
<body>
<header>Khali Store</header>
<button id="cart-toggle">Cart</button>
<div id="cart">
<h2>Your Cart</h2>
<ul id="cart-items"></ul>
<p><strong>Total: $<span id="total">0</span></strong></p>
<button onclick="checkout()">Checkout</button>
</div>
<main>
<div id="product-grid" class="products"></div>
</main>
<footer>
<p>&copy; 2025 Khali Store | All Rights Reserved</p>
</footer>
<script>
let cart=[];
document.getElementById('cart-toggle').addEventListener('click',()=>{const cartEl=document.getElementById('cart');cartEl.style.display=cartEl.style.display==='flex'?'none':'flex';});
function addToCart(name,price){cart.push({name,price});updateCart();}
function updateCart(){const cartItems=document.getElementById('cart-items');const total=document.getElementById('total');cartItems.innerHTML='';let sum=0;cart.forEach(item=>{const li=document.createElement('li');li.textContent=`${item.name} - $${item.price}`;cartItems.appendChild(li);sum+=item.price;});total.textContent=sum.toFixed(2);}
function checkout(){let message="Hello, I’d like to order:\\n";cart.forEach(item=>{message+=`${item.name} - $${item.price}\\n`;});const total=document.getElementById('total').textContent;message+=`\\nTotal: $${total}`;const url=`https://wa.me/267123456789?text=${encodeURIComponent(message)}`;window.open(url,'_blank');}
async function loadProducts(){const res=await fetch('/api/products');const products=await res.json();const productGrid=document.getElementById('product-grid');productGrid.innerHTML='';products.forEach(product=>{const productCard=document.createElement('div');productCard.className='product';productCard.innerHTML=`<img src="${product.image_url}" alt="${product.name}"><h3>${product.name}</h3><p>${product.description}</p><p><strong>$${product.price}</strong></p><button onclick="addToCart('${product.name}',${product.price})">Add to Cart</button>`;productGrid.appendChild(productCard);});}
window.onload=loadProducts;
</script>
</body>
</html>
"""

ADMIN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Khali Store Admin</title>
<style>
body {font-family: Arial,sans-serif;background:#f9f9f9;padding:2rem;}
h1{text-align:center;color:#111;}
form{background:#fff;padding:1rem;border-radius:8px;box-shadow:0 2px 5px rgba(0,0,0,0.1);max-width:400px;margin:0 auto 2rem;}
form input,form textarea,form button{width:100%;margin:0.5rem 0;padding:0.7rem;border:1px solid #ccc;border-radius:6px;font-size:1rem;}
form button{background:#111;color:#fff;cursor:pointer;}
form button:hover{background:#ff4757;}
.product-list{max-width:800px;margin:0 auto;display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:1rem;}
.product{background:#fff;padding:1rem;border-radius:8px;box-shadow:0 2px 5px rgba(0,0,0,0.1);text-align:center;}
.product img{max-width:100%;height:150px;object-fit:contain;border-radius:6px;margin-bottom:0.5rem;}
.product h3{margin:0.5rem 0;}
.product p{margin:0.2rem 0;}
button.delete{background:#ff4757;color:#fff;margin-top:0.5rem;}
button.delete:hover{background:#111;}
</style>
</head>
<body>
<h1>Khali Store Admin</h1>
<form method="POST" enctype="multipart/form-data">
<input type="text" name="name" placeholder="Product Name" required>
<textarea name="description" placeholder="Description" required></textarea>
<input type="number" step="0.01" name="price" placeholder="Price" required>
<input type="file" name="image" accept="image/*" required>
<button type="submit">Add Product</button>
</form>
<h2 style="text-align:center;">All Products</h2>
<div class="product-list">
{% for product in products %}
<div class="product">
<img src="{{ product.image_url }}" alt="{{ product.name }}">
<h3>{{ product.name }}</h3>
<p>{{ product.description }}</p>
<p><strong>$ {{ product.price }}</strong></p>
<form method="POST" action="/delete/{{ product.id }}">
<button type="submit" class="delete">Delete</button>
</form>
</div>
{% endfor %}
</div>
</body>
</html>
"""

# Home page
@app.route('/')
def index():
    return render_template_string(INDEX_HTML)

# API endpoint
@app.route('/api/products')
def get_products():
    products = Product.query.all()
    return jsonify([{"id":p.id,"name":p.name,"description":p.description,"price":p.price,"image_url":p.image_url} for p in products])

# Admin page
@app.route('/admin', methods=['GET','POST'])
def admin():
    if request.method=='POST' and 'image' in request.files:
        name = request.form['name']
        description = request.form['description']
        price = float(request.form['price'])
        image = request.files['image']

        filename = image.filename
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(filepath)

        new_product = Product(name=name, description=description, price=price, image_url=f"/uploads/{filename}")
        db.session.add(new_product)
        db.session.commit()

        return redirect('/admin')

    products = Product.query.all()
    return render_template_string(ADMIN_HTML, products=products)

# Delete product route
@app.route('/delete/<int:id>', methods=['POST'])
def delete_product(id):
    product = Product.query.get(id)
    if product:
        # Remove image file
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], os.path.basename(product.image_url))
        if os.path.exists(image_path):
            os.remove(image_path)
        db.session.delete(product)
        db.session.commit()
    return redirect('/admin')

# Serve uploaded images
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Initialize database
with app.app_context():
    db.create_all()

# Run server
if __name__=='__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
