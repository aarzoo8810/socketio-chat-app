from flask import Flask, render_template, request, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from flask_socketio import SocketIO, send, leave_room, join_room
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, UserMixin, login_required, logout_user, current_user
from datetime import datetime

import os

from forms import RegisterForm, LoginForm

app = Flask(__name__)
app.config["SECRET_KEY"] = "J98TJ98U8T834IJYER9T4"
socketio = SocketIO(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "instance/chat_app.db")
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String, nullable=False)
    db.UniqueConstraint(username, email)

    def get_id(self):
        return (self.id)
    

class Chat(db.Model):
    __tablename__ = "chats"
    chat_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    channel_code = db.Column(db.String, nullable=False)
    chat_text = db.Column(db.String, nullable=False)
    datetime = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


with app.app_context():
    db.create_all()


@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()

    if request.method == "POST" and form.validate_on_submit:
        username = form.username.data.strip()
        email = form.email.data.strip()
        password = form.password.data.strip()

        hash_password = generate_password_hash(password, method="pbkdf2:sha256", salt_length=8)

        new_user = User(username=username, email=email, password=hash_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("register.html", form=form)

@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()

    if request.method == "POST" and form.validate_on_submit:
        email = form.email.data.strip()
        password = form.password.data.strip()

        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                    login_user(user)
                    # flash("Successfully logged in.")
                    return redirect(url_for('home'))
    
    return render_template("register.html", form=form)


@app.route("/logout")
def logout():
    logout_user()
    print(current_user)
    return redirect(url_for("home"))

@socketio.on("message")
def message(data):
    content = {
        "name": "anonymous",
        "message": data["data"]
    }
    print(content)
    send(content)


if "__main__" == __name__:
    app.run(debug=True, host="0.0.0.0")