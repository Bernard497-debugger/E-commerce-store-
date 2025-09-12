import os
from functools import wraps
from flask import Flask, request, jsonify, render_template_string, Response
import cloudinary
import cloudinary.uploader
import cloudinary.api

app = Flask(__name__)

# ------------------------
# Cloudinary configuration
# ------------------------
cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_NAME"),
    api_key=os.environ.get("CLOUDINARY_KEY"),
    api_secret=os.environ.get("CLOUDINARY_SECRET"),
    secure=True
)

# ------------------------
# Admin authentication
# ------------------------
ADMIN_USERNAME = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASS", "password")

def check_auth(username, password):
    return username == ADMIN_USERNAME and password == ADMIN_PASSWORD

def authenticate():
    return Response(
        'Authentication required', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'}
    )

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

# ------------------------
# User page HTML
# ------------------------
USER_HTML = """
{% raw %}
<!DOCTYPE html>
<html>
<head>
<title>Khali Store</title>
<style>
body{font-family:Arial,sans-serif;background:#f4f6f8;margin:0;padding:0;}
header{background:#111827;color:#fff;padding:15px;text-align:center;}
main{max-width:1000px;margin:30px auto;}
#filters{margin-bottom:20px;}
button.filter{padding:8px 12px;margin:2px;background:#2563eb;color:#fff;border:none;border-radius:8px;cursor:pointer;}
button.filter:hover{background:#1d4ed8;}
.product-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:15px;}
.product{background:#fff;padding:15px;border-radius:12px;box-shadow:0 4px 12px rgba(0,0,0,0.1);text-align:center;}
.product img{width:100%;height:150px;object-fit:cover;border-radius:8px;}
button.buy{margin-top:10px;padding:10px 15px;background:#10b981;color:#fff;border:none;border-radius:8px;cursor:pointer;}
button.buy:hover{background:#059669;}
#search{width:100%;padding:10px;margin-bottom:20px;border-radius:8px;border:1px solid #ccc;font-size:16px;}
</style>
</head>
<body>
<header><h1>Khali Store</h1></header>
<main>
<input type="text" id="search" placeholder="Search products...">
<div id="filters"></div>
<div class="product-grid" id="products"></div>
</main>
<script>
let products=[];

async function loadProducts(){
    const res = await fetch('/api/products', { cache: "no-store" });
    products = await res.json();
    renderFilters();
    renderProducts();
}

function renderFilters(){
    const container = document.getElementById('filters');
    const categories = [...new Set(products.map(p=>p.category).filter(c=>c))];
    container.innerHTML = '<button class="filter" onclick="filterByCategory(\'\')">All</button>';
    categories.forEach(cat=>{
        const btn = document.createElement('button');
        btn.className='filter';
        btn.textContent=cat;
        btn.onclick=()=>filterByCategory(cat);
        container.appendChild(btn);
    });
}

function filterByCategory(category){
    renderProducts(category, document.getElementById('search').value);
}

document.getElementById('search').addEventListener('input', e=>{
    renderProducts('', e.target.value);
});

function renderProducts(category='', search=''){
    const container = document.getElementById('products');
    container.innerHTML='';
    let filtered = products;
    if(category) filtered = filtered.filter(p=>p.category===category);
    if(search) filtered = filtered.filter(p=>p.name.toLowerCase().includes(search.toLowerCase())||p.description.toLowerCase().includes(search.toLowerCase()));
    filtered.forEach(p=>{
        const div = document.createElement('div');
        div.className='product';
        div.innerHTML=`
        <img src="${p.image_url}" alt="${p.name}">
        <h3>${p.name}</h3>
        <p>$${p.price.toFixed(2)}</p>
        <small>${p.description}</small><br>
        <button class="buy" onclick="buyWhatsApp('${p.name}',${p.price})">Buy via WhatsApp</button>`;
        container.appendChild(div);
    });
}

function buyWhatsApp(name, price){
    const phone = "YOUR_PHONE_NUMBER"; // replace with your WhatsApp number
    const msg = `Hello, I want to buy: ${name} for $${price.toFixed(2)}`;
    const waUrl = `https://wa.me/${phone}?text=${encodeURIComponent(msg)}`;
    window.open(waUrl,'_blank');
}

loadProducts();
</script>
</body>
</html>
{% endraw %}
"""

