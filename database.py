import sqlite3
import os

DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cafe.db")

MENU = [
("Cappuccino","Velvety espresso, steamed milk and a soft foam cap.",120,"☕","coffee.svg"),
("Espresso","Rich, bold espresso with a smooth aromatic finish.",100,"☕","coffee.svg"),
("Cafe Latte","Silky steamed milk balanced with fresh espresso.",130,"🥛","coffee.svg"),
("Americano","Espresso finished with hot water for a clean cup.",110,"☕","coffee.svg"),
("Cafe Mocha","Chocolate, espresso and steamed milk in one cozy cup.",150,"🍫","coffee.svg"),
("Cold Coffee","Chilled creamy coffee blended until perfectly frothy.",140,"🧋","coffee.svg"),
("Masala Tea","Indian spiced tea brewed warm and fragrant.",80,"🍵","tea.svg"),
("Green Tea","Light, refreshing green tea for a calm break.",90,"🍵","tea.svg"),
("Fresh Lime Soda","Zesty lime with a sparkling, refreshing finish.",100,"🍋","tea.svg"),
("Fresh Mojito","Mint, lime and fizz for a bright café refresher.",130,"🥤","tea.svg"),
("Chocolate Milkshake","Creamy chocolate shake topped for a sweet treat.",160,"🥤","dessert.svg"),
("Strawberry Milkshake","Cool strawberry goodness blended smooth and creamy.",160,"🍓","dessert.svg"),
("Classic Burger","A hearty veggie patty layered with fresh café toppings.",180,"🍔","burger.svg"),
("Cheese Burger","Classic burger with a generous melted cheese layer.",200,"🍔","burger.svg"),
("Veg Pizza","Crispy crust, vegetables and herbs with café-style cheese.",200,"🍕","burger.svg"),
("Cheese Pizza","Cheesy comfort on a golden, freshly baked crust.",220,"🍕","burger.svg"),
("Club Sandwich","Layered toasted sandwich packed with fresh fillings.",160,"🥪","sandwich.svg"),
("Veg Grilled Sandwich","Golden grilled bread with a savory vegetable filling.",150,"🥪","sandwich.svg"),
("French Fries","Crispy golden fries with the perfect café crunch.",120,"🍟","sandwich.svg"),
("White Sauce Pasta","Creamy pasta with herbs and a silky white sauce.",190,"🍝","pasta.svg"),
("Chocolate Cake","Moist chocolate cake for an indulgent finish.",150,"🍰","dessert.svg"),
("Brownie","Fudgy chocolate brownie, rich and comforting.",130,"🍫","dessert.svg"),
("Cheesecake","Creamy cheesecake with a delicate café-style finish.",180,"🍰","dessert.svg"),
("Ice Cream","Cool, creamy sweetness to finish your café visit.",100,"🍨","dessert.svg")
]

def create_database():
    db = sqlite3.connect(DATABASE)
    cur = db.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL, password TEXT NOT NULL)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS menu(
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
        description TEXT NOT NULL, price REAL NOT NULL, emoji TEXT NOT NULL,
        image TEXT DEFAULT 'coffee.svg')""")
    cur.execute("PRAGMA table_info(menu)")
    cols = {r[1] for r in cur.fetchall()}
    if "image" not in cols:
        cur.execute("ALTER TABLE menu ADD COLUMN image TEXT DEFAULT 'coffee.svg'")
    cur.execute("""CREATE TABLE IF NOT EXISTS cart(
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
        menu_id INTEGER NOT NULL, quantity INTEGER NOT NULL DEFAULT 1,
        FOREIGN KEY(user_id) REFERENCES users(id), FOREIGN KEY(menu_id) REFERENCES menu(id),
        UNIQUE(user_id, menu_id))""")
    cur.execute("""CREATE TABLE IF NOT EXISTS orders(
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
        total REAL NOT NULL, status TEXT NOT NULL DEFAULT 'Pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        customer_name TEXT DEFAULT '', phone TEXT DEFAULT '',
        order_type TEXT DEFAULT 'Pickup', notes TEXT DEFAULT '',
        FOREIGN KEY(user_id) REFERENCES users(id))""")
    cur.execute("PRAGMA table_info(orders)")
    order_cols = {r[1] for r in cur.fetchall()}
    for col, typ in [("customer_name","TEXT DEFAULT ''"),("phone","TEXT DEFAULT ''"),("order_type","TEXT DEFAULT 'Pickup'"),("notes","TEXT DEFAULT ''")]:
        if col not in order_cols:
            cur.execute(f"ALTER TABLE orders ADD COLUMN {col} {typ}")
    cur.execute("""CREATE TABLE IF NOT EXISTS order_items(
        id INTEGER PRIMARY KEY AUTOINCREMENT, order_id INTEGER NOT NULL,
        menu_id INTEGER NOT NULL, quantity INTEGER NOT NULL, price REAL NOT NULL,
        FOREIGN KEY(order_id) REFERENCES orders(id), FOREIGN KEY(menu_id) REFERENCES menu(id))""")

    existing = {r[0] for r in cur.execute("SELECT name FROM menu").fetchall()}
    for item in MENU:
        if item[0] not in existing:
            cur.execute("INSERT INTO menu(name,description,price,emoji,image) VALUES(?,?,?,?,?)", item)
        else:
            cur.execute("UPDATE menu SET description=?,price=?,emoji=?,image=? WHERE name=?", (item[1],item[2],item[3],item[4],item[0]))
    db.commit(); db.close()
    print("Database ready — existing users/orders preserved and menu upgraded.")

if __name__ == "__main__":
    create_database()
