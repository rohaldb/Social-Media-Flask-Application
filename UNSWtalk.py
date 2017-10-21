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
from datetime import datetime

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
def landing():
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
        response = make_response(redirect(url_for("landing")))
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
    # if not "current_user" in session:
    #     flash("You must be logged in to access that page")
    #     return redirect(url_for("login"))

    # get the users details
    user_details = getUserDetails(z_id)
    # get the posts, comments and replies.
    pcr = getPCRofUser(z_id)
    # get the users friend details
    friends = getFriends(z_id)
    return render_template('profile.html', user_details=user_details, public_attrs=["program", "zid", "birthday", "name", "friends"], image_path=user_details["image_path"], pcr=pcr, friends=friends)

# gets a users personal details


def getUserDetails(z_id):
    a = query_db("select * from users where z_id=?", [z_id], one=True)
    return a

# gets all of a users friends


def getFriends(z_id):
    user_details = getUserDetails(z_id)
    friends = []
    friend_ids = re.split(r"\s*,\s*", user_details["friends"])
    for friend_id in friend_ids:
        friend_data = query_db(
            "select * from users where z_id=?", [friend_id], one=True)
        friends.append(friend_data)
    return friends


# gets the comments, posts and replies for a user
def getPCRofUser(z_id):
    posts = query_db(
        "select * from posts where user=? order by created_at DESC", [z_id])
    return getCommentsAndRepliesOfPosts(posts)


def sanitizePCR(object):
    sanitizeTime(object)
    replaceTagsWithLinks(object)


def sanitizeTime(object):
    # remove time zone because cant get working with %z and convert to datetime
    time = datetime.strptime(object["created_at"], '%Y-%m-%d %H:%M:%S')
    # update to desired format
    object["created_at"] = datetime.strftime(time, ' %H:%M:%S, %a %d %m %Y')


def replaceTagsWithLinks(object):
    text = object["message"]
    # find all instances of zXXXXXXX and replace with link
    for match in re.findall(r"\b(z\d{7})\b", text):
        url = url_for('profile', z_id=match)
        text = text.replace(match, "<a href='%s'>%s</a>" % (url, match))
    object["message"] = text


@app.route('/home', methods=['GET', 'POST'])
def home():
    friends_content = getPCROfFriends("z5195935")
    mentioned_posts = getPCROfMentions("z5195935")
    users_post = getRecentPostsOfUser("z5195935")
    feed = friends_content + mentioned_posts + users_post
    # remove duplicated based on post id
    feed = list({v['id']:v for v in feed}.values())
    return render_template('home.html', feed=friends_content)

# def getRecentPostsOfUser(z_id):
#     posts = query_db("select * from posts where user=? order by created_at DESC LIMIT 5", [z_id])
#     return posts


def getCommentsAndRepliesOfPosts(posts):
    pcr = []
    # itterate over posts
    for post in posts:
        sanitizePCR(post)
        # get the comments for each post
        post["comments"] = []
        for comment in query_db("select * from comments where post=?", [post["id"]]):
            sanitizePCR(comment)
            # get the replies for each comment
            comment["replies"] = []
            for reply in query_db("select * from replies where comment=?", [comment["id"]]):
                sanitizePCR(reply)
                # append to parent objects
                comment["replies"].append(reply)
            post["comments"].append(comment)
        pcr.append(post)
    return pcr

# gets the posts comments and replies of a users friends


def getPCROfFriends(z_id):
    query = """select * from posts where user in
    (select friend from friends where reference=?)
     order by created_at DESC"""
    friends_posts = query_db(query, [z_id])
    return getCommentsAndRepliesOfPosts(friends_posts)



# gets alll posts of posts comments or replies where a user is mentioned
def getPCROfMentions(z_id):
    # query to find all posts where the post, a comment or a reply contain the users id
    query = """select * from posts p1 where
p1.id in (
	select id from posts p2 where p2.message like ?
)  or p1.id in (
	select post from comments c1 where c1.message like ?
)  or p1.id in (
	select post from replies p1 where p1.message like ?
)  order by created_at desc"""
    mentioned_posts = query_db(query, ['%'+z_id+'%', '%'+z_id+'%','%'+z_id+'%'])
    return getCommentsAndRepliesOfPosts(mentioned_posts)


if __name__ == '__main__':
    app.secret_key = os.urandom(12)
    app.run(debug=True)
