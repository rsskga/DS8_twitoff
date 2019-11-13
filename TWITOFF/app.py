"""TwitOff router/controller/application"""

from decouple import config
from flask import Flask, render_template, request
from .models import DB, User
from .predict import predict_user
from .twitter import add_or_update_user, update_all_users


def create_app():
    """Create/configure Flask app"""
    app = Flask(__name__)

    app.config["ENV"] = config("ENV")
    app.config["SQLALCHEMY_DATABASE_URI"] = config("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    DB.init_app(app)

    @app.route("/")
    def root():
        users = User.query.all()
        return render_template("base.html", title="Home",
                               users=User.query.all())

    @app.route("/reset")
    def reset():
        DB.drop_all()
        DB.create_all()
        return render_template("base.html", title="Reset database")

    @app.route("/update")
    def update():
        update_all_users()
        return render_template("base.html", title="Update all users",
                               users=User.query.all())

    @app.route("/user", methods=["POST"])
    @app.route("/user/<name>", methods=["GET"])
    def user(name=None, message=""):
        name = name or request.values["user_name"]
        try:
            if request.method == "POST":
                add_or_update_user(name)
                message = "User {} successfully added!".format(name)
            tweets = User.query.filter(User.name == name).one().tweets
        except Exception as e:
            message = "Error adding {}: {}".format(name, e)
            tweets = []
        return render_template("user.html", title=name, tweets=tweets,
                               message=message)

    @app.route("/compare", methods=["POST"])
    def compare(message=''):
        user1, user2 = sorted([request.values["user1"],
                               request.values["user2"]])
        if user1 == user2:
            message = "Cannot compare a user to themselves!"
        else:
            tweet_text = request.values["tweet_text"]
            confidence = int(predict_user(user1, user2, tweet_text) * 100)
            if confidence >= 50:
                message = (
                    f'"{tweet_text}\" is more likely to be said by {user1} '
                    f'than {user2}, with {confidence}% confidence'
                )
            else:
                message = (
                    f'"{tweet_text}" is more likely to be said by {user2} '
                    f'than {user1}, with {100 - confidence}% confidence'
                )
        return render_template("prediction.html", title="Prediction",
                               message=message)

    return app
