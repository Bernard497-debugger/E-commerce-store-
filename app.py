import os
from functools import wraps
from flask import Flask, request, jsonify, render_template_string
import cloudinary
import cloudinary.uploader

app = Flask(__name__)

# ------------------------
# Cloudinary config
# ------------------------
cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_NAME"),
    api_key=os.environ.get("CLOUDINARY_KEY"),
    api_secret=os.environ.get("CLOUDINARY_SECRET"),
    secure=True
)

# ------------------------
# Admin auth
# ------------------------
ADMIN_USER = os.environ.get("ADMIN_USER","admin")
ADMIN_PASS = os.environ.get("ADMIN_PASS","password")

def check_auth(username,password):
    return username==ADMIN_USER and password==ADMIN_PASS

def requires_auth(f):
    @wraps(f)
    def decorated(*args,**kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return ('Unauthorized', 401, {'WWW-Authenticate':'Basic realm="Login Required"'})
        return f(*args,**kwargs)
    return decorated

# ------------------------
# In-memory products list
# ------------------------
products = []

# ------------------------
# HTML Templates
# ------------------------
USER_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Khali Store</title>
<link href="https://fonts.googleapis.com/css2?family=Permanent+Marker&display=swap" rel="stylesheet">
<style>
body { margin:0; font-family: Arial, sans-serif; background:#1c1c1c; color:white; }
header { display:flex; align-items:center; justify-content:center; background:#2b2b2b; color:white; font-family:'Permanent Marker', cursive; padding:20px 0; font-size:2rem; position:sticky; top:0; z-index:1000; box-shadow: 0 4px 10px rgba(0,0,0,0.5); }
header img { height:50px; margin-right:15px; }
#products { display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:20px; padding:20px; }
.product { background:#2b2b2b; border-radius:12px; box-shadow:0 4px 12px rgba(0,0,0,0.5); padding:15px; text-align:center; transition: transform 0.2s, box-shadow 0.2s; }
.product:hover { transform:translateY(-5px); box-shadow:0 8px 20px rgba(0,0,0,0.7); }
.product img { width:100%; height:200px; object-fit:cover; border-radius:10px; }
.product button { margin-top:8px; padding:8px; width:100%; background:black; color:white; border:none; border-radius:8px; cursor:pointer; transition: transform 0.2s; }
.product button:hover { transform:scale(1.05); }
#cart { position:fixed; bottom:20px; right:20px; background:black; color:white; padding:15px 20px; border-radius:50px; cursor:pointer; box-shadow: 0 4px 10px rgba(0,0,0,0.7); }
#cart-items { margin-top:10px; max-height:250px; overflow-y:auto; }
#checkout { margin-top:10px; display:none; width:100%; padding:10px; border:none; border-radius:8px; background:#0a0; color:white; cursor:pointer; }
footer { background:#111; color:white; padding:20px; text-align:center; margin-top:30px; }
h1 { text-align:center; margin:20px 0; color:white; }
</style>
</head>
<body>

<header>
  Khali Store
</header>

<h1>Products</h1>
<div id="products"></div>

<div id="cart">
  🛒 Cart (<span id="cart-count">0</span>)
  <div id="cart-items" style="display:none;"></div>
  <button id="checkout">Checkout via WhatsApp</button>
</div>

<footer>
    &copy; 2025 Khali Store. All rights reserved.
</footer>

<script>
let displayed = [];
let cart = [];

async function loadProducts(){
    try{
        const res = await fetch('/api/products',{cache:"no-store"});
        const data = await res.json();
        const container = document.getElementById('products');
        container.innerHTML='';
        data.forEach(p=>{
            const div = document.createElement('div');
            div.className='product';
            div.innerHTML=`
                <img src="${p.image_url}" alt="${p.name}">
                <br><strong>${p.name}</strong><br>
                $${p.price}<br>${p.category}<br>${p.description}
                <button onclick="addToCart('${p.name}',${p.price})">Add to Cart</button>
            `;
            container.appendChild(div);
        });
    }catch(err){ console.error("Failed to fetch products:",err);}
}

function addToCart(name,price){
    cart.push({name,price});
    updateCart();
}

function updateCart(){
    const count = document.getElementById('cart-count');
    const itemsDiv = document.getElementById('cart-items');
    const checkoutBtn = document.getElementById('checkout');
    count.textContent = cart.length;

    if(cart.length>0){
        itemsDiv.style.display='block';
        checkoutBtn.style.display='block';
        itemsDiv.innerHTML='';
        cart.forEach(item=>{
            const div=document.createElement('div');
            div.textContent=`${item.name} - $${item.price}`;
            itemsDiv.appendChild(div);
        });
    }else{
        itemsDiv.style.display='none';
        checkoutBtn.style.display='none';
    }
}

document.getElementById('checkout').addEventListener('click',()=>{
    if(cart.length===0) return;
    let orderText='Hello, I would like to order:%0A';
    cart.forEach(item=>{
        orderText+=`- ${item.name} : $${item.price}%0A`;
    });
    const waNumber='YOUR_WHATSAPP_NUMBER'; // replace with your number
    window.open(`https://wa.me/${waNumber}?text=${orderText}`,'_blank');
});

loadProducts();
setInterval(loadProducts,5000);
</script>

</body>
</html>
"""

ADMIN_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Khali Store Admin</title>
<style>
body { margin:0; font-family: Arial, sans-serif; background:#1c1c1c; color:white; }
header { display:flex; align-items:center; justify-content:center; background:#2b2b2b; color:white; font-family:'Permanent Marker', cursive; padding:20px 0; font-size:2rem; position:sticky; top:0; z-index:1000; box-shadow: 0 4px 10px rgba(0,0,0,0.5); }
form { max-width:500px; margin:20px auto; background:#2b2b2b; padding:20px; border-radius:12px; box-shadow:0 4px 12px rgba(0,0,0,0.5); }
input, button { width:100%; margin:8px 0; padding:10px; border-radius:8px; border:1px solid #555; background:#1c1c1c; color:white; }
button { background:black; color:white; border:none; cursor:pointer; transition: transform 0.2s; }
button:hover { transform: scale(1.05); }
#msg { text-align:center; margin-top:10px; color:#0f0; }
</style>
</head>
<body>

<header>Khali Store Admin</header>

<h1 style="text-align:center;">Admin Panel</h1>
<form id="form" enctype="multipart/form-data">
<input name="name" placeholder="Product Name" required>
<input name="price" type="number" step="0.01" placeholder="Price" required>
<input name="category" placeholder="Category">
<input name="description" placeholder="Description">
<input type="file" name="image" required>
<button type="submit">Upload Product</button>
</form>
<p id="msg"></p>

<script>
const form = document.getElementById('form');
const msg = document.getElementById('msg');
form.addEventListener('submit', async e=>{
    e.preventDefault();
    const fd = new FormData(form);
    try{
        const username = prompt("Username:");
        const password = prompt("Password:");
        const res = await fetch('/api/products',{
            method:'POST',
            body: fd,
            headers:{'Authorization':'Basic '+btoa(username+':'+password)}
        });
        const data = await res.json();
        msg.textContent = data.message;
        form.reset();
    }catch(err){ msg.textContent = "Upload failed!"; }
});
</script>

</body>
</html>
"""

# ------------------------
# Routes
# ------------------------
@app.route('/')
def user_page():
    return render_template_string(USER_HTML)

@app.route('/admin')
@requires_auth
def admin_page():
    return render_template_string(ADMIN_HTML)

@app.route('/api/products', methods=['GET'])
def get_products():
    return jsonify(products)

@app.route('/api/products', methods=['POST'])
@requires_auth
def add_product():
    try:
        name = request.form['name']
        price = float(request.form['price'])
        category = request.form.get('category','')
        description = request.form.get('description','')
        file = request.files.get('image')
        if not file:
            return jsonify({"message":"No image"}),400
        upload_result = cloudinary.uploader.upload(file, folder="khali_store")
        products.append({
            "name": name,
            "price": price,
            "category": category,
            "description": description,
            "image_url": upload_result['secure_url']
        })
        return jsonify({"message":"Product uploaded successfully"})
    except Exception as e:
        return jsonify({"message":f"Error: {str(e)}"}),500

# ------------------------
if __name__=="__main__":
    app.run(host='0.0.0.0', port=5000)
