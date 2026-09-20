from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.secret_key = "cafe-aroma-secret-key"

DATABASE = "cafe.db"


def get_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


# =====================================================
# HOME
# =====================================================

@app.route("/")
def home():

    connection = get_db()

    menu_items = connection.execute(
        "SELECT * FROM menu ORDER BY id"
    ).fetchall()

    connection.close()

    return render_template(
        "index.html",
        menu_items=menu_items
    )


# =====================================================
# REGISTER
# =====================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            return """
            <h2>Passwords do not match.</h2>
            <a href="/register">Go Back</a>
            """

        hashed_password = generate_password_hash(password)

        connection = get_db()

        try:

            connection.execute(
                """
                INSERT INTO users
                (name, email, password)
                VALUES (?, ?, ?)
                """,
                (name, email, hashed_password)
            )

            connection.commit()

        except sqlite3.IntegrityError:

            connection.close()

            return """
            <h2>Email already registered.</h2>
            <a href="/login">Login here</a>
            """

        connection.close()

        return redirect(url_for("login"))

    return render_template("register.html")


# =====================================================
# CUSTOMER LOGIN
# =====================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        connection = get_db()

        user = connection.execute(
            """
            SELECT *
            FROM users
            WHERE email = ?
            """,
            (email,)
        ).fetchone()

        connection.close()

        if user and check_password_hash(
            user["password"],
            password
        ):

            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["user_email"] = user["email"]

            return redirect(url_for("account"))

        return """
        <h2>Invalid email or password.</h2>
        <a href="/login">Try Again</a>
        """

    return render_template("login.html")


# =====================================================
# ACCOUNT
# =====================================================

@app.route("/account")
def account():

    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template(
        "account.html",
        name=session["user_name"],
        email=session["user_email"]
    )


# =====================================================
# CUSTOMER LOGOUT
# =====================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("home"))


# =====================================================
# OWNER LOGIN
# =====================================================

@app.route("/owner-login", methods=["GET", "POST"])
def owner_login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        if (
            email == "owner@cafe.com"
            and password == "owner123"
        ):

            session["owner_logged_in"] = True

            return redirect(
                url_for("owner_dashboard")
            )

        return """
        <h2>Invalid owner email or password.</h2>
        <a href="/owner-login">Try Again</a>
        """

    return render_template("owner_login.html")


# =====================================================
# OWNER DASHBOARD
# =====================================================

@app.route("/owner-dashboard")
def owner_dashboard():

    if not session.get("owner_logged_in"):
        return redirect(url_for("owner_login"))

    connection = get_db()

    customer_count = connection.execute(
        "SELECT COUNT(*) FROM users"
    ).fetchone()[0]

    menu_count = connection.execute(
        "SELECT COUNT(*) FROM menu"
    ).fetchone()[0]

    order_count = connection.execute(
        "SELECT COUNT(*) FROM orders"
    ).fetchone()[0]

    connection.close()

    return render_template(
        "owner_dashboard.html",
        customer_count=customer_count,
        menu_count=menu_count,
        order_count=order_count
    )


# =====================================================
# OWNER LOGOUT
# =====================================================

@app.route("/owner-logout")
def owner_logout():

    session.pop("owner_logged_in", None)

    return redirect(url_for("owner_login"))


# =====================================================
# MENU MANAGEMENT
# =====================================================

@app.route("/menu")
def menu():

    if not session.get("owner_logged_in"):
        return redirect(url_for("owner_login"))

    connection = get_db()

    menu_items = connection.execute(
        "SELECT * FROM menu ORDER BY id"
    ).fetchall()

    connection.close()

    return render_template(
        "menu.html",
        menu_items=menu_items
    )


# =====================================================
# ADD MENU
# =====================================================

@app.route("/add-menu", methods=["GET", "POST"])
def add_menu():

    if not session.get("owner_logged_in"):
        return redirect(url_for("owner_login"))

    if request.method == "POST":

        name = request.form["name"]
        description = request.form["description"]
        price = request.form["price"]
        emoji = request.form["emoji"]

        connection = get_db()

        connection.execute(
            """
            INSERT INTO menu
            (name, description, price, emoji)
            VALUES (?, ?, ?, ?)
            """,
            (name, description, price, emoji)
        )

        connection.commit()
        connection.close()

        return redirect(url_for("menu"))

    return render_template("add_menu.html")


# =====================================================
# EDIT MENU
# =====================================================

@app.route(
    "/edit-menu/<int:item_id>",
    methods=["GET", "POST"]
)
def edit_menu(item_id):

    if not session.get("owner_logged_in"):
        return redirect(url_for("owner_login"))

    connection = get_db()

    item = connection.execute(
        """
        SELECT *
        FROM menu
        WHERE id = ?
        """,
        (item_id,)
    ).fetchone()

    if item is None:

        connection.close()

        return """
        <h2>Menu item not found.</h2>
        <a href="/menu">Back to Menu</a>
        """

    if request.method == "POST":

        name = request.form["name"]
        description = request.form["description"]
        price = request.form["price"]
        emoji = request.form["emoji"]

        connection.execute(
            """
            UPDATE menu
            SET
                name = ?,
                description = ?,
                price = ?,
                emoji = ?
            WHERE id = ?
            """,
            (
                name,
                description,
                price,
                emoji,
                item_id
            )
        )

        connection.commit()
        connection.close()

        return redirect(url_for("menu"))

    connection.close()

    return render_template(
        "edit_menu.html",
        item=item
    )


# =====================================================
# DELETE MENU
# =====================================================

@app.route(
    "/delete-menu/<int:item_id>",
    methods=["POST"]
)
def delete_menu(item_id):

    if not session.get("owner_logged_in"):
        return redirect(url_for("owner_login"))

    connection = get_db()

    connection.execute(
        """
        DELETE FROM menu
        WHERE id = ?
        """,
        (item_id,)
    )

    connection.commit()
    connection.close()

    return redirect(url_for("menu"))


# =====================================================
# ADD TO CART
# =====================================================

@app.route(
    "/add-to-cart/<int:item_id>",
    methods=["POST"]
)
def add_to_cart(item_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    connection = get_db()

    existing_item = connection.execute(
        """
        SELECT *
        FROM cart
        WHERE user_id = ?
        AND menu_id = ?
        """,
        (user_id, item_id)
    ).fetchone()

    if existing_item:

        connection.execute(
            """
            UPDATE cart
            SET quantity = quantity + 1
            WHERE user_id = ?
            AND menu_id = ?
            """,
            (user_id, item_id)
        )

    else:

        connection.execute(
            """
            INSERT INTO cart
            (user_id, menu_id, quantity)
            VALUES (?, ?, 1)
            """,
            (user_id, item_id)
        )

    connection.commit()
    connection.close()

    return redirect(url_for("cart"))


# =====================================================
# CART
# =====================================================

@app.route("/cart")
def cart():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    connection = get_db()

    cart_items = connection.execute(
        """
        SELECT
            cart.id,
            cart.quantity,
            menu.id AS menu_id,
            menu.name,
            menu.description,
            menu.price,
            menu.emoji
        FROM cart
        JOIN menu
        ON cart.menu_id = menu.id
        WHERE cart.user_id = ?
        ORDER BY cart.id
        """,
        (user_id,)
    ).fetchall()

    connection.close()

    total = 0

    for item in cart_items:
        total += item["price"] * item["quantity"]

    return render_template(
        "cart.html",
        cart_items=cart_items,
        total=total
    )


# =====================================================
# UPDATE CART
# =====================================================

@app.route(
    "/update-cart/<int:cart_id>",
    methods=["POST"]
)
def update_cart(cart_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    try:
        quantity = int(request.form["quantity"])
    except (ValueError, TypeError):
        quantity = 1

    user_id = session["user_id"]

    connection = get_db()

    if quantity <= 0:

        connection.execute(
            """
            DELETE FROM cart
            WHERE id = ?
            AND user_id = ?
            """,
            (cart_id, user_id)
        )

    else:

        connection.execute(
            """
            UPDATE cart
            SET quantity = ?
            WHERE id = ?
            AND user_id = ?
            """,
            (quantity, cart_id, user_id)
        )

    connection.commit()
    connection.close()

    return redirect(url_for("cart"))


# =====================================================
# REMOVE FROM CART
# =====================================================

@app.route(
    "/remove-from-cart/<int:cart_id>",
    methods=["POST"]
)
def remove_from_cart(cart_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    connection = get_db()

    connection.execute(
        """
        DELETE FROM cart
        WHERE id = ?
        AND user_id = ?
        """,
        (cart_id, user_id)
    )

    connection.commit()
    connection.close()

    return redirect(url_for("cart"))


# =====================================================
# CHECKOUT
# =====================================================

@app.route("/checkout")
def checkout():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    connection = get_db()

    cart_items = connection.execute(
        """
        SELECT
            cart.id,
            cart.quantity,
            menu.name,
            menu.description,
            menu.price,
            menu.emoji
        FROM cart
        JOIN menu
        ON cart.menu_id = menu.id
        WHERE cart.user_id = ?
        ORDER BY cart.id
        """,
        (user_id,)
    ).fetchall()

    connection.close()

    if not cart_items:
        return redirect(url_for("cart"))

    total = 0

    for item in cart_items:
        total += item["price"] * item["quantity"]

    return render_template(
        "checkout.html",
        cart_items=cart_items,
        total=total
    )


# =====================================================
# PLACE ORDER
# =====================================================

@app.route(
    "/place-order",
    methods=["POST"]
)
def place_order():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    connection = get_db()

    cart_items = connection.execute(
        """
        SELECT
            cart.menu_id,
            cart.quantity,
            menu.name,
            menu.price
        FROM cart
        JOIN menu
        ON cart.menu_id = menu.id
        WHERE cart.user_id = ?
        """,
        (user_id,)
    ).fetchall()

    if not cart_items:

        connection.close()

        return redirect(url_for("cart"))

    total = 0

    for item in cart_items:
        total += item["price"] * item["quantity"]

    # Create order
    cursor = connection.execute(
        """
        INSERT INTO orders
        (user_id, total, status)
        VALUES (?, ?, ?)
        """,
        (user_id, total, "Pending")
    )

    order_id = cursor.lastrowid

    # Save every cart item
    for item in cart_items:

        connection.execute(
            """
            INSERT INTO order_items
            (order_id, menu_id, quantity, price)
            VALUES (?, ?, ?, ?)
            """,
            (
                order_id,
                item["menu_id"],
                item["quantity"],
                item["price"]
            )
        )

    # Clear cart
    connection.execute(
        """
        DELETE FROM cart
        WHERE user_id = ?
        """,
        (user_id,)
    )

    connection.commit()
    connection.close()

    return redirect(
        url_for(
            "order_success",
            order_id=order_id
        )
    )


# =====================================================
# ORDER SUCCESS
# =====================================================

@app.route("/order-success/<int:order_id>")
def order_success(order_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    connection = get_db()

    order = connection.execute(
        """
        SELECT
            orders.id,
            orders.total,
            orders.status,
            orders.created_at
        FROM orders
        WHERE orders.id = ?
        AND orders.user_id = ?
        """,
        (order_id, user_id)
    ).fetchone()

    connection.close()

    if order is None:

        return """
        <h2>Order not found.</h2>
        <a href="/">Go Home</a>
        """

    return render_template(
        "order_success.html",
        order=order
    )


# =====================================================
# MY ORDERS
# =====================================================

@app.route("/my-orders")
def my_orders():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    connection = get_db()

    orders = connection.execute(
        """
        SELECT
            id,
            total,
            status,
            created_at
        FROM orders
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (user_id,)
    ).fetchall()

    connection.close()

    return render_template(
        "my_orders.html",
        orders=orders
    )


