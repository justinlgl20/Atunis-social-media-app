from flask import Blueprint, render_template, flash, session, request, redirect, url_for
from datetime import timedelta
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy


media = Blueprint(
    "media", __name__, static_folder="static", template_folder="templates"
)

from code import db, users, Post


@media.route("/")
def home():
    return render_template("media_index.html", users=users)


@media.route("/chat")
def chat():
    return render_template("chat.html", users=users)


@media.route("/feed", methods=["GET", "POST"])
def feed():
    return render_template("feed.html", users=users, Post=Post, given_posts=Post.query.all())


@media.route("/profile/<usr>")
def profile(usr):
    return render_template("profile.html", usr=users.query.filter_by(name=usr).first(), Post=Post, users=users)

@media.route("/users")
def users():
    return render_template("media_users.html", users=users)

@media.route("/user", methods=["GET", "POST"])
def mediauser():
    email = None
    if "user" in session:
        usr = users.query.filter_by(name=session["user"]).first()
        if request.method == "POST":
            return redirect(
                url_for("media.mediaedit_user", email=usr.email, password=usr.password)
            )
        else:
            return render_template(
                "mediauser.html", users=users, email=usr.email, password=usr.password
            )
    else:
        return redirect(url_for("login"))


@media.route("/edit_user", methods=["GET", "POST"])
def mediaedit_user():
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
            return redirect(url_for("media.mediauser"))
        else:
            email = usr.email
            return render_template(
                "mediaedit_user.html", users=users, email=email, password=usr.password
            )
    else:
        return redirect(url_for("login"))


@media.route("/post", methods=["GET", "POST"])
def post():
    if request.method == "POST":
        body = request.form["body"]
        title = request.form["title"]
        if title == "" or body == "":
            flash("Fill in all areas")
            return redirect(url_for("post", title=title, body=body))
        pos = Post(
            title=title,
            body=body,
            author=users.query.filter_by(name=session["user"]).first(),
        )
        db.session.add(pos)
        db.session.commit()
        flash("Post made")
        return redirect(url_for("media.feed"))
    return render_template("post.html", users=users)
