from flask import Flask, request, jsonify, Response, send_from_directory
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db = SQLAlchemy(app)

# Product model
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    desc = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Float, nullable=False)
    img = db.Column(db.String(255), nullable=False)

# Initialize database
if not os.path.exists('database.db'):
    with app.app_context():
        db.create_all()

# Serve uploaded images
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ===== Store front-end =====
@app.route('/')
def store():
    return Response(STORE_HTML, mimetype='text/html')

# ===== Admin panel =====
@app.route('/admin')
def admin():
    return Response(ADMIN_HTML, mimetype='text/html')

# ===== APIs =====
@app.route('/api/products', methods=['GET'])
def get_products():
    products = Product.query.all()
    return jsonify([{'id': p.id, 'name': p.name, 'desc': p.desc, 'price': p.price, 'img': p.img} for p in products])

@app.route('/api/products', methods=['POST'])
def add_product():
    data = request.json
    new_product = Product(name=data['name'], desc=data['desc'], price=float(data['price']), img=data['img'])
    db.session.add(new_product)
    db.session.commit()
    return jsonify({'message': 'Product added'})

@app.route('/api/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    return jsonify({'message': 'Product deleted'})

@app.route('/api/upload', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    filename = file.filename
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    return jsonify({'url': f'/uploads/{filename}'})

# ===== Store HTML =====
STORE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Khali Store</title>
<link href="https://fonts.googleapis.com/css2?family=Fredericka+the+Great&display=swap" rel="stylesheet">
<style>
body{font-family:Arial;margin:0;background:#FDF6EC;color:#0D1B2A;}
header {padding:40px 20px;text-align:center;background:#0D1B2A;color:#FFD700;font-family: 'Fredericka the Great', cursive;font-size:3rem;letter-spacing:2px;}
.products{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:20px;margin:20px;}
.product{background:#fff;padding:15px;border-radius:15px;box-shadow:0 4px 15px rgba(0,0,0,0.2);}
.product img{width:100%;height:auto;max-height:250px;object-fit:contain;border-radius:10px;background:#f0f0f0;}
button{background:#FFD700;border:none;padding:10px;border-radius:10px;cursor:pointer;}
button:hover{background:#e6c200;}
#cart{position:fixed;right:20px;top:70px;background:#fff;padding:15px;width:250px;border-radius:15px;display:none;box-shadow:0 5px 20px rgba(0,0,0,0.3);}
#cart h3{margin:0;font-size:1.2rem;}
#cart button#toggleCart{float:right;background:#0D1B2A;color:#FFD700;border:none;border-radius:50%;width:25px;height:25px;cursor:pointer;font-weight:bold;}
footer {background: #0D1B2A;color: #FFD700;text-align: center;padding: 20px;font-size: 0.9rem;position: relative;bottom: 0;width: 100%;}
footer a {color: #FFD700; text-decoration: none;}
footer a:hover {text-decoration: underline;}
</style>
</head>
<body>
<header>Khali Store</header>

<div id="cart">
  <h3>Cart <button id="toggleCart">-</button></h3>
  <div id="cartItems"></div>
  <p id="total"></p>
  <button onclick="checkout()">Checkout</button>
</div>

<main>
<div class="products" id="products"></div>
</main>

<footer>
  <p>© 2025 Khali Store. All rights reserved.</p>
  <p>Contact us: <a href="https://wa.me/26771234567" target="_blank">WhatsApp</a></p>
</footer>

<script>
let cart=[];
const whatsappNumber="26771234567";

async function loadProducts(){
    const res = await fetch('/api/products'); const data = await res.json();
    const container = document.getElementById('products'); container.innerHTML='';
    data.forEach(p=>{
        const div=document.createElement('div'); div.className='product';
        div.innerHTML=`<img src="${p.img}" alt="${p.name}"><h3>${p.name}</h3><p>${p.desc}</p><p>$${p.price.toFixed(2)}</p>
                       <button onclick='addToCart(${JSON.stringify(p)})'>Add to Cart</button>`;
        container.appendChild(div);
    });
}

function addToCart(p){const item=cart.find(i=>i.id===p.id);if(item){item.qty+=1;}else{cart.push({...p,qty:1});} renderCart();}
function renderCart(){const cartDiv=document.getElementById('cartItems');cartDiv.innerHTML='';let total=0;cart.forEach(i=>{total+=i.price*i.qty; cartDiv.innerHTML+=`<p>${i.name} x${i.qty} <button onclick="removeFromCart(${i.id})">Remove</button></p>`}); document.getElementById('total').innerText='Total: $'+total.toFixed(2); document.getElementById('cart').style.display='block';}
function removeFromCart(id){cart=cart.filter(i=>i.id!==id); renderCart();}
function checkout(){if(cart.length===0){alert('Cart empty');return;} let msg="Hello, I want to order:%0A"; let total=0; cart.forEach(i=>{total+=i.price*i.qty; msg+=`${i.name} x${i.qty} = $${(i.price*i.qty).toFixed(2)}%0A`}); msg+=`Total: $${total.toFixed(2)}`; window.open(`https://wa.me/${whatsappNumber}?text=${msg}`,'_blank');}

const toggleButton = document.getElementById('toggleCart');
let cartMinimized = false;
toggleButton.addEventListener('click', () => {
    cartMinimized = !cartMinimized;
    const itemsDiv = document.getElementById('cartItems');
    const totalP = document.getElementById('total');
    const checkoutBtn = itemsDiv.nextElementSibling;
    if(cartMinimized){itemsDiv.style.display='none'; totalP.style.display='none'; checkoutBtn.style.display='none'; toggleButton.innerText='+';}
    else{itemsDiv.style.display='block'; totalP.style.display='block'; checkoutBtn.style.display='block'; toggleButton.innerText='-';}
});

loadProducts();
</script>
</body>
</html>
"""

# ===== Admin HTML =====
ADMIN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Khali Store Admin</title>
<style>
body{font-family:Arial;margin:0;padding:0;background:#FDF6EC;}
header{background:#0D1B2A;color:#FFD700;padding:20px;text-align:center;font-size:2rem;}
.container{padding:20px;}
input, button{padding:10px;margin:5px;border-radius:5px;border:1px solid #ccc;}
button{background:#FFD700;border:none;cursor:pointer;}
button:hover{background:#e6c200;}
.products{margin-top:20px;display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:15px;}
.product{border:1px solid #ccc;padding:10px;border-radius:10px;background:#fff;text-align:center;}
.product img{width:100%;height:auto;max-height.product img{width:100%;height:auto;max-height:150px;object-fit:contain;border-radius:10px;background:#f0f0f0;}
</style>
</head>
<body>
<header>Khali Store Admin</header>
<div class="container">
<h2>Add Product</h2>
<input type="text" id="name" placeholder="Product Name">
<input type="text" id="desc" placeholder="Description">
<input type="number" id="price" placeholder="Price">
<input type="file" id="image">
<button onclick="addProduct()">Add</button>

<div class="products" id="productsList"></div>
</div>

<script>
async function loadProducts(){
    const res = await fetch('/api/products');
    const data = await res.json();
    const container = document.getElementById('productsList');
    container.innerHTML='';
    data.forEach(p=>{
        const div=document.createElement('div'); div.className='product';
        div.innerHTML=`<img src="${p.img}" alt="${p.name}"><br>
                       <b>${p.name}</b><br>${p.desc}<br>Price: $${p.price.toFixed(2)}
                       <br><button onclick='deleteProduct(${p.id})'>Delete</button>`;
        container.appendChild(div);
    });
}

async function addProduct(){
    const name=document.getElementById('name').value;
    const desc=document.getElementById('desc').value;
    const price=document.getElementById('price').value;
    const imageFile=document.getElementById('image').files[0];
    if(!name || !desc || !price || !imageFile){alert('All fields required'); return;}
    const formData = new FormData();
    formData.append('file', imageFile);
    const uploadRes = await fetch('/api/upload', {method:'POST', body:formData});
    const uploadData = await uploadRes.json();
    const imgUrl = uploadData.url;
    await fetch('/api/products', {method:'POST', headers:{'Content-Type':'application/json'},
        body: JSON.stringify({name, desc, price, img: imgUrl})});
    loadProducts();
}

async function deleteProduct(id){
    await fetch('/api/products/'+id, {method:'DELETE'});
    loadProducts();
}

loadProducts();
</script>
</body>
</html>
"""

# ===== Production-ready app run =====
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)