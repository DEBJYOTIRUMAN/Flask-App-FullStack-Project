from flask import Flask, render_template, request, redirect, session, send_file
from flask_sqlalchemy import SQLAlchemy
import bcrypt
import cloudinary
from cloudinary.uploader import upload
from tempfile import NamedTemporaryFile
import requests

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
app.secret_key = "flask_secret_key"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# Configure Cloudinary
cloudinary.config(
    cloud_name="dge8cstlp",
    api_key="363171236823678",
    api_secret="3J6F-hFIuXvWNpfZAd2n0WDUl9Y",
)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))

    def __init__(self, name, email, password):
        self.name = name
        self.email = email
        self.password = bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

    def check_password(self, password):
        return bcrypt.checkpw(password.encode("utf-8"), self.password.encode("utf-8"))


class Todo(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    id = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    desc = db.Column(db.String(500), nullable=False)
    date_created = db.Column(db.DateTime, default=db.func.date())

    def __repr__(self) -> str:
        return f"{self.sno} - {self.title}"


class Image(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    id = db.Column(db.Integer, nullable=False)
    image_url = db.Column(db.String(500), nullable=False)
    date_created = db.Column(db.DateTime, default=db.func.date())

    def __repr__(self) -> str:
        return f"{self.sno} - {self.image_url}"


class Payment(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    sender_email = db.Column(db.String(100), nullable=False)
    receiver_email = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    date_created = db.Column(db.DateTime, default=db.func.date())

    def __repr__(self) -> str:
        return (
            f"{self.sno} - {self.sender_email} - {self.receiver_email} - {self.amount}"
        )


class Contact(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.Integer)
    message = db.Column(db.String(1000), nullable=False)
    date_created = db.Column(db.DateTime, default=db.func.date())

    def __repr__(self) -> str:
        return f"{self.sno} - {self.fullname} - {self.email} - {self.phone} - {self.message}"


# Login Routes
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        if not email:
            return render_template(
                "login.html",
                error="Login Failed!",
                errorMsg="Email cannot be empty.",
            )

        if not password:
            return render_template(
                "login.html",
                error="Login Failed!",
                errorMsg="Password cannot be empty.",
            )

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            session["id"] = user.id
            session["email"] = user.email
            return redirect("/home")
        else:
            return render_template(
                "login.html",
                error="Login Failed!",
                errorMsg="This email or password is incorrect.",
            )

    return render_template("login.html")


# Register Routes
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        if not name:
            return render_template(
                "register.html",
                error="Register Failed!",
                errorMsg="Name cannot be empty.",
            )

        if not email:
            return render_template(
                "register.html",
                error="Register Failed!",
                errorMsg="Email cannot be empty.",
            )

        if not password:
            return render_template(
                "register.html",
                error="Register Failed!",
                errorMsg="Password cannot be empty.",
            )

        user = User.query.filter_by(email=email).first()
        if not user:
            new_user = User(name=name, email=email, password=password)
            db.session.add(new_user)
            db.session.commit()
            session["id"] = new_user.id
            session["email"] = new_user.email
            return redirect("/home")
        else:
            return render_template(
                "register.html",
                error="Register Failed!",
                errorMsg="This email is already taken.",
            )
    return render_template("register.html")


# Home Routes
@app.route("/home", methods=["GET", "POST"])
def home():
    if not session["id"]:
        return redirect("/")

    allTodo = Todo.query.filter_by(id=session["id"]).all()
    if request.method == "POST":
        id = session["id"]
        title = request.form["title"]
        desc = request.form["desc"]

        if not title:
            return render_template(
                "home.html",
                allTodo=allTodo,
                error="Todo Failed!",
                errorMsg="Title cannot be empty.",
            )

        if not desc:
            return render_template(
                "home.html",
                allTodo=allTodo,
                error="Todo Failed!",
                errorMsg="Description cannot be empty.",
            )

        todo = Todo(id=id, title=title, desc=desc)
        db.session.add(todo)
        db.session.commit()

    allTodo = Todo.query.filter_by(id=session["id"]).all()
    return render_template("home.html", allTodo=allTodo)


@app.route("/update/<int:sno>", methods=["GET", "POST"])
def update(sno):
    if not session["id"]:
        return redirect("/")

    todo = Todo.query.filter_by(sno=sno).first()
    if request.method == "POST":
        title = request.form["title"]
        desc = request.form["desc"]

        if not title:
            return render_template(
                "update.html",
                todo=todo,
                error="Todo Failed!",
                errorMsg="Title cannot be empty.",
            )

        if not desc:
            return render_template(
                "update.html",
                todo=todo,
                error="Todo Failed!",
                errorMsg="Description cannot be empty.",
            )

        todo = Todo.query.filter_by(sno=sno).first()

        todo.title = title
        todo.desc = desc
        db.session.add(todo)
        db.session.commit()
        return redirect("/home")

    todo = Todo.query.filter_by(sno=sno).first()
    return render_template("update.html", todo=todo)


@app.route("/delete/<int:sno>")
def delete(sno):
    if not session["id"]:
        return redirect("/")

    todo = Todo.query.filter_by(sno=sno).first()
    db.session.delete(todo)
    db.session.commit()
    return redirect("/home")


# Gallery Routes
@app.route("/gallery", methods=["GET", "POST"])
def gallery():
    if not session["id"]:
        return redirect("/")

    allImage = Image.query.filter_by(id=session["id"]).all()
    if request.method == "POST":

        if "file" not in request.files:
            return render_template(
                "gallery.html",
                allImage=allImage,
                error="Upload Failed!",
                errorMsg="No image found.",
            )
        file = request.files["file"]

        if file.filename == "":
            return render_template(
                "gallery.html",
                allImage=allImage,
                error="Upload Failed!",
                errorMsg="No selected file.",
            )

        if file and allowed_file(file.filename):
            result = upload(file)
            id = session["id"]
            image = Image(id=id, image_url=result["secure_url"])
            db.session.add(image)
            db.session.commit()

    allImage = Image.query.filter_by(id=session["id"]).all()
    return render_template("gallery.html", allImage=allImage)


@app.route("/download/<int:sno>")
def download_image(sno):
    if not session["id"]:
        return redirect("/")

    image = Image.query.filter_by(sno=sno).first()
    allImage = Image.query.filter_by(id=session["id"]).all()
    if image:
        image_url = image.image_url
        filename = image_url.split("/")[-1]
        response = requests.get(image_url)
        if response.status_code == 200:
            temp_file = NamedTemporaryFile(delete=False)
            temp_file.write(response.content)
            temp_file.close()

            return send_file(temp_file.name, as_attachment=True, download_name=filename)
        else:
            return render_template(
                "gallery.html",
                allImage=allImage,
                error="Upload Failed!",
                errorMsg="Something went wrong, Image download failed.",
            )
    else:
        return render_template(
            "gallery.html",
            allImage=allImage,
            error="Upload Failed!",
            errorMsg="Something went wrong, Image not found.",
        )


@app.route("/delete_image/<int:sno>")
def delete_image(sno):
    if not session["id"]:
        return redirect("/")

    image = Image.query.filter_by(sno=sno).first()
    db.session.delete(image)
    db.session.commit()
    return redirect("/gallery")


# Payment Routes
@app.route("/payment", methods=["GET", "POST"])
def payment():
    if not session["email"]:
        return redirect("/")

    allPayment_sender = Payment.query.filter_by(sender_email=session["email"]).all()
    allPayment_receiver = Payment.query.filter_by(receiver_email=session["email"]).all()
    allPayment = allPayment_sender + allPayment_receiver

    if request.method == "POST":
        sender_email = session["email"]
        receiver_email = request.form["email"]
        amount = request.form["amount"]

        if not receiver_email:
            return render_template(
                "payment.html",
                allPayment=allPayment,
                error="Payment Failed!",
                errorMsg="Email address cannot be empty.",
            )

        if not amount:
            return render_template(
                "payment.html",
                allPayment=allPayment,
                error="Payment Failed!",
                errorMsg="Amount cannot be empty.",
            )

        check_receiver_email = User.query.filter_by(email=receiver_email).first()
        if not check_receiver_email:
            return render_template(
                "payment.html",
                allPayment=allPayment,
                error="Payment Failed!",
                errorMsg="Email address not registered.",
            )

        payment = Payment(
            sender_email=sender_email, receiver_email=receiver_email, amount=amount
        )
        db.session.add(payment)
        db.session.commit()

    allPayment_sender = Payment.query.filter_by(sender_email=session["email"]).all()
    allPayment_receiver = Payment.query.filter_by(receiver_email=session["email"]).all()
    allPayment = allPayment_sender + allPayment_receiver

    return render_template("payment.html", allPayment=allPayment)


@app.route("/delete_payment/<int:sno>")
def delete_payment(sno):
    if not session["id"]:
        return redirect("/")

    payment = Payment.query.filter_by(sno=sno).first()
    db.session.delete(payment)
    db.session.commit()
    return redirect("/payment")


# Account
@app.route("/account")
def account():
    if session["id"]:
        user = User.query.filter_by(id=session["id"]).first()
        return render_template("account.html", user=user)

    return redirect("/")


# Logout
@app.route("/logout")
def logout():
    session.pop("id", None)
    session.pop("email", None)
    return redirect("/")


# About
@app.route("/about")
def about():
    if session["id"]:
        return render_template("about.html")

    return redirect("/")


# Contact
@app.route("/contact", methods=["GET", "POST"])
def contact():
    if session["id"]:
        if request.method == "POST":
            fullname = request.form["fullname"]
            email = request.form["email"]
            phone = request.form["phone"]
            message = request.form["message"]

            contact = Contact(
                fullname=fullname, email=email, phone=phone, message=message
            )
            db.session.add(contact)
            db.session.commit()
            return render_template(
                "contact.html",
                success="Thank You.",
                successMsg="We will get back to you as soon as possible.",
            )

        return render_template("contact.html")

    return redirect("/")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=False)
