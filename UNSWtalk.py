#!/web/cs2041/bin/python3.6.3

# written by andrewt@cse.unsw.edu.au October 2017
# as a starting point for COMP[29]041 assignment 2
# https://cgi.cse.unsw.edu.au/~cs2041/assignments/UNSWtalk/
# return redirect("/login", code=302)

import os
import re
import pathlib
import sqlite3
from flask import Flask, render_template, session, g, request, redirect, make_response, url_for, flash

students_dir = "static/dataset-small"
DATABASE = 'database.db'


app = Flask(__name__)


def connect_db():
    return sqlite3.connect(DATABASE)
# database open conn


@app.before_request
def before_request():
    g.db = connect_db()

def query_db(query, args=(), one=False):
    cur = g.db.execute(query, args)
    rv = [dict((cur.description[idx][0], value)
               for idx, value in enumerate(row)) for row in cur.fetchall()]
    return (rv[0] if rv else None) if one else rv


@app.after_request
def after_request(response):
    g.db.close()
    return response


@app.route('/', methods=['GET', 'POST'])
def home():
    if "current_user" in session:
        print("current user from start is ")
        print(session["current_user"])
    else:
        print("aint no user bish")
    return render_template('start.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    username = request.form.get('email', '')
    password = request.form.get('password', '')
    user = query_db("select * from users where email=? and password=?",
                    [username, password], one=True)
    if user:
        session["current_user"] = user["z_id"]
        response = make_response(redirect(url_for("home")))
        response.set_cookie('user', user["z_id"])
        return response
    else:
        response = make_response(render_template('login.html'))
        return response


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    if "current_user" in session:
        session.pop("current_user", None)
        response = make_response(redirect("/"))
        return response
    else:
        response = make_response(redirect("/"))
        return response


@app.route('/search', methods=['GET', 'POST'])
def search():
    # redirect back to login if not authenticated
    if not "current_user" in session:
        flash("You must be logged in to access that page")
        return redirect(url_for("login"))

    search_query = request.form.get('search_query', '')
    matched_users = query_db(
        "select * from users where z_id like ?", [search_query])
    return render_template('search.html', matched_users=matched_users)


@app.route('/profile/<z_id>', methods=['GET', 'POST'])
def profile(z_id):
    # redirect back to login if not authenticated
    if not "current_user" in session:
        flash("You must be logged in to access that page")
        return redirect(url_for("login"))

    # get the users details
    user_details = getUserDetails(z_id)
    # get the posts, comments and replies.
    pcr = getPCR(z_id)
    # get the users friend details
    friends = getFriends(user_details)
    return render_template('profile.html', user_details=user_details, public_attrs=["program", "zid", "birthday", "name", "friends"], image_path=user_details["image_path"], pcr=pcr, friends=friends)

# gets a users personal details


def getUserDetails(z_id):
    a = query_db("select * from users where z_id=?", [z_id], one=True)
    return a

# gets all of a users friends


def getFriends(user_details):
    friends = []
    friend_ids = re.split(r"\s*,\s*", user_details["friends"])
    for friend_id in friend_ids:
        friend_data = query_db(
            "select * from users where z_id=?", [friend_id], one=True)
        friends.append(friend_data)
    return friends


# gets the comments, posts and replies for a user
def getPCR(z_id):
    pcr = []
    # itterate over posts
    for post in query_db("select * from posts where user=?", [z_id]):
        # get the comments for each post
        post["comments"] = []
        for comment in query_db("select * from comments where post=?", [post["id"]]):
            # get the replies for each comment
            comment["replies"] = []
            for reply in query_db("select * from replies where comment=?", [comment["id"]]):
                # append to parent objects
                comment["replies"].insert(0, reply)
            post["comments"].insert(0, comment)
        pcr.insert(0, post)
    return pcr


if __name__ == '__main__':
    app.secret_key = os.urandom(12)
    app.run(debug=True)
