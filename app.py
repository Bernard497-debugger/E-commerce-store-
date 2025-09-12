import os
from flask import Flask, request, jsonify, render_template_string
import cloudinary
import cloudinary.uploader
import cloudinary.api

app = Flask(__name__)

# ------------------------
# Cloudinary configuration
# ------------------------
cloudinary.config(cloudinary_url=os.environ.get("CLOUDINARY_URL"))

# ------------------------
# USER page HTML
# ------------------------
USER_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Khali Store</title>
<style>
body{{font-family:Arial,sans-serif;background:#f4f6f8;margin:0;padding:0;}}
header{{background:#111827;color:#fff;padding:15px;text-align:center;}}
main{{max-width:1000px;margin:30px auto;}}
.product-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:15px;}}
.product{{background:#fff;padding:15px;border-radius:12px;box-shadow:0 4px 12px rgba(0,0,0,0.1);text-align:center;}}
.product img{{width:100%;height:150px;object-fit:cover;border-radius:8px;}}
button{{margin-top:10px;padding:10px 15px;background:#2563eb;color:#fff;border:none;border-radius:8px;cursor:pointer;}}
button:hover{{background:#1d4ed8;}}
</style>
</head>
<body>
<header><h1>Khali Store</h1></header>
<main>
<div class="product-grid" id="products"></div>
</main>
<script>
async function loadProducts(){{
    const res = await fetch('/api/products');
    const data = await res.json();
    const container = document.getElementById('products');
    container.innerHTML='';
    data.forEach(p=>{{
        const div = document.createElement('div');
        div.className='product';
        div.innerHTML=`
        <img src="${{p.image_url}}" alt="${{p.name}}">
        <h3>${{p.name}}</h3>
        <p>$${{p.price.toFixed(2)}}</p>
        <small>${{p.description}}</small>
        <button>Add to Cart</button>`;
        container.appendChild(div);
    }});
}}
loadProducts();
</script>
</body>
</html>
"""

# ------------------------
# ADMIN page HTML
# ------------------------
ADMIN_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Khali Commerce Admin</title>
<style>
body{{font-family:Arial,sans-serif;background:#f4f6f8;margin:0;padding:0;}}
header{{background:#111827;color:#fff;padding:15px;text-align:center;}}
main{{max-width:800px;margin:30px auto;background:#fff;padding:20px;border-radius:12px;box-shadow:0 4px 12px rgba(0,0,0,0.1);}}
form{{display:flex;flex-direction:column;gap:15px;}}
input,textarea{{padding:10px;border:1px solid #ddd;border-radius:8px;font-size:14px;}}
button{{background:#2563eb;color:#fff;padding:12px;border:none;border-radius:8px;font-size:16px;cursor:pointer;}}
button:hover{{background:#1d4ed8;}}
#message{{margin-top:10px;font-size:14px;}}
#products{{margin-top:20px;}}
.product{{display:flex;align-items:center;background:#f9fafb;padding:10px;margin-bottom:10px;border-radius:8px;gap:10px;}}
.product img{{width:60px;height:60px;object-fit:cover;border-radius:6px;}}
</style>
</head>
<body>
<header><h1>Khali Commerce Admin</h1></header>
<main>
<h2>Add New Product</h2>
<form id="productForm" enctype="multipart/form-data">
<input type="text" name="name" placeholder="Product Name" required>
<input type="number" name="price" placeholder="Price" step="0.01" required>
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

async function loadProducts(){{
    const res=await fetch('/api/products');
    const data=await res.json();
    productsDiv.innerHTML='';
    data.forEach(p=>{{
        const div=document.createElement('div');
        div.className='product';
        div.innerHTML=`<img src="${{p.image_url}}" alt="${{p.name}}"><div><strong>${{p.name}}</strong><br>$${{p.price.toFixed(2)}}<br><small>${{p.description}}</small></div>`;
        productsDiv.appendChild(div);
    }});
}}
loadProducts();

form.addEventListener('submit',async e=>{{
    e.preventDefault();
    const formData=new FormData(form);
    if(!formData.get('image')){{
        message.textContent="Please select an image!";
        return;
    }}
    const res=await fetch('/api/products',{{method:'POST',body:formData}});
    const result=await res.json();
    message.textContent=result.message;
    form.reset();
    loadProducts();
}});
</script>
</body>
</html>
"""

# ------------------------
# API Routes
# ------------------------
@app.route('/')
def user_page():
    return render_template_string(USER_HTML)

@app.route('/admin')
def admin_page():
    return render_template_string(ADMIN_HTML)

@app.route('/api/products', methods=['GET'])
def get_products():
    # Fetch all images with metadata from Cloudinary folder "khali_store"
    resources = cloudinary.api.resources(type="upload", prefix="khali_store", max_results=500)["resources"]
    products = []
    for r in resources:
        meta = r.get("context", {}).get("custom", {})
        products.append({{
            "name": meta.get("name", "Unnamed"),
            "price": float(meta.get("price", 0)),
            "description": meta.get("description", ""),
            "image_url": r["secure_url"]
        }})
    return jsonify(products)

@app.route('/api/products', methods=['POST'])
def add_product():
    name = request.form['name']
    price = request.form['price']
    description = request.form.get('description', '')

    file = request.files.get('image')
    if not file:
        return jsonify({{"message":"No image uploaded!"}}), 400

    # Upload to Cloudinary in folder "khali_store" with metadata
    upload_result = cloudinary.uploader.upload(
        file,
        folder="khali_store",
        context=f"name={name}|price={price}|description={description}"
    )

    return jsonify({{"message": "Product added successfully!"}})

# ------------------------
# Run
# ------------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
