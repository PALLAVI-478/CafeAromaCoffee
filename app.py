import os
import sqlite3
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "cafe.db")

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "cafe-aroma-dev-secret-change-before-deploy")

OWNER_EMAIL = os.environ.get("OWNER_EMAIL", "owner@cafe.com")
OWNER_PASSWORD = os.environ.get("OWNER_PASSWORD", "owner123")

MENU_IMAGES = {
    "Coffee": "coffee.svg", "Tea & Refreshers": "tea.svg", "Burgers & Pizza": "burger.svg",
    "Sandwiches & Sides": "sandwich.svg", "Pasta": "pasta.svg", "Desserts": "dessert.svg",
}

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db

@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login to continue.", "warning")
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped

def owner_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("owner_logged_in"):
            flash("Owner login required.", "warning")
            return redirect(url_for("owner_login"))
        return view(*args, **kwargs)
    return wrapped

def cart_rows(user_id):
    return get_db().execute("""
        SELECT cart.id AS cart_id, cart.quantity,
               menu.id AS menu_id, menu.name, menu.description, menu.price, menu.emoji, menu.image
        FROM cart JOIN menu ON menu.id = cart.menu_id
        WHERE cart.user_id = ? ORDER BY cart.id DESC
    """, (user_id,)).fetchall()

def cart_total(rows):
    return sum(float(row["price"]) * int(row["quantity"]) for row in rows)

@app.context_processor
def inject_globals():
    count = 0
    if "user_id" in session:
        row = get_db().execute("SELECT COALESCE(SUM(quantity),0) AS count FROM cart WHERE user_id=?", (session["user_id"],)).fetchone()
        count = int(row["count"])
    return {"cart_count": count, "cafe_name": "Café Aroma.coffee"}

