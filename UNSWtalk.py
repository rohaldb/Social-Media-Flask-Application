#!/usr/local/bin/python3.6

# written by andrewt@cse.unsw.edu.au October 2017
# as a starting point for COMP[29]041 assignment 2
# https://cgi.cse.unsw.edu.au/~cs2041/assignments/UNSWtalk/

import os, re, pathlib, sqlite3
from flask import Flask, render_template, session, g

students_dir = "static/dataset-small";
DATABASE = 'database.db'

app = Flask(__name__)

# DATABASE FUNCTIONS
def connect_db():
    return sqlite3.connect(DATABASE)
#database open conn
@app.before_request
def before_request():
    g.db = connect_db()
#database query func
def query_db(query, args=(), one=False):
    cur = g.db.execute(query, args)
    rv = [dict((cur.description[idx][0], value)
               for idx, value in enumerate(row)) for row in cur.fetchall()]
    return (rv[0] if rv else None) if one else rv
# close conn
@app.after_request
def after_request(response):
    g.db.close()
    return response

@app.route('/', methods=['GET','POST'])
@app.route('/start', methods=['GET','POST'])
def start():
    return render_template('start.html')

@app.route('/<z_id>', methods=['GET','POST'])
def student(z_id):
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

#gets all of a users friends
def getFriends(user_details):
    friends = []
    friend_ids = re.split(r"\s*,\s*", user_details["friends"])
    for friend_id in friend_ids:
        friend_data = query_db("select * from users where z_id=?", [friend_id], one=True)
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
                comment["replies"].insert(0,reply)
            post["comments"].insert(0,comment)
        pcr.insert(0,post)
    return pcr

if __name__ == '__main__':
    app.secret_key = os.urandom(12)
    app.run(debug=True)
