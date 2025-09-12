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
USER_HTML = """<html>
<head><title>Khali Store</title></head>
<body>
<h1>Khali Store</h1>
<div id="products"></div>

<script>
let displayed = [];

async function loadProducts(){
    try{
        const res = await fetch('/api/products', { cache:"no-store" });
        const data = await res.json();
        const container = document.getElementById('products');

        data.forEach(p=>{
            if(!displayed.includes(p.image_url)){
                const div = document.createElement('div');
                div.innerHTML = `<img src="${p.image_url}" width="200"><br>${p.name} - $${p.price}<br>${p.category}<br>${p.description}<hr>`;
                container.appendChild(div);
                displayed.push(p.image_url);
            }
        });
    } catch(err){
        console.error("Failed to fetch products:", err);
    }
}

// Initial load
loadProducts();

// Poll every 5 seconds for new products
setInterval(loadProducts, 5000);
</script>
</body>
</html>"""

ADMIN_HTML = """<html>
<head><title>Admin - Khali Store</title></head>
<body>
<h1>Admin Panel</h1>
<form id="form" enctype="multipart/form-data">
<input name="name" placeholder="Name" required><br>
<input name="price" type="number" step="0.01" placeholder="Price" required><br>
<input name="category" placeholder="Category"><br>
<input name="description" placeholder="Description"><br>
<input type="file" name="image" required><br>
<button type="submit">Upload</button>
</form>
<p id="msg"></p>
<script>
const form = document.getElementById('form');
const msg = document.getElementById('msg');
form.addEventListener('submit', async e=>{
    e.preventDefault();
    const fd = new FormData(form);
    const username=prompt('Username');
    const password=prompt('Password');
    try{
        const res = await fetch('/api/products',{
            method:'POST',
            body: fd,
            headers:{'Authorization':'Basic '+btoa(username+':'+password)}
        });
        const data = await res.json();
        msg.textContent=data.message;
        form.reset();
    } catch(err){
        msg.textContent="Upload failed!";
    }
});
</script>
</body>
</html>"""

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

@app.route('/api/products',methods=['GET'])
def get_products():
    return jsonify(products)

@app.route('/api/products',methods=['POST'])
@requires_auth
def add_product():
    try:
        name=request.form['name']
        price=float(request.form['price'])
        category=request.form.get('category','')
        description=request.form.get('description','')
        file=request.files.get('image')
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
    app.run(host='0.0.0.0',port=5000)