@app.route("/")
def home():
    db = get_db()
    featured = db.execute("SELECT * FROM menu ORDER BY id LIMIT 6").fetchall()
    return render_template("index.html", featured=featured)

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/menu")
def menu():
    items = get_db().execute("SELECT * FROM menu ORDER BY id").fetchall()
    return render_template("menu.html", items=items)

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not name or not email or len(password) < 6:
            flash("Enter your name and email, and use a password of at least 6 characters.", "danger")
            return render_template("register.html")
        db = get_db()
        try:
            db.execute("INSERT INTO users (name,email,password) VALUES (?,?,?)", (name, email, generate_password_hash(password)))
            db.commit()
            flash("Account created! Please login.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("That email is already registered.", "danger")
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = get_db().execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        if user and check_password_hash(user["password"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            flash(f"Welcome back, {user['name']}!", "success")
            return redirect(request.args.get("next") or url_for("home"))
        flash("Invalid email or password.", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user_id", None)
    session.pop("user_name", None)
    flash("You have been logged out.", "success")
    return redirect(url_for("home"))

@app.route("/account")
@login_required
def account():
    user = get_db().execute("SELECT id,name,email FROM users WHERE id=?", (session["user_id"],)).fetchone()
    return render_template("account.html", user=user)

@app.route("/owner-login", methods=["GET", "POST"])
def owner_login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if email == OWNER_EMAIL.lower() and password == OWNER_PASSWORD:
            session.clear()
            session["owner_logged_in"] = True
            flash("Owner dashboard unlocked.", "success")
            return redirect(url_for("owner_dashboard"))
        flash("Invalid owner credentials.", "danger")
    return render_template("owner_login.html")

@app.route("/owner-logout")
def owner_logout():
    session.pop("owner_logged_in", None)
    flash("Owner session ended.", "success")
    return redirect(url_for("home"))

@app.route("/owner-dashboard")
@owner_required
def owner_dashboard():
    db = get_db()
    stats = {
        "users": db.execute("SELECT COUNT(*) FROM users").fetchone()[0],
        "menu": db.execute("SELECT COUNT(*) FROM menu").fetchone()[0],
        "orders": db.execute("SELECT COUNT(*) FROM orders").fetchone()[0],
        "revenue": db.execute("SELECT COALESCE(SUM(total),0) FROM orders WHERE status != 'Cancelled'").fetchone()[0],
    }
    recent = db.execute("""
        SELECT orders.*, users.name AS customer_name, users.email AS customer_email
        FROM orders JOIN users ON users.id=orders.user_id
        ORDER BY orders.id DESC LIMIT 8
    """).fetchall()
    return render_template("owner_dashboard.html", stats=stats, recent=recent)

@app.route("/add-menu", methods=["GET", "POST"])
@owner_required
def add_menu():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        price = request.form.get("price", "0").strip()
        emoji = request.form.get("emoji", "☕").strip() or "☕"
        image = request.form.get("image", "coffee.svg").strip() or "coffee.svg"
        try:
            price = float(price)
            if price < 0: raise ValueError
            get_db().execute("INSERT INTO menu(name,description,price,emoji,image) VALUES(?,?,?,?,?)", (name,description,price,emoji,image))
            get_db().commit()
            flash("Menu item added.", "success")
            return redirect(url_for("owner_dashboard"))
        except ValueError:
            flash("Please enter a valid price.", "danger")
    return render_template("add_menu.html")

@app.route("/edit-menu/<int:item_id>", methods=["GET", "POST"])
@owner_required
def edit_menu(item_id):
    db = get_db()
    item = db.execute("SELECT * FROM menu WHERE id=?", (item_id,)).fetchone()
    if not item: return redirect(url_for("owner_dashboard"))
    if request.method == "POST":
        try:
            price = float(request.form.get("price", "0"))
            db.execute("UPDATE menu SET name=?,description=?,price=?,emoji=?,image=? WHERE id=?", (
                request.form.get("name", "").strip(), request.form.get("description", "").strip(), price,
                request.form.get("emoji", "☕").strip() or "☕", request.form.get("image", "coffee.svg").strip() or "coffee.svg", item_id))
            db.commit()
            flash("Menu item updated.", "success")
            return redirect(url_for("owner_dashboard"))
        except ValueError:
            flash("Please enter a valid price.", "danger")
    return render_template("edit_menu.html", item=item)

@app.route("/delete-menu/<int:item_id>", methods=["POST"])
@owner_required
def delete_menu(item_id):
    db = get_db()
    db.execute("DELETE FROM cart WHERE menu_id=?", (item_id,))
    db.execute("DELETE FROM menu WHERE id=?", (item_id,))
    db.commit()
    flash("Menu item removed.", "success")
    return redirect(url_for("owner_dashboard"))

@app.route("/add-to-cart/<int:item_id>", methods=["POST"])
@login_required
def add_to_cart(item_id):
    db = get_db()
    if not db.execute("SELECT id FROM menu WHERE id=?", (item_id,)).fetchone():
        flash("That menu item is no longer available.", "danger")
        return redirect(url_for("menu"))
    db.execute("""INSERT INTO cart(user_id,menu_id,quantity) VALUES(?,?,1)
                  ON CONFLICT(user_id,menu_id) DO UPDATE SET quantity=quantity+1""", (session["user_id"], item_id))
    db.commit()
    flash("Added to your cart.", "success")
    return redirect(request.referrer or url_for("menu"))

@app.route("/cart")
@login_required
def cart():
    rows = cart_rows(session["user_id"])
    return render_template("cart.html", items=rows, total=cart_total(rows))

@app.route("/update-cart/<int:cart_id>", methods=["POST"])
@login_required
def update_cart(cart_id):
    quantity = max(1, int(request.form.get("quantity", 1)))
    get_db().execute("UPDATE cart SET quantity=? WHERE id=? AND user_id=?", (quantity, cart_id, session["user_id"]))
    get_db().commit()
    return redirect(url_for("cart"))

@app.route("/remove-from-cart/<int:cart_id>", methods=["POST"])
@login_required
def remove_from_cart(cart_id):
    get_db().execute("DELETE FROM cart WHERE id=? AND user_id=?", (cart_id, session["user_id"]))
    get_db().commit()
    flash("Item removed from cart.", "success")
    return redirect(url_for("cart"))

@app.route("/checkout")
@login_required
def checkout():
    rows = cart_rows(session["user_id"])
    if not rows:
        flash("Your cart is empty.", "warning")
        return redirect(url_for("menu"))
    user = get_db().execute("SELECT * FROM users WHERE id=?", (session["user_id"],)).fetchone()
    return render_template("checkout.html", items=rows, total=cart_total(rows), user=user)

@app.route("/place-order", methods=["POST"])
@login_required
def place_order():
    db = get_db()
    rows = cart_rows(session["user_id"])
    if not rows:
        flash("Your cart is empty.", "warning")
        return redirect(url_for("menu"))
    total = cart_total(rows)
    customer_name = request.form.get("customer_name", "").strip()
    phone = request.form.get("phone", "").strip()
    order_type = request.form.get("order_type", "Pickup")
    notes = request.form.get("notes", "").strip()
    if not customer_name or not phone:
        flash("Please enter your name and phone number.", "danger")
        return redirect(url_for("checkout"))
    cur = db.execute("INSERT INTO orders(user_id,total,status,customer_name,phone,order_type,notes) VALUES(?,?,?,?,?,?,?)",
                     (session["user_id"], total, "Pending", customer_name, phone, order_type, notes))
    order_id = cur.lastrowid
    for row in rows:
        db.execute("INSERT INTO order_items(order_id,menu_id,quantity,price) VALUES(?,?,?,?)", (order_id,row["menu_id"],row["quantity"],row["price"]))
    db.execute("DELETE FROM cart WHERE user_id=?", (session["user_id"],))
    db.commit()
    return redirect(url_for("order_success", order_id=order_id))

@app.route("/order-success/<int:order_id>")
@login_required
def order_success(order_id):
    order = get_db().execute("SELECT * FROM orders WHERE id=? AND user_id=?", (order_id,session["user_id"])).fetchone()
    if not order: return redirect(url_for("my_orders"))
    return render_template("order_success.html", order=order)

@app.route("/my-orders")
@login_required
def my_orders():
    db = get_db()
    orders = db.execute("SELECT * FROM orders WHERE user_id=? ORDER BY id DESC", (session["user_id"],)).fetchall()
    return render_template("my_orders.html", orders=orders)

@app.route("/my-orders/<int:order_id>")
@login_required
def order_detail(order_id):
    db = get_db()
    order = db.execute("SELECT * FROM orders WHERE id=? AND user_id=?", (order_id,session["user_id"])).fetchone()
    if not order: return redirect(url_for("my_orders"))
    items = db.execute("""
        SELECT order_items.*, menu.name, menu.emoji, menu.image
        FROM order_items JOIN menu ON menu.id=order_items.menu_id WHERE order_id=?
    """, (order_id,)).fetchall()
    return render_template("order_detail.html", order=order, items=items)

@app.route("/owner-orders")
@owner_required
def owner_orders():
    db = get_db()
    orders = db.execute("SELECT orders.*, users.email FROM orders JOIN users ON users.id=orders.user_id ORDER BY orders.id DESC").fetchall()
    return render_template("owner_orders.html", orders=orders)

@app.route("/update-order-status/<int:order_id>", methods=["POST"])
@owner_required
def update_order_status(order_id):
    status = request.form.get("status", "Pending")
    allowed = {"Pending", "Preparing", "Ready", "Completed", "Cancelled"}
    if status in allowed:
        get_db().execute("UPDATE orders SET status=? WHERE id=?", (status,order_id))
        get_db().commit()
        flash(f"Order #{order_id} updated to {status}.", "success")
    return redirect(url_for("owner_orders"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
