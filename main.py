from flask import Flask, render_template, request, redirect, url_for, session

from werkzeug.security import generate_password_hash, check_password_hash
from flask_socketio import SocketIO, send, leave_room, join_room
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, UserMixin, login_required, logout_user, current_user
from datetime import datetime

import os

from forms import RegisterForm, LoginForm, CreateChannelForm

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
    chat = db.relationship("Chat", backref="users", lazy=True)
    db.UniqueConstraint(username, email)

    def get_id(self):
        return (self.id)

class Channel(db.Model):
    __tablename__ = "channels"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)
    chats = db.relationship("Chat", backref="channels", lazy=True)

class Chat(db.Model):
    __tablename__ = "chats"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    channel_id = db.Column(db.Integer, db.ForeignKey("channels.id"), nullable=False)
    chat_text = db.Column(db.String, nullable=False)
    datetime = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


with app.app_context():
    db.create_all()

    try:
        first_user = User(username="admin", email="admin@mail.com", password=generate_password_hash("admin"))
        db.session.add(first_user)
        db.session.commit()
        second_user = User(username="mushoku", email="mushoku@mail.com", password=generate_password_hash("mushoku"))
        db.session.add(second_user)
        db.session.commit()
    except:
        pass

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


@app.route("/")
def home():
    channels = Channel.query.all()
    return render_template("index.html", channels=channels)


@app.route("/create-channel", methods=["POST", "GET"])
def create_channel():
    form = CreateChannelForm()

    if request.method == "POST" and form.validate_on_submit:
        channel_name = form.channel_name.data.strip()
        
        channel_entry = Channel.query.filter_by(name=channel_name).first()
        if not channel_entry:
            new_channel = Channel(name=channel_name)
            db.session.add(new_channel)
            db.session.commit()
        else:
            print(f"Error: Channel {channel_name} already exists.")


    return render_template("create_channel.html", form=form)


@app.route("/channel/<int:channel_id>")
def channel(channel_id):
    channels = Channel.query.all()
    chats = Chat.query.filter_by(channel_id=channel_id).all()
    if current_user.is_authenticated:
        print(current_user.is_authenticated)
        session["channel_id"] = channel_id
        session["username"] = current_user.username
        return render_template("index.html", chats=chats, channels=channels)

    return render_template("index.html", chats=chats, channels=channels)


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
    room = int(session.get("channel_id"))
    if room and room > 0 and current_user.is_authenticated:
        new_chat = Chat(user_id=current_user.id, channel_id=room, chat_text=data["data"])
        db.session.add(new_chat)
        db.session.commit()
        content = {
            "name": current_user.username,
            "message": data["data"],
            "username": current_user.username,
            "datetime": new_chat.datetime.isoformat()
        }
        print(new_chat.datetime)
        send(content, to=room)
        print(content)
    else:
        return


@socketio.on("connect")
def connect(auth):
    room = session.get("channel_id")
    name = session.get("username")

    if room:
        join_room(room)
        send({"name": name, "message": "has entered the room."}, to=room)
        print(f"{name} joined room {room}")


if "__main__" == __name__:
    app.run(debug=True, host="0.0.0.0")