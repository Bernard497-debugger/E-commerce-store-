from flask import Flask, request, jsonify, render_template_string, redirect
import cloudinary
import cloudinary.uploader
import json
import os

app = Flask(__name__)

# Cloudinary setup (reads CLOUDINARY_URL from environment automatically)
cloudinary.config()

# Local storage for product metadata (in memory, since images go to Cloudinary)
PRODUCTS_FILE = "products.json"

def load_products():
    if os.path.exists(PRODUCTS_FILE):
        with open(PRODUCTS_FILE, "r") as f:
            return json.load(f)
    return []

def save_products(products):
    with open(PRODUCTS_FILE, "w") as f:
        json.dump(products, f)

# ==============================
# Admin Page (upload products)
# ==============================
@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        try:
            name = request.form.get("name")
            price = request.form.get("price")
            image = request.files["image"]

            # Upload image to Cloudinary
            upload_result = cloudinary.uploader.upload(image)
            image_url = upload_result["secure_url"]

            # Save product metadata
            products = load_products()
            products.append({"name": name, "price": price, "image": image_url})
            save_products(products)

            return redirect("/admin")
        except Exception as e:
            return f"Failed to add product: {str(e)}", 400

    products = load_products()
    return render_template_string("""
    <h1>Admin Panel</h1>
    <form method="post" enctype="multipart/form-data">
        <input type="text" name="name" placeholder="Product Name" required><br>
        <input type="text" name="price" placeholder="Product Price" required><br>
        <input type="file" name="image" accept="image/*" required><br>
        <button type="submit">Add Product</button>
    </form>
    <h2>Uploaded Products</h2>
    <ul>
    {% for p in products %}
        <li>{{ p.name }} - ${{ p.price }} <br><img src="{{ p.image }}" width="100"></li>
    {% endfor %}
    </ul>
    """, products=products)

# ==============================
# User Page (storefront)
# ==============================
@app.route("/")
def user_page():
    products = load_products()
    return render_template_string("""
    <h1>Khali Store</h1>
    <div style="display:flex;flex-wrap:wrap;gap:20px;">
    {% for p in products %}
        <div style="border:1px solid #ccc;padding:10px;border-radius:8px;width:200px;text-align:center;">
            <img src="{{ p.image }}" style="max-width:100%;border-radius:8px;"><br>
            <b>{{ p.name }}</b><br>
            ${{ p.price }}<br>
        </div>
    {% endfor %}
    </div>
    """, products=products)

# ==============================
# API to fetch products
# ==============================
@app.route("/api/products")
def api_products():
    return jsonify(load_products())

# ==============================
# Run app
# ==============================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
