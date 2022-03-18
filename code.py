from flask import Flask, redirect, url_for, render_template, request, session, flash
from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy
from hashlib import md5
from werkzeug.security import generate_password_hash, check_password_hash
import datetime


app = Flask(__name__)
app.secret_key = "somethingsohardthatnoonewillguessit,butiknowhwatitisikr,butitissoannoying,butnoonewillunlockthishash"
app.permanent_session_lifetime = timedelta(minutes=480)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.sqlite3"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

followers = db.Table(
    "followers",
    db.Column("follower_id", db.Integer, db.ForeignKey("users.id")),
    db.Column("followed_id", db.Integer, db.ForeignKey("users.id")),
)


class users(db.Model):
    id = db.Column("id", db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    about_me = db.Column(db.String(400))
    password = db.Column(db.String(100))
    posts = db.relationship("Post", backref="author", lazy="dynamic")
    followed = db.relationship(
        "users",
        secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref("followers", lazy="dynamic"),
        lazy="dynamic",
    )

    def avatar(self):
        return (
            "https://www.gravatar.com/avatar/"
            + md5(self.email.encode()).hexdigest()
            + "?d=identicon"
        )

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(followers.c.followed_id == user.id).count() > 0

    def followed_posts(self):
        followed = Post.query.join(
            followers, (followers.c.followed_id == Post.user_id)
        ).filter(followers.c.follower_id == self.id)
        own = Post.query.filter_by(user_id=self.id)
        return followed.union(own).order_by(Post.date.desc())


class Post(db.Model):
    id = db.Column("id", db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    body = db.Column(db.String(400))
    date = db.Column(db.String(100), index=True, default=datetime.datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))


from media import media

app.register_blueprint(media, url_prefix="/media")


@app.route("/")
def home():
    return render_template("index.html", users=users)


@app.route("/edit_user", methods=["GET", "POST"])
def edit_user():
    email = None
    if "user" in session:
        usr = users.query.filter_by(name=session["user"]).first()
        user = session["user"]
        if request.method == "POST":
            email = request.form["email"]
            psw = request.form["psw"]
            usr.email = email
            usr.about_me = request.form["about_me"]
            usr.password = generate_password_hash(psw)
            db.session.commit()
            flash("Settings changed")
            return redirect(url_for("user"))
        else:
            email = usr.email
            return render_template(
                "edit_user.html", users=users, email=email, password=usr.password
            )
    else:
        return redirect(url_for("login"))


@app.route("/user", methods=["GET", "POST"])
def user():
    email = None
    if "user" in session:
        usr = users.query.filter_by(name=session["user"]).first()
        if request.method == "POST":
            return redirect(
                url_for("edit_user", email=usr.email, password=usr.password)
            )
        else:
            return render_template(
                "user.html", users=users, email=usr.email, password=usr.password
            )
    else:
        return redirect(url_for("login"))


@app.route("/login", methods=["POST", "GET"])
def login():
    if "user" in session:
        return redirect(url_for("chat"))
    elif request.method == "POST":
        session.permanent = True
        user = request.form["nm"]
        password = request.form["password"]
        try:
            x = users.query.filter_by(name=user).first()
            if x and check_password_hash(x.password, password):
                session["user"] = user
                flash("Logged in")
                return redirect(url_for("home"))
            else:
                flash("Wrong log-in details")
                return redirect(url_for("login"))
        except:
            flash("Wrong log-in details")
            return redirect(url_for("login"))
        return redirect(url_for("home"))
    else:
        return render_template("login.html", users=users)


@app.route("/logout")
def logout():
    if "user" in session:
        flash("You have been logged out", "info")
    session.pop("user", None)
    session.pop("email", None)
    return redirect(url_for("home"))


@app.route("/chat")
def chat():
    if "user" in session:
        user = session["user"]
        return render_template("chat.html", user=user, users=users)
    else:
        return redirect(url_for("login"))


@app.route("/signup", methods=["POST", "GET"])
def signup():
    if request.method == "POST":
        user = request.form["user_name"]
        try:
            found_user = users.query.filter_by(name=user).first()
            if found_user:
                flash("Username already taken")
                return redirect(url_for("signup"))
            else:
                password = request.form["psw"]
                second = request.form["psw-repeat"]
                if password != second:
                    flash("Passwords do not match")
                    return redirect(url_for("signup"))
                tc = request.form["T&C"]
                if tc != "on":
                    flash("You must agree to our T&Cs")
                    return redirect(url_for("signup"))
                usr = users(
                    name=user,
                    email="",
                    about_me="",
                    password=generate_password_hash(password),
                )

                db.session.add(usr)
                db.session.commit()
                session["user"] = user
                flash("Account created")
                return redirect(url_for("user"))
        except:
            password = request.form["psw"]
            second = request.form["psw-repeat"]
            if password != second:
                flash("Passwords do not match")
                return redirect(url_for("signup"))
            tc = request.form["T&C"]
            if tc != "on":
                flash("You must agree to our T&Cs")
                return redirect(url_for("signup"))
            usr = users(user, "", "", password)
            db.session.add(usr)
            db.session.commit()
            usr.about_me = ""
            db.session.commit()
            session["user"] = user
            flash("Account created")
            return redirect(url_for("user"))
    else:
        return render_template("signup.html", users=users)


if __name__ == "__main__":
    db.create_all()
    app.run()
