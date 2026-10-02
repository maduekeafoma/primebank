"""PrimeBank Flask application.

This application provides a simple online banking experience with
user authentication, account creation, profile image uploads,
balance management, deposits, withdrawals, and transfers.
"""

# Import Libraries
import os
import random
from datetime import datetime, timezone

from flask import (
    Flask,
    redirect,
    url_for,
    request,
    render_template,
    flash
)

from flask_login import (
    LoginManager,
    UserMixin,
    current_user,
    logout_user,
    login_user,
    login_required
)

from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)
from werkzeug.utils import secure_filename

from dotenv import load_dotenv


load_dotenv()

# Create Directories
os.makedirs("instance/", exist_ok=True)
os.makedirs("static/upload", exist_ok=True)

# Default Variables
ALLOWED_FORMATS = ["jpg", "jpeg", "png"]
MAX_UPLOAD_BYTES = 2 * 1024 * 1024  # 2 MB


def generate_random_num():
    """function to generate a list - 5 num - of further adjustable nunber from a prelist see from os"""
    seed_list = os.getenv("SEED_LIST", "1,2,3,4,5,6,7,8,9").split(",")
    number_list =[random.choice(seed_list) for _ in range(7)]
    number_list =[number_list[i] for i in range(5)]
    number_list_int=[]
    for i in  number_list :
        """use the seed to create random values"""
        i = int(i)
        num = str(random.randint(0, i))
        number_list_int.append(i)
    return  number_list_int
        
def generate_random_number():
    """Function to generate 3 random numbers"""
    num_list = []

    for i in range(3):
        number = random.randint(1, 200)
        num_list.append(number)

    return num_list

print(generate_random_number())

def _read_initial_balance():
    """Read the starting balance from the environment.

    Returns:
        float: A numeric starting balance, or 0.0 if the value is missing
        or invalid.
    """
    raw = os.getenv("INITIAL_BALANCE", "0")
    try:
        return float(raw)
    except (TypeError, ValueError):
        return 0.0


INITIAL_BALANCE = _read_initial_balance()

# Flask Configuration
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("SQLALCHEMY_DATABASE_URI")
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["UPLOAD_FOLDER"] = os.getenv("UPLOAD_FOLDER", "static/upload")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_BYTES