# =====================================================
# OWNER ORDERS
# =====================================================

@app.route("/owner-orders")
def owner_orders():

    if not session.get("owner_logged_in"):
        return redirect(url_for("owner_login"))

    connection = get_db()

    orders = connection.execute(
        """
        SELECT
            orders.id,
            orders.total,
            orders.status,
            orders.created_at,
            users.name,
            users.email
        FROM orders
        JOIN users
        ON orders.user_id = users.id
        ORDER BY orders.id DESC
        """
    ).fetchall()

    connection.close()

    return render_template(
        "owner_orders.html",
        orders=orders
    )


# =====================================================
# UPDATE ORDER STATUS
# =====================================================

@app.route(
    "/update-order-status/<int:order_id>",
    methods=["POST"]
)
def update_order_status(order_id):

    if not session.get("owner_logged_in"):
        return redirect(url_for("owner_login"))

    status = request.form["status"]

    allowed_statuses = [
        "Pending",
        "Preparing",
        "Ready",
        "Completed",
        "Cancelled"
    ]

    if status not in allowed_statuses:
        return redirect(url_for("owner_orders"))

    connection = get_db()

    connection.execute(
        """
        UPDATE orders
        SET status = ?
        WHERE id = ?
        """,
        (status, order_id)
    )

    connection.commit()
    connection.close()

    return redirect(url_for("owner_orders"))


# =====================================================
# RUN
# =====================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )