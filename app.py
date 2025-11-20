from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = "secretkey"

# -------------------- DATABASE SETUP --------------------
db_path = os.path.join(os.path.dirname(__file__), "wagas.db")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# -------------------- MODELS --------------------
class User(db.Model):
    __tablename__ = "User"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)


class Order(db.Model):
    __tablename__ = "orders"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("User.id"))
    name = db.Column(db.String(100))
    address = db.Column(db.String(200))
    contact = db.Column(db.String(50))
    payment_method = db.Column(db.String(50))
    total = db.Column(db.Float)
    status = db.Column(db.String(50), default="Pending")

    user = db.relationship("User", backref=db.backref("orders", lazy=True))


# -------------------- LOGIN --------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username_or_email = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter(
            ((User.username == username_or_email) | (User.email == username_or_email))
            & (User.password == password)
        ).first()

        if user:
            session["user"] = user.username
            session["user_id"] = user.id

            flash("Login successful!", "success")

            # ✅ If admin logs in
            if user.username.lower() == "admin":
                return redirect(url_for("admin_orders"))
            else:
                return redirect(url_for("index"))
        else:
            flash("Invalid username/email or password.", "error")
            return redirect(url_for("login"))

    return render_template("login.html")


# -------------------- SIGNUP --------------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        if username and email and password:
            existing_user = User.query.filter(
                (User.username == username) | (User.email == email)
            ).first()

            if existing_user:
                flash("Username or Email already exists. Please login.", "error")
                return redirect(url_for("login"))

            new_user = User(username=username, email=email, password=password)
            db.session.add(new_user)
            db.session.commit()
            flash("Signup successful! Please login.", "success")
            return redirect(url_for("login"))
        else:
            flash("Please fill out all fields.", "error")
            return redirect(url_for("signup"))

    return render_template("signup.html")


# -------------------- HOME --------------------
@app.route("/")
def index():
    if "user" not in session:
        return redirect(url_for("login"))
    username = session["user"]
    return render_template("index.html", name=username)


# -------------------- MENU --------------------
@app.route("/menu")
def menu():
    if "user" not in session:
        return redirect(url_for("login"))
    username = session["user"]
    return render_template("menu.html", name=username)


# -------------------- ABOUT US --------------------
@app.route("/aboutus")
def aboutus():
    if "user" not in session:
        return redirect(url_for("login"))
    username = session["user"]
    return render_template("aboutus.html", name=username)


# -------------------- CHECKOUT --------------------
# -------------------- CHECKOUT PAGE --------------------
@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    if "user" not in session:
        flash("Please login first.", "warning")
        return redirect(url_for("login"))

    cart = session.get("cart", [])
    subtotal = sum(item["price"] for item in cart)
    delivery_fee = 49
    total = subtotal + delivery_fee

    if request.method == "POST":
        name = request.form.get("name")
        address = request.form.get("address")
        contact = request.form.get("contact")
        payment_method = request.form.get("payment_method")

        # ✅ Save to database
        if "user_id" in session:
            new_order = Order(
                user_id=session["user_id"],
                name=name,
                address=address,
                contact=contact,
                payment_method=payment_method,
                total=total,
                status="Pending"
            )
            db.session.add(new_order)
            db.session.commit()

            # 🧹 Clear cart after checkout
            session.pop("cart", None)

        flash("✅ Order placed successfully!", "success")
        return render_template(
            "thankyou.html",
            name=name,
            address=address,
            contact=contact,
            payment_method=payment_method,
            total=total
        )

    return render_template("checkout.html", total=total)


# -------------------- CANCEL ORDER --------------------
@app.route("/cancel_order")
def cancel_order():
    flash("❌ Order canceled. You can continue shopping.", "info")
    return redirect(url_for("menu"))



# -------------------- USERS PAGE --------------------
@app.route("/users")
def users():
    if "user" not in session:
        return redirect(url_for("login"))

    all_users = User.query.all()
    return render_template("users.html", users=all_users)


# -------------------- CONTACT --------------------
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        print(f"New message from {name} ({email}): {message}")
        return render_template('contact.html', success=True)
    return render_template('contact.html')


