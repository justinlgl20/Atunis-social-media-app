from flask import Blueprint, render_template, flash, session, request, redirect, url_for
from datetime import timedelta
import datetime
from werkzeug.security import generate_password_hash, check_password_hash

media = Blueprint(
    "media", __name__, static_folder="static", template_folder="templates"
)

from code import db, users, Post, followers


@media.route("/")
def home():
    return render_template("media_index.html", users=users)


@media.route("/chat")
def chat():
    return render_template("chat.html", users=users)


@media.route("/posts/<post_id>")
def view_post(post_id):
    post = Post.query.get(post_id)
    return render_template("view_post.html", post=post, users=users)


@media.route("/feed", methods=["GET", "POST"])
def feed():
    return render_template(
        "feed.html",
        users=users,
        Post=Post,
        given_posts=users.query.filter_by(name=session["user"])
        .first()
        .followed_posts()
        .all(),
    )


@media.route("/explore", methods=["GET", "POST"])
def explore():
    # USE RECOMMENDATION ENGINE TO GENERATE POSTS TO VIEW
    return render_template(
        "explore.html",
        users=users,
        Post=Post,
        given_posts=users.query.filter_by(name=session["user"])
        .first()
        .followed_posts()
        .all(),
    )


@media.route("/profile/<usr>", methods=["GET", "POST"])
def profile(usr):
    if request.method == "POST":
        if request.form["button"] == "Follow":
            usr = users.query.filter_by(name=usr).first()
            us = users.query.filter_by(name=session["user"]).first()
            us.follow(usr)
            flash("Followed " + usr.name)
            db.session.commit()
            return redirect(url_for("media.profile", usr=usr.name))
        else:
            usr = users.query.filter_by(name=usr).first()
            us = users.query.filter_by(name=session["user"]).first()
            us.unfollow(usr)
            flash("Unfollowed " + usr.name)
            db.session.commit()
            return redirect(url_for("media.profile", usr=usr.name))
    else:
        try:
            usr = users.query.filter_by(name=usr).first()
        except:
            flash("No user found")
            return redirect(url_for("media.home"))
        followers = usr.followers.all()
        following = usr.followed.all()
        return render_template(
            "profile.html",
            usr=usr,
            users=users,
            given_posts=Post.query.filter_by(author=usr),
            following=len(following),
            followers=len(followers),
            us=users.query.filter_by(name=session["user"]).first(),
        )


@media.route("/users", methods=["POST", "GET"])
def usrs():
    if request.method == "POST":
        search = request.form["search"]
        usrsi = users.query.filter(users.name.like("%" + search + "%")).limit(50)
        return render_template("media_users.html", users=users, given_users=usrsi)
    else:
        return render_template(
            "media_users.html", users=users, given_users=users.query.limit(50)
        )


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
