import os
from flask import Flask, request, jsonify, render_template_string, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import cloudinary
import cloudinary.uploader

# ------------------------------
# Flask + Database setup
# ------------------------------
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL").replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ------------------------------
# Cloudinary setup
# ------------------------------
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

# ------------------------------
# Product Model
# ------------------------------
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(255))
    image_url = db.Column(db.String(255))

db.create_all()

# ------------------------------
# Routes
# ------------------------------

# User Page (Shop)
@app.route("/")
def user_page():
    products = Product.query.all()
    html = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Khali Store</title>
<style>
:root {
  --dark-bg: #121212;
  --dark-card: #1e1e1e;
  --lime: #A7FF83;
  --text-light: #fff;
}
body { margin:0; font-family:'Segoe UI',sans-serif; background:var(--dark-bg); color:var(--text-light);}
header {padding:1rem 2rem; background:var(--dark-card); display:flex; justify-content:space-between; align-items:center; box-shadow:0 2px 6px rgba(0,0,0,0.5);}
header h1 {margin:0; color:var(--lime);}
main {padding:2rem; display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:1.5rem;}
.product-card {background:var(--dark-card); border-radius:12px; overflow:hidden; box-shadow:0 4px 10px rgba(0,0,0,0.4); display:flex; flex-direction:column; transition: transform 0.3s;}
.product-card:hover {transform: translateY(-5px);}
.product-card img {width:100%; height:180px; object-fit:cover;}
.product-info {padding:1rem; flex-grow:1; display:flex; flex-direction:column; justify-content:space-between;}
.product-info h2 {margin:0 0 0.5rem 0; font-size:1.1rem;}
.product-info p {margin:0 0 1rem 0; font-weight:bold; color:var(--lime);}
button {padding:0.5rem; background:var(--lime); border:none; border-radius:6px; cursor:pointer; font-weight:bold; transition: background 0.3s;}
button:hover {background:#8fe068;}
#cart {position:fixed; top:1rem; right:1rem; background:var(--dark-card); border:2px solid var(--lime); padding:1rem; border-radius:12px; max-width:300px; max-height:80vh; overflow-y:auto;}
#cart h3 {margin-top:0; color:var(--lime);}
#cart-items li {margin-bottom:0.5rem;}
</style>
</head>
<body>
<header>
  <h1>Khali Store</h1>
</header>

<main id="products">
{% for p in products %}
<div class="product-card">
  <img src="{{p.image_url}}" alt="{{p.name}}">
  <div class="product-info">
    <h2>{{p.name}}</h2>
    <p>${{p.price}}</p>
    <p>{{p.description}}</p>
    <button onclick="addToCart({{p.id}}, '{{p.name}}', {{p.price}})">Add to Cart</button>
  </div>
</div>
{% endfor %}
</main>

<div id="cart">
  <h3>Cart</h3>
  <ul id="cart-items"></ul>
  <p>Total: $<span id="total">0.00</span></p>
</div>

<script>
let cart = JSON.parse(localStorage.getItem('cart')) || [];

function addToCart(id, name, price) {
  const existing = cart.find(item => item.id === id);
  if(existing) existing.qty += 1;
  else cart.push({id, name, price, qty:1});
  localStorage.setItem('cart', JSON.stringify(cart));
  renderCart();
}

function renderCart() {
  const cartItemsList = document.getElementById('cart-items');
  const totalElem = document.getElementById('total');
  cartItemsList.innerHTML = '';
  let total = 0;
  cart.forEach(item => {
    total += item.price * item.qty;
    const li = document.createElement('li');
    li.textContent = `${item.name} x${item.qty} - $${(item.price*item.qty).toFixed(2)}`;
    cartItemsList.appendChild(li);
  });
  totalElem.textContent = total.toFixed(2);
}

renderCart();
</script>

</body>
</html>
"""
    return render_template_string(html, products=products)

# Admin Panel
@app.route("/admin", methods=["GET", "POST"])
def admin_panel():
    if request.method == "POST":
        name = request.form.get("name")
        price = float(request.form.get("price", 0))
        description = request.form.get("description")
        file = request.files["image"]
        result = cloudinary.uploader.upload(file)
        image_url = result["secure_url"]

        product = Product(name=name, price=price, description=description, image_url=image_url)
        db.session.add(product)
        db.session.commit()
        return redirect(url_for("admin_panel"))

    products = Product.query.all()
    html = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Admin - Khali Store</title>
<style>
body { font-family:'Segoe UI',sans-serif; background:#121212; color:#fff; margin:0; padding:1rem;}
h1,h2 { color:#A7FF83;}
form {background:#1e1e1e; padding:1rem; border-radius:12px; margin-bottom:2rem;}
input, button {padding:0.5rem; margin:0.5rem 0; border-radius:6px; border:none;}
button {background:#A7FF83; color:#000; font-weight:bold; cursor:pointer;}
button:hover {background:#8fe068;}
.product-list div {background:#1e1e1e; padding:0.5rem; margin-bottom:0.5rem; border-radius:8px;}
.product-list img {vertical-align:middle;}
</style>
</head>
<body>
<h1>Admin Panel</h1>
<form method="post" enctype="multipart/form-data">
  <input type="text" name="name" placeholder="Name" required><br>
  <input type="number" step="0.01" name="price" placeholder="Price" required><br>
  <input type="text" name="description" placeholder="Description"><br>
  <input type="file" name="image" accept="image/*" required><br>
  <button type="submit">Add Product</button>
</form>

<h2>Existing Products</h2>
<div class="product-list">
{% for p in products %}
<div>
<img src="{{p.image_url}}" width="80">
<strong>{{p.name}}</strong> - ${{p.price}}
</div>
{% endfor %}
</div>
</body>
</html>
"""
    return render_template_string(html, products=products)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000)