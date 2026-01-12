from flask import  request, jsonify
from flask_jwt_extended import create_access_token,    jwt_required, get_jwt,get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from .database.dbb import db
import psycopg2
from . import app

@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    email = data['email']
    name = data['name']
    password = generate_password_hash(data['password'])
    role = 'user'   

    conn = db()
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT INTO users (name, email, password, role)
            VALUES (%s, %s, %s, %s)
        """, (name, email, password, role))
        conn.commit()
        return jsonify({'message': 'User registered'}), 201

    except psycopg2.IntegrityError:
        return jsonify({'error': 'User already exists'}), 409

    finally:
        cur.close()
        conn.close()
@app.route("/forgot-password", methods=["POST"])
def forgot_password():
    data = request.get_json()

    email = data.get("email")
    new_password = data.get("newPassword")

    if not email or not new_password:
        return jsonify({"error": "Missing fields"}), 400

    conn = db()
    cursor = conn.cursor()

    # Check if email exists
    cursor.execute(
        "SELECT id FROM users WHERE email = %s",
        (email,)
    )
    user = cursor.fetchone()

    if not user:
        cursor.close()
        conn.close()
        return jsonify({"error": "Email not found"}), 404

    # Hash password
    hashed_password = generate_password_hash(new_password)

    # Update password
    cursor.execute(
        "UPDATE users SET password = %s WHERE email = %s",
        (hashed_password, email)
    )

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "Password updated successfully"}), 200


@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data['email']
    password = data['password']

    conn = db()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, password, role FROM users WHERE email = %s
    """, (email,))
    user = cur.fetchone()

    cur.close()
    conn.close()

    if not user or not check_password_hash(user[1], password):
        return jsonify({'error': 'Invalid credentials'}), 401

    token = create_access_token(
        identity=str(user[0]),
        additional_claims={'role': user[2]}
    )
    return jsonify({'access_token': token})

def admin_required():
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"error": "Admin access required"}), 403

@app.route('/products', methods=['POST'])
@jwt_required()
def add_product():

    admin_check = admin_required()
    if admin_check:
        return admin_check

    data = request.json
    name = data['name']
    price = data['price']
    quantity = data['quantity']
    category = data['category']
    image = data['image']
    if not all([name, price, quantity, category, image]):
        return jsonify({'error': 'All fields required'}), 400


    conn = db()
    cur = conn.cursor()

    try:
        # category
        cur.execute("""
            INSERT INTO categories (name)
            VALUES (%s)
            ON CONFLICT (name) DO NOTHING
        """, (category.lower(),))

        cur.execute("SELECT id FROM categories WHERE name=%s", (category.lower(),))
        category_id = cur.fetchone()[0]

        cur.execute("""
            INSERT INTO products (name, price, quantity, image, category_id)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            name,
            int(price),
            int(quantity),
            image,
            category_id
        ))

        conn.commit()
        return jsonify({'message': 'Product added'}), 201

    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500

    finally:
        cur.close()
        conn.close()


@app.route("/products", methods=["GET"])
@jwt_required()
def get_products():
    claims = get_jwt()

    if claims.get("role") != "admin":
        return jsonify({"error": "Admin access required"}), 403

    conn = db()
    cur = conn.cursor()

    cur.execute("""
        SELECT 
            p.id,
            p.name,
            p.price,
            p.quantity,
            p.image,
            c.name AS category
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        ORDER BY p.id DESC
    """)

    rows = cur.fetchall()
    cur.close()
    conn.close()

    products = []
    for r in rows:
        products.append({
            "id": r[0],
            "name": r[1],
            "price": r[2],
            "quantity": r[3],
            "image": r[4],
            "category": r[5]
        })

    return jsonify(products), 200




@app.route("/products/<int:product_id>", methods=["GET"])
@jwt_required()
def get_product(product_id):
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"error": "Admin access required"}), 403

    conn = db()
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            p.id,
            p.name,
            p.price,
            p.quantity,
            p.image,
            c.name AS category
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE p.id = %s
    """, (product_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return jsonify({"error": "Product not found"}), 404

    product = {
        "id": row[0],
        "name": row[1],
        "price": row[2],
        "quantity": row[3],
        "image": row[4],
        "category": row[5]
    }

    return jsonify(product), 200

@app.route("/products/<int:product_id>", methods=["PUT"])
@jwt_required()
def update_product(product_id):
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"error": "Admin access required"}), 403

    data = request.get_json()
    name = data.get("name")
    price = data.get("price")
    quantity = data.get("quantity")
    category_name = data.get("category")

    conn = db()
    cur = conn.cursor()

    cur.execute("SELECT id FROM categories WHERE LOWER(name) = LOWER(%s)", (category_name,))
    cat_row = cur.fetchone()
    if not cat_row:
        cur.close()
        conn.close()
        return jsonify({"error": "Category not found"}), 400
    category_id = cat_row[0]

    cur.execute("""
        UPDATE products
        SET name=%s, price=%s, quantity=%s, category_id=%s
        WHERE id=%s
    """, (name, price, quantity, category_id, product_id))
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"message": "Product updated successfully"}), 200


@app.route("/products/<int:product_id>", methods=["DELETE"])
@jwt_required()
def delete_product(product_id):
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"error": "Admin access required"}), 403

    conn = db()
    cur = conn.cursor()
    cur.execute("DELETE FROM products WHERE id = %s", (product_id,))
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"message": "Product deleted successfully"}), 200

@app.route("/categories", methods=["GET"])
def get_categories():
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM categories")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify([
        {"id": r[0], "name": r[1]} for r in rows
    ])


@app.route("/productspage", methods=["GET"])
def getuser_products():
    category_id = request.args.get("category_id")

    conn = db()
    cur = conn.cursor()

    if category_id:
        cur.execute("""
            SELECT id, name, price, image
            FROM products
            WHERE category_id = %s
            AND quantity > 0
        """, (category_id,))
    else:
        cur.execute("""
            SELECT id, name, price, image
            FROM products  WHERE quantity > 0 
        """)

    rows = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify([
        {
            "id": r[0],
            "name": r[1],
            "price": r[2],
            "image": r[3]
        } for r in rows
    ])


@app.route("/profile", methods=["GET"])
@jwt_required()
def get_profile():
    user_id = get_jwt_identity()
    conn = db()
    cur = conn.cursor()

    cur.execute("""
        SELECT name, email, role
        FROM users
        WHERE id = %s
    """, (user_id,))

    user = cur.fetchone()
    cur.close()
    conn.close()

    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "name": user[0],
        "email": user[1],
        "role": user[2]
    }), 200
@app.route("/cart/add", methods=["POST"])
@jwt_required()
def add_to_cart():
    user_id = get_jwt_identity()
    data = request.get_json()

    product_id = data.get("product_id")
    qty = data.get("quantity", 1)

    if not product_id:
        return jsonify({"error": "Product ID required"}), 400

    conn = db()
    cur = conn.cursor()

    # Check available stock
    cur.execute("SELECT quantity FROM products WHERE id = %s", (product_id,))
    product = cur.fetchone()

    if not product or product[0] < qty:
        cur.close()
        conn.close()
        return jsonify({"error": "Insufficient stock"}), 400

    # Check if already in cart
    cur.execute("""
        SELECT id FROM cart
        WHERE user_id = %s AND product_id = %s
    """, (user_id, product_id))
    existing = cur.fetchone()

    if existing:
        cur.execute("""
            UPDATE cart
            SET quantity = quantity + %s
            WHERE id = %s
        """, (qty, existing[0]))
    else:
        cur.execute("""
            INSERT INTO cart (user_id, product_id, quantity)
            VALUES (%s, %s, %s)
        """, (user_id, product_id, qty))

    # Reduce product stock
    cur.execute("""
        UPDATE products
        SET quantity = quantity - %s
        WHERE id = %s
    """, (qty, product_id))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"message": "Product added to cart"}), 200

@app.route("/cart", methods=["GET"])
@jwt_required()
def get_cart():
    user_id = get_jwt_identity()

    conn = db()
    cur = conn.cursor()

    cur.execute("""
        SELECT 
            c.id,
            p.id,
            p.name,
            p.price,
            p.image,
            c.quantity,
            (p.price * c.quantity)
        FROM cart c
        JOIN products p ON c.product_id = p.id
        WHERE c.user_id = %s
    """, (user_id,))

    rows = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify([
        {
            "cart_id": r[0],
            "product_id": r[1],
            "name": r[2],
            "price": r[3],
            "image": r[4],
            "quantity": r[5],
            "total_price": r[6]
        } for r in rows
    ])

@app.route("/cart/update", methods=["PUT"])
@jwt_required()
def update_cart():
    data = request.get_json()
    cart_id = data.get("cart_id")
    new_qty = data.get("quantity")

    conn = db()
    cur = conn.cursor()

    cur.execute("""
        SELECT c.product_id, c.quantity, p.quantity
        FROM cart c
        JOIN products p ON c.product_id = p.id
        WHERE c.id = %s
    """, (cart_id,))

    row = cur.fetchone()
    if not row:
        return jsonify({"error": "Cart item not found"}), 404

    product_id, old_qty, stock = row
    diff = new_qty - old_qty

    if diff > stock:
        return jsonify({"error": "Not enough stock"}), 400

    # Update cart
    cur.execute("""
        UPDATE cart SET quantity = %s WHERE id = %s
    """, (new_qty, cart_id))

    # Adjust product stock
    cur.execute("""
        UPDATE products
        SET quantity = quantity - %s
        WHERE id = %s
    """, (diff, product_id))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"message": "Cart updated"}), 200