# DB, Login and CSRF Configurations
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Please Login To Access The Page."
login_manager.login_message_category = "error"
csrf = CSRFProtect(app)


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(50), unique=True, nullable=False)
    username = db.Column(db.String(20), unique=True, nullable=False)
    firstname = db.Column(db.String(25), nullable=False)
    lastname = db.Column(db.String(25), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    image = db.Column(db.String(255), nullable=True)
    balance = db.Column(db.Float, nullable=False, default=INITIAL_BALANCE)
    account_number = db.Column(db.String(10), nullable=False, unique=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )


# Helper Functions
def hash_password(raw_password):
    """Hash a plain text password using Werkzeug security helpers."""
    return generate_password_hash(raw_password)


def verify_password(password_hash, raw_password):
    """Check whether the entered password matches the stored hash."""
    return check_password_hash(password_hash, raw_password)


def generate_account_number():
    """Generate a unique 10-character bank account number for a user."""
    prefix = "002"
    while True:
        num = [str(random.randint(0, 9)) for _ in range(7)]
        account = prefix + "".join(num)
        if not User.query.filter_by(account_number=account).first():
            return account


def is_allowed_image_format(image_filename):
    """Return True when the uploaded file has an approved image extension."""
    if not image_filename.strip():
        return False
    ext = image_filename.rsplit(".", 1)[-1].lower().strip()
    if ext not in ALLOWED_FORMATS:
        return False
    return True


def parse_amount(raw_amount):
    """Convert an incoming form value to a rounded numeric amount.

    Returns:
        float | None: A rounded amount, or None if the input is not valid.
    """
    try:
        return round(float(raw_amount), 2)
    except (TypeError, ValueError):
        return None


def generate_random():
    """Generate a random 4-digit number."""
    num_list = []
    for _ in range(4):
        num_list.append(str(random.randint(0, 9)))
    num = int("".join(num_list))
    return num


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


@app.context_processor
def inject_globals():
    return {"current_year": datetime.now(timezone.utc).year}


with app.app_context():
    db.create_all()


@app.route("/")
@app.route("/bank")
@login_required
def bank():
    """Display the authenticated user's bank dashboard."""
    return render_template("bank.html", user=current_user)

# @app.route("/about")
# def about():
#     return render_template("about.html")

@app.route("/logout")
@login_required
def logout():
    """Log out the current user and redirect them to the login page."""
    logout_user()
    flash("User Logged Out Successfully", "success")
    return redirect(url_for("login"))


@app.route("/about")
def about():
    """Display the about page for the application."""
    return render_template("about.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Authenticate a user using email or username and password."""
    if current_user.is_authenticated:
        return redirect(url_for("bank"))
    if request.method == "POST":
        email_or_username = request.form.get(
            "email_or_username", ""
        ).strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter(
            (User.email == email_or_username) | (User.username == email_or_username)
        ).first()

        if user and verify_password(user.password_hash, password):
            login_user(user)
            flash(f"Welcome back, {user.firstname.title()}!", "success")
            return redirect(url_for("bank"))
        flash("Incorrect Username/Email or Password.", "error")
        return render_template("login.html")
    return render_template("login.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    """Create a new user account and save it to the database."""
    if current_user.is_authenticated:
        return redirect(url_for("bank"))
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        firstname = request.form.get("firstname", "").strip().lower()
        lastname = request.form.get("lastname", "").strip().lower()
        phone = request.form.get("phone", "").strip()

        # NOTE: this used to be "and" between the checks, which only
        # flagged an error if EVERY field was missing at once. It's
        # "or" so a single missing field is caught.
        if not username or not password or not email:
            flash("Username, Email and Password Required.", "error")
            return render_template("signup.html")
        if not firstname or not lastname:
            flash("Firstname and Lastname Required.", "error")
            return render_template("signup.html")
        if len(password) < 8:
            flash("Password Must Be At Least 8 Characters.", "error")
            return render_template("signup.html")
        if password != confirm_password:
            flash("Passwords Do Not Match.", "error")
            return render_template("signup.html")

        email_exists = User.query.filter_by(email=email).first()
        if email_exists:
            flash("Email Exists, Use Another Email.", "error")
            return render_template("signup.html")

        username_exists = User.query.filter_by(username=username).first()
        if username_exists:
            flash("Username Already Taken.", "error")
            return render_template("signup.html")

        image = request.files.get("image_file")
        if image and image.filename and is_allowed_image_format(image.filename):
            ext = image.filename.rsplit(".", 1)[-1].lower().strip()
            image_file = secure_filename(f"{username}.{ext}")
            image.save(os.path.join(app.config["UPLOAD_FOLDER"], image_file))
        else:
            image_file = ""

        user = User(
            firstname=firstname,
            lastname=lastname,
            email=email,
            username=username,
            phone=phone,
            password_hash=hash_password(password),  # was "passhword_hash": silently dropped every password
            image=image_file,
            account_number=generate_account_number()
        )

        db.session.add(user)
        db.session.commit()

        flash("User Account Created Successfully", "success")
        return redirect(url_for("login"))
    return render_template("signup.html")


@app.route("/deposit", methods=["POST"])
@login_required
def deposit():
    """Add money to the logged-in user's current balance."""
    amount = parse_amount(request.form.get("amount"))
    if amount is None or amount <= 0:
        flash("Invalid Amount", "error")
    else:
        current_user.balance += amount
        db.session.commit()
        flash(f"₦{amount:,.2f} has been deposited.", "success")
    return redirect(url_for("bank"))


@app.route("/withdraw", methods=["POST"])
@login_required
def withdraw():
    """Withdraw money from the logged-in user's account if funds allow."""
    amount = parse_amount(request.form.get("amount"))
    if amount is None or amount <= 0:
        flash("Invalid Amount", "error")
    elif amount > current_user.balance:
        flash("Insufficient Funds", "error")
    else:
        current_user.balance -= amount
        db.session.commit()
        flash(f"₦{amount:,.2f} has been withdrawn.", "success")
    return redirect(url_for("bank"))


@app.route("/transfer", methods=["POST"])
@login_required
def transfer():
    """Transfer funds from one account to another valid account."""
    amount = parse_amount(request.form.get("amount"))
    receiver_account = request.form.get("receiver_account", "").strip()

    receiver = User.query.filter_by(account_number=receiver_account).first()

    if amount is None:
        flash("Invalid Amount", "error")
    elif not receiver:
        flash("The Receiver Account Number Does Not Exist.", "error")
    elif receiver.id == current_user.id:
        flash("Oga, don't transfer to yourself", "error")
    elif amount <= 0:
        flash("Invalid Amount", "error")
    elif amount > current_user.balance:
        flash("Insufficient Funds", "error")
    else:
        current_user.balance -= amount
        receiver.balance += amount
        db.session.commit()
        flash(f"₦{amount:,.2f} has been transferred to {receiver.firstname.title()}.", "success")
    return redirect(url_for("bank"))


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