# -------------------- LOGOUT --------------------
@app.route("/logout")
def logout():
    session.pop("user", None)
    session.pop("user_id", None)
    flash("Logged out successfully!", "info")
    return redirect(url_for("login"))

# -------------------- ADD TO CART --------------------
@app.route("/add_to_cart", methods=["POST"])
def add_to_cart():
    if "user" not in session:
        return redirect(url_for("login"))

    item_name = request.form.get("name")
    item_price = float(request.form.get("price", 0))

    if "cart" not in session:
        session["cart"] = []

    cart = session["cart"]

    # ✅ Assign a unique ID for each item (based on length + 1)
    item_id = len(cart) + 1
    cart.append({"id": item_id, "name": item_name, "price": item_price})

    session["cart"] = cart
    flash(f"🛒 {item_name} added to cart!", "success")
    return redirect(url_for("menu"))


# -------------------- VIEW CART --------------------
@app.route("/cart")
def cart():
    if "user" not in session:
        return redirect(url_for("login"))

    cart = session.get("cart", [])
    subtotal = sum(item["price"] for item in cart)
    delivery_fee = 49
    total = subtotal + delivery_fee

    return render_template("cart.html", cart=cart, subtotal=subtotal, delivery_fee=delivery_fee, total=total)

@app.route("/remove_from_cart/<int:item_id>")
def remove_from_cart(item_id):
    if "cart" in session:
        session["cart"] = [item for item in session["cart"] if item["id"] != item_id]
        session.modified = True
        flash("🗑️ Item removed from cart.", "info")

    return redirect(url_for("cart"))


# -------------------- CLEAR CART --------------------
@app.route("/clear_cart")
def clear_cart():
    session.pop("cart", None)
    flash("🧹 Cart cleared.", "info")
    return redirect(url_for("menu"))



# -------------------- ADMIN ORDERS --------------------
# -------------------- ADMIN ORDERS --------------------
@app.route('/admin/orders')
def admin_orders():
    if "user" not in session or session["user"].lower() != "admin":
        flash("Access denied. Admins only.", "error")
        return redirect(url_for("login"))

    # ✅ Group orders by status for separate tabs
    pending_orders = db.session.query(
        Order.id, User.username, Order.name, Order.address, Order.contact,
        Order.payment_method, Order.total, Order.status
    ).join(User, Order.user_id == User.id).filter(Order.status == "Pending").all()

    approved_orders = db.session.query(
        Order.id, User.username, Order.name, Order.address, Order.contact,
        Order.payment_method, Order.total, Order.status
    ).join(User, Order.user_id == User.id).filter(Order.status == "Approved").all()

    rejected_orders = db.session.query(
        Order.id, User.username, Order.name, Order.address, Order.contact,
        Order.payment_method, Order.total, Order.status
    ).join(User, Order.user_id == User.id).filter(Order.status == "Rejected").all()

    return render_template(
        "admin_orders.html",
        pending_orders=pending_orders,
        approved_orders=approved_orders,
        rejected_orders=rejected_orders
    )


# -------------------- UPDATE ORDER STATUS --------------------
@app.route('/admin/update_order/<int:order_id>/<string:status>')
def update_order(order_id, status):
    if "user" not in session or session["user"].lower() != "admin":
        flash("Access denied.", "error")
        return redirect(url_for("login"))

    order = Order.query.get(order_id)
    if order:
        order.status = status
        db.session.commit()
        flash(f"✅ Order #{order_id} marked as {status}.", "success")
    else:
        flash("Order not found.", "error")

    return redirect(url_for("admin_orders"))


# -------------------- DELETE ORDER --------------------
@app.route('/admin/delete_order/<int:order_id>')
def delete_order(order_id):
    if "user" not in session or session["user"].lower() != "admin":
        flash("Access denied.", "error")
        return redirect(url_for("login"))

    order = Order.query.get(order_id)
    if order:
        db.session.delete(order)
        db.session.commit()
        flash(f"🗑️ Order #{order_id} deleted.", "info")
    else:
        flash("Order not found.", "error")

    return redirect(url_for("admin_orders"))


# -------------------- MAIN --------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5001)