@app.route("/cart/remove/<int:cart_id>", methods=["DELETE"])
@jwt_required()
def remove_cart_item(cart_id):
    user_id = get_jwt_identity()

    conn = db()
    cur = conn.cursor()

    # Get quantity to restore stock
    cur.execute("""
        SELECT product_id, quantity
        FROM cart
        WHERE id = %s AND user_id = %s
    """, (cart_id, user_id))
    item = cur.fetchone()

    if not item:
        return jsonify({"error": "Item not found"}), 404

    product_id, qty = item

    cur.execute("DELETE FROM cart WHERE id = %s", (cart_id,))
    cur.execute("""
        UPDATE products
        SET quantity = quantity + %s
        WHERE id = %s
    """, (qty, product_id))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"message": "Item removed"}), 200
@app.route("/order/place", methods=["POST"])
@jwt_required()
def place_order():
    user_id = get_jwt_identity()
    DELIVERY_CHARGES = 300

    conn = db()
    cur = conn.cursor()

    # 1️⃣ Get cart items with price
    cur.execute("""
        SELECT c.product_id, c.quantity, p.price
        FROM cart c
        JOIN products p ON c.product_id = p.id
        WHERE c.user_id = %s
    """, (user_id,))

    cart_items = cur.fetchall()

    if not cart_items:
        cur.close()
        conn.close()
        return jsonify({"error": "Cart is empty"}), 400

    # 2️⃣ Calculate subtotal
    subtotal = sum(item[1] * item[2] for item in cart_items)
    total_amount = subtotal + DELIVERY_CHARGES

    # 3️⃣ Create order
    cur.execute("""
        INSERT INTO orders (user_id, total_amount, status)
        VALUES (%s, %s, 'pending')
        RETURNING id
    """, (user_id, total_amount))

    order_id = cur.fetchone()[0]

    # 4️⃣ Insert into order_items
    for product_id, quantity, price in cart_items:
        cur.execute("""
            INSERT INTO order_items (order_id, product_id, quantity, price)
            VALUES (%s, %s, %s, %s)
        """, (order_id, product_id, quantity, price))

    # 5️⃣ Clear cart
    cur.execute("DELETE FROM cart WHERE user_id = %s", (user_id,))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({
        "message": "Order placed successfully",
        "order_id": order_id,
        "subtotal": subtotal,
        "delivery_charges": DELIVERY_CHARGES,
        "total_amount": total_amount,
        "payment_method": "Cash on Delivery"
    }), 200


@app.route("/orders", methods=["GET"])
@jwt_required()
def get_orders():
    user_id = get_jwt_identity()

    conn = db()
    cur = conn.cursor()

    # Check if user is admin
    cur.execute("SELECT role FROM users WHERE id = %s", (user_id,))
    role = cur.fetchone()[0]

    if role == "admin":
        # Admin sees all orders
        cur.execute("""
            SELECT o.id, o.user_id, u.name, o.total_amount, o.status, o.created_at,
                   oi.product_id, p.name, oi.quantity, oi.price
            FROM orders o
            JOIN users u ON o.user_id = u.id
            JOIN order_items oi ON oi.order_id = o.id
            JOIN products p ON oi.product_id = p.id
            ORDER BY o.created_at DESC
        """)
    else:
        # User sees only their orders
        cur.execute("""
            SELECT o.id, o.user_id, u.name, o.total_amount, o.status, o.created_at,
                   oi.product_id, p.name, oi.quantity, oi.price
            FROM orders o
            JOIN users u ON o.user_id = u.id
            JOIN order_items oi ON oi.order_id = o.id
            JOIN products p ON oi.product_id = p.id
            WHERE o.user_id = %s
            ORDER BY o.created_at DESC
        """, (user_id,))

    rows = cur.fetchall()
    conn.commit()
    cur.close()
    conn.close()

    # Convert to structured JSON
    orders = {}
    for r in rows:
        order_id = r[0]
        if order_id not in orders:
            orders[order_id] = {
                "id": r[0],
                "user_id": r[1],
                "user_name": r[2],
                "total_amount": r[3],
                "status": r[4],
                "created_at": r[5].strftime("%Y-%m-%d %H:%M"),
                "items": []
            }
        orders[order_id]["items"].append({
            "product_id": r[6],
            "product_name": r[7],
            "quantity": r[8],
            "price": r[9]
        })

    return jsonify({
        "role": role,
        "orders": list(orders.values())
    }), 200


@app.route("/orders/update-status", methods=["PUT"])
@jwt_required()
def update_order_status():
    user_id = get_jwt_identity()
    data = request.get_json()
    order_id = data.get("order_id")
    status = data.get("status")

    if not order_id or not status:
        return jsonify({"error": "Missing fields"}), 400

    allowed_status = ['pending', 'packed', 'shipped', 'delivered', 'cancelled']

    if status not in allowed_status:
        return jsonify({"error": "Invalid status"}), 400

    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT role FROM users WHERE id = %s", (user_id,))
    role = cur.fetchone()[0]

    if role != "admin":
        return jsonify({"error": "Unauthorized"}), 403

    cur.execute("UPDATE orders SET status=%s WHERE id=%s", (status, order_id))
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"message": f"Order status updated to '{status}'"}), 200
