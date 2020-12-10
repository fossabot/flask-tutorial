import functools

from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask import url_for
from werkzeug.exceptions import abort

from flaskr import db
from flaskr.auth.models import Users

bp = Blueprint("auth", __name__, url_prefix="/auth")


def login_required(view):
    """View decorator that redirects anonymous users to the login page."""

    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))

        return view(**kwargs)

    return wrapped_view


def get_profile(id, check_author=True):
    # user = Users.query.filter_by(id=id).with_entities(Users.username.label('username'), Users.profile.label('profile')).first()
    # user.update({'username': user_attributes[0], 'profile' = })
    user = Users.query.get_or_404(id, f"User id {id} doesn't exist.")
    print(user.username)
    print(g.user)
    if check_author and user != g.user:
        abort(403)

    return user


@bp.before_app_request
def load_logged_in_user():
    """If a user id is stored in the session, load the user object from
    the database into ``g.user``."""
    user_id = session.get("user_id")
    g.user = Users.query.get(user_id) if user_id is not None else None


@bp.route("/register", methods=("GET", "POST"))
def register():
    """Register a new user.

    Validates that the username is not already taken. Hashes the
    password for security.
    """
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        profile = request.form["profile"]
        error = None

        if not username:
            error = "Username is required."
        elif not password:
            error = "Password is required."
        elif not profile:
            error = "Profile is required."
        elif db.session.query(
            Users.query.filter_by(username=username).exists()
        ).scalar():
            error = f"User {username} is already registered."

        if error is None:
            # the name is available, create the user and go to the login page
            db.session.add(Users(username=username, password=password, profile=profile))
            db.session.commit()
            return redirect(url_for("auth.login"))

        flash(error)

    return render_template("auth/register.html")


@bp.route("/login", methods=("GET", "POST"))
def login():
    """Log in a registered user by adding the user id to the session."""
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        error = None
        user = Users.query.filter_by(username=username).first()

        if user is None:
            error = "Incorrect username."
        elif not user.check_password(password):
            error = "Incorrect password."

        if error is None:
            # store the user id in a new session and return to the index
            session.clear()
            session["user_id"] = user.id
            return redirect(url_for("index"))

        flash(error)

    return render_template("auth/login.html")


@bp.route("/logout")
def logout():
    """Clear the current session, including the stored user id."""
    session.clear()
    return redirect(url_for("index"))


@bp.route("/<int:id>/profile", methods=("GET", "POST"))
@login_required
def profile(id):
    """Update a user profile"""
    user = get_profile(id)

    if request.method == "POST":
        username = request.form["username"] 
        profile = request.form["profile"]
        error = None

        if not username:
            error = "Username is required"

        if not profile:
            error = "Profile is required"

        if error is not None:
            flash(error)
        else:
            user.username = username
            user.profile = profile
            db.session.commit()
            return redirect(url_for("blog.index"))
    
    return render_template("auth/profile.html", user=user)