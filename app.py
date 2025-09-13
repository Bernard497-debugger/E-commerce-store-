import os
from flask import Flask, request, jsonify, render_template_string
from flask_sqlalchemy import SQLAlchemy
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Database setup
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Cloudinary setup
cloudinary.config(
    cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME'),
    api_key=os.environ.get('CLOUDINARY_API_KEY'),
    api_secret=os.environ.get('CLOUDINARY_API_SECRET')
)

# Database model
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(300), nullable=False)

db.create_all()

# ----- FRONTEND HTML -----
frontend_html = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Khali Commerce</title>
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
form {margin-bottom:2rem;}
input, label {display:block; margin:0.5rem 0; padding:0.5rem; border-radius:6px; border:none;}
input[type="file"] {padding:0;}
</style>
</head>
<body>
<header>
  <h1>Khali Commerce</h1>
</header>

<main>
  <!-- Upload Form -->
  <form id="upload-form">
    <h2>Admin Upload</h2>
    <input type="text" id="name" placeholder="Product Name" required>
    <input type="number" id="price" placeholder="Price" step="0.01" required>
    <input type="file" id="file" accept="image/*" required>
    <button type="submit">Upload Product</button>
  </form>

  <!-- Products -->
  <div id="products"></div>
</main>

<div id="cart">
  <h3>Cart</h3>
  <ul id="cart-items"></ul>
  <p>Total: $<span id="total">0.00</span></p>
</div>

<script>
const productsContainer = document.getElementById('products');
const cartItemsList = document.getElementById('cart-items');
const totalElem = document.getElementById('total');
const uploadForm = document.getElementById('upload-form');
let cart = [];

// Fetch products
function loadProducts(){
  fetch('/products')
  .then(res => res.json())
  .then(products => {
    productsContainer.innerHTML = '';
    products.forEach(p=>{
      const card = document.createElement('div');
      card.className = 'product-card';
      card.innerHTML = `
        <img src="${p.image_url}" alt="${p.name}">
        <div class="product-info">
          <h2>${p.name}</h2>
          <p>$${p.price.toFixed(2)}</p>
          <button onclick="addToCart(${p.id}, '${p.name}', ${p.price})">Add to Cart</button>
        </div>
      `;
      productsContainer.appendChild(card);
    });
  });
}
loadProducts();

// Add to cart
function addToCart(id,name,price){
  const existing = cart.find(item=>item.id===id);
  if(existing) existing.qty +=1;
  else cart.push({id,name,price,qty:1});
  renderCart();
}

function renderCart(){
  cartItemsList.innerHTML='';
  let total=0;
  cart.forEach(item=>{
    total += item.price * item.qty;
    const li = document.createElement('li');
    li.textContent = `${item.name} x${item.qty} - $${(item.price*item.qty).toFixed(2)}`;
    cartItemsList.appendChild(li);
  });
  totalElem.textContent=total.toFixed(2);
}

// Handle product upload
uploadForm.addEventListener('submit', e=>{
  e.preventDefault();
  const file = document.getElementById('file').files[0];
  const name = document.getElementById('name').value;
  const price = document.getElementById('price').value;

  const formData = new FormData();
  formData.append('file', file);
  formData.append('name', name);
  formData.append('price', price);

  fetch('/upload',{
    method:'POST',
    body: formData
  })
  .then(res=>res.json())
  .then(data=>{
    alert(data.message);
    uploadForm.reset();
    loadProducts();
  });
});
</script>

</body>
</html>
"""

# ----- ROUTES -----
@app.route('/')
def home():
    return render_template_string(frontend_html)

@app.route('/products', methods=['GET'])
def get_products():
    products = Product.query.all()
    return jsonify([{'id':p.id,'name':p.name,'price':p.price,'image_url':p.image_url} for p in products])

@app.route('/upload', methods=['POST'])
def upload_product():
    if 'file' not in request.files:
        return jsonify({'error':'No file part'}),400
    file = request.files['file']
    name = request.form.get('name')
    price = request.form.get('price')
    if not file or not name or not price:
        return jsonify({'error':'Missing file, name, or price'}),400

    # Upload to Cloudinary
    result = cloudinary.uploader.upload(file)

    # Save to DB
    product = Product(name=name, price=float(price), image_url=result['secure_url'])
    db.session.add(product)
    db.session.commit()
    return jsonify({'message':'Product uploaded successfully!'})

# ----- RUN -----
if __name__ == '__main__':
    app.run(debug=True)