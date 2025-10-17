from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = "secretkey"

# -------------------- DATABASE SETUP --------------------
db_path = os.path.join(os.path.dirname(__file__), "wagas.db")
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# -------------------- MODEL --------------------
class User(db.Model):
    __tablename__ = "User"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(100))
    password = db.Column(db.String(100), nullable=False)

# -------------------- LOGIN --------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session["user"] = user.username
            flash("Login successful!", "success")
            return redirect(url_for("index"))
        else:
            flash("Invalid username or password.", "error")
            return redirect(url_for("login"))

    return render_template("login.html")

# -------------------- SIGNUP --------------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        if username and password:
            # Check if user exists
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                flash("Username already exists. Please login.", "error")
                return redirect(url_for("login"))
            
            # Create new user
            new_user = User(username=username, email=email, password=password)
            db.session.add(new_user)
            db.session.commit()
            flash("Signup successful! Please login.", "success")
            return redirect(url_for("login"))
        else:
            flash("Please fill all required fields.", "error")
            return redirect(url_for("signup"))

    return render_template("signup.html")

# -------------------- HOME --------------------
@app.route("/")
def index():
    if "user" not in session:
        return redirect(url_for("login"))
    username = session["user"]
    return render_template("index.html", name=username)

# -------------------- CHECKOUT --------------------
@app.route("/checkout")
def checkout():
    if "user" not in session:
        return redirect(url_for("login"))
    total = request.args.get("total", 0)
    return render_template("checkout.html", total=total)

# -------------------- LOGOUT --------------------
@app.route("/logout")
def logout():
    session.pop("user", None)
    session.clear()  # <-- This clears all session data, including flash messages
    return redirect(url_for("login"))


# -------------------- MAIN --------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # auto-create tables if not exist
    app.run(debug=True, port=5001)