# ------------------------
# Admin page HTML
# ------------------------
ADMIN_HTML = """
{% raw %}
<!DOCTYPE html>
<html>
<head>
<title>Khali Store Admin</title>
<style>
body{font-family:Arial,sans-serif;background:#f4f6f8;margin:0;padding:0;}
header{background:#111827;color:#fff;padding:15px;text-align:center;}
main{max-width:800px;margin:30px auto;background:#fff;padding:20px;border-radius:12px;box-shadow:0 4px 12px rgba(0,0,0,0.1);}
form{display:flex;flex-direction:column;gap:15px;}
input,textarea,select{padding:10px;border:1px solid #ddd;border-radius:8px;font-size:14px;}
button{background:#2563eb;color:#fff;padding:12px;border:none;border-radius:8px;font-size:16px;cursor:pointer;}
button:hover{background:#1d4ed8;}
#message{margin-top:10px;font-size:14px;}
#products{margin-top:20px;}
.product{display:flex;align-items:center;background:#f9fafb;padding:10px;margin-bottom:10px;border-radius:8px;gap:10px;}
.product img{width:60px;height:60px;object-fit:cover;border-radius:6px;}
</style>
</head>
<body>
<header><h1>Khali Store Admin</h1></header>
<main>
<h2>Add New Product</h2>
<form id="productForm" enctype="multipart/form-data">
<input type="text" name="name" placeholder="Product Name" required>
<input type="number" name="price" placeholder="Price" step="0.01" required>
<input type="text" name="category" placeholder="Category">
<textarea name="description" placeholder="Description"></textarea>
<input type="file" name="image" accept="image/*" required>
<button type="submit">Add Product</button>
</form>
<p id="message"></p>
<div id="product-list"><h2>Current Products</h2><div id="products"></div></div>
</main>
<script>
const form=document.getElementById('productForm');
const message=document.getElementById('message');
const productsDiv=document.getElementById('products');

function renderProducts(data){
    productsDiv.innerHTML='';
    data.forEach(p=>{
        const div=document.createElement('div');
        div.className='product';
        div.innerHTML=`<img src="${p.image_url}" alt="${p.name}"><div><strong>${p.name}</strong><br>${p.category ? p.category+'<br>' : ''}$${p.price.toFixed(2)}<br><small>${p.description}</small></div>`;
        productsDiv.appendChild(div);
    });
}

async function loadProducts(){
    try{
        const res=await fetch('/api/products', { cache: "no-store" });
        const data=await res.json();
        renderProducts(data);
    }catch(err){
        productsDiv.innerHTML='<p style="color:red;">Failed to load products.</p>';
    }
}
loadProducts();

form.addEventListener('submit',async e=>{
    e.preventDefault();
    const formData=new FormData(form);
    if(!formData.get('image')){
        message.textContent="Please select an image!";
        return;
    }
    try {
        const res=await fetch('/api/products',{method:'POST',body:formData,headers:{'Authorization':'Basic '+btoa(prompt('Username')+':'+prompt('Password'))}});
        const result=await res.json();
        message.textContent=result.message;
        form.reset();
        loadProducts();
    } catch(err){
        message.textContent="Upload failed!";
    }
});
</script>
</body>
</html>
{% endraw %}
"""

# ------------------------
# ROUTES
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
    try:
        res = cloudinary.api.resources(type='upload', prefix='khali_store')
        products_list = []
        for r in res.get('resources', []):
            metadata = r.get('context', {}).get('custom', {})
            products_list.append({
                "name": metadata.get('name', 'Unnamed'),
                "price": float(metadata.get('price', 0)),
                "category": metadata.get('category', ''),
                "description": metadata.get('description', ''),
                "image_url": r['secure_url']
            })
        return jsonify(products_list)
    except Exception as e:
        return jsonify({"message": f"Failed to fetch products: {str(e)}"}), 500

@app.route('/api/products', methods=['POST'])
@requires_auth
def add_product():
    try:
        name = request.form['name']
        price = float(request.form['price'])
        category = request.form.get('category', '')
        description = request.form.get('description', '')

        file = request.files.get('image')
        if not file:
            return jsonify({"message":"No image uploaded!"}), 400

        upload_result = cloudinary.uploader.upload(
            file,
            folder="khali_store",
            context=f"name={name}|price={price}|category={category}|description={description}"
        )

        return jsonify({"message": "Product added successfully!"})
    except Exception as e:
        return jsonify({"message": f"Failed to add product: {str(e)}"}), 500

# ------------------------
# Run app
# ------------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
