import sqlite3

DATABASE = "cafe.db"


def create_database():

    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    # USERS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # MENU
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS menu (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            price REAL NOT NULL,
            emoji TEXT NOT NULL
        )
    """)

    # CART
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cart (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            menu_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (menu_id) REFERENCES menu(id),
            UNIQUE(user_id, menu_id)
        )
    """)

    # ORDERS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            total REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # ORDER ITEMS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            menu_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(id),
            FOREIGN KEY (menu_id) REFERENCES menu(id)
        )
    """)

    # DEFAULT MENU
    cursor.execute("SELECT COUNT(*) FROM menu")
    count = cursor.fetchone()[0]

    if count == 0:

        items = [

            # COFFEE
            (
                "Cappuccino",
                "Rich espresso with creamy milk foam.",
                120,
                "☕"
            ),
            (
                "Espresso",
                "Strong and aromatic freshly brewed coffee.",
                100,
                "☕"
            ),
            (
                "Cafe Latte",
                "Smooth espresso blended with steamed milk.",
                130,
                "🥛"
            ),
            (
                "Americano",
                "Classic espresso with hot water.",
                110,
                "☕"
            ),
            (
                "Cafe Mocha",
                "Chocolate-flavoured coffee with creamy milk.",
                150,
                "🍫"
            ),
            (
                "Cold Coffee",
                "Chilled creamy coffee served cold.",
                140,
                "🧋"
            ),

            # TEA & DRINKS
            (
                "Masala Tea",
                "Hot tea prepared with aromatic spices.",
                80,
                "🍵"
            ),
            (
                "Green Tea",
                "Light and refreshing green tea.",
                90,
                "🍵"
            ),
            (
                "Fresh Lime Soda",
                "Refreshing lime drink with a fizzy twist.",
                100,
                "🍋"
            ),
            (
                "Fresh Mojito",
                "Refreshing mint and lime drink.",
                130,
                "🥤"
            ),
            (
                "Chocolate Milkshake",
                "Thick and creamy chocolate milkshake.",
                160,
                "🥤"
            ),
            (
                "Strawberry Milkshake",
                "Creamy milkshake made with strawberry flavour.",
                160,
                "🍓"
            ),

            # FAST FOOD
            (
                "Classic Burger",
                "Juicy burger with fresh vegetables.",
                180,
                "🍔"
            ),
            (
                "Cheese Burger",
                "Delicious burger topped with melted cheese.",
                200,
                "🍔"
            ),
            (
                "Veg Pizza",
                "Pizza topped with fresh vegetables and cheese.",
                200,
                "🍕"
            ),
            (
                "Cheese Pizza",
                "Hot pizza loaded with delicious cheese.",
                220,
                "🍕"
            ),
            (
                "Club Sandwich",
                "Fresh sandwich with crispy vegetables.",
                160,
                "🥪"
            ),
            (
                "Veg Grilled Sandwich",
                "Grilled sandwich filled with fresh vegetables.",
                150,
                "🥪"
            ),
            (
                "French Fries",
                "Crispy golden fries served hot.",
                120,
                "🍟"
            ),
            (
                "White Sauce Pasta",
                "Creamy pasta prepared with rich white sauce.",
                190,
                "🍝"
            ),

            # DESSERTS
            (
                "Chocolate Cake",
                "Soft and delicious chocolate cake.",
                150,
                "🍰"
            ),
            (
                "Brownie",
                "Warm and soft chocolate brownie.",
                130,
                "🍫"
            ),
            (
                "Cheesecake",
                "Creamy cheesecake with a delicious base.",
                180,
                "🍰"
            ),
            (
                "Ice Cream",
                "Creamy and refreshing ice cream.",
                100,
                "🍨"
            )
        ]

        cursor.executemany("""
            INSERT INTO menu
            (name, description, price, emoji)
            VALUES (?, ?, ?, ?)
        """, items)

    connection.commit()
    connection.close()

    print("Database ready!")


if __name__ == "__main__":
    create_database()