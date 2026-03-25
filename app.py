from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import requests, hashlib
from config import Config
from models import db, User, Transaction

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/register", methods=["POST","GET"])
def register():
    if request.method=="POST":
        u = User(username=request.form["username"],
                 email=request.form["email"],
                 password=generate_password_hash(request.form["password"]))
        db.session.add(u)
        db.session.commit()
        return redirect("/login")
    return render_template("register.html")

@app.route("/login", methods=["POST","GET"])
def login():
    if request.method=="POST":
        u = User.query.filter_by(email=request.form["email"]).first()
        if u and check_password_hash(u.password, request.form["password"]):
            login_user(u)
            return redirect("/dashboard")
    return render_template("login.html")

@app.route("/dashboard")
@login_required
def dashboard():
    tx = Transaction.query.filter_by(user_id=current_user.id).all()
    return render_template("dashboard.html", user=current_user, tx=tx)

@app.route("/buy_airtime", methods=["POST"])
@login_required
def airtime():
    amt=float(request.form["amount"])
    if current_user.balance<amt:
        return "Low balance"
    headers={"api-key":app.config["VTPASS_API_KEY"],
             "public-key":app.config["VTPASS_PUBLIC_KEY"]}
    payload={"serviceID":"airtime","amount":amt,"phone":request.form["phone"]}
    r=requests.post("https://sandbox.vtpass.com/api/pay",json=payload,headers=headers).json()
    if r.get("code")=="000":
        current_user.balance-=amt
        db.session.commit()
    return redirect("/dashboard")

@app.route("/fund", methods=["POST"])
@login_required
def fund():
    amt=int(request.form["amount"])*100
    headers={"Authorization":f"Bearer {app.config['PAYSTACK_SECRET_KEY']}"}
    data={"email":current_user.email,"amount":amt}
    return requests.post("https://api.paystack.co/transaction/initialize",json=data,headers=headers).json()

@app.route("/webhook", methods=["POST"])
def webhook():
    sig=request.headers.get("x-paystack-signature")
    secret=app.config["PAYSTACK_SECRET_KEY"]
    hashv=hashlib.sha512(request.data+secret.encode()).hexdigest()
    if sig!=hashv: return "bad",400
    data=request.json
    if data["event"]=="charge.success":
        email=data["data"]["customer"]["email"]
        amt=data["data"]["amount"]/100
        u=User.query.filter_by(email=email).first()
        if u:
            u.balance+=amt
            db.session.commit()
    return jsonify({"ok":True})

@app.route("/admin")
@login_required
def admin():
    if not current_user.is_admin:
        return "Forbidden"
    users=User.query.all()
    tx=Transaction.query.all()
    return render_template("admin.html",users=users,tx=tx)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")

if __name__=="__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
