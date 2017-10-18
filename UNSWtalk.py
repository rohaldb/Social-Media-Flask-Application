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
    with open(os.path.join(students_dir, z_id, "student.txt")) as f:
        details = divideDetailsIntoHash(f.readlines())
    # get the users image and set to default if it doesnt exist
    image_path = os.path.join(students_dir, z_id, "img.jpg")
    if not pathlib.Path(image_path).is_file(): image_path = "static/images/defaultprofile.png"
    # get the posts, comments and replies.
    pcr = getPCR(z_id)
    return render_template('profile.html', details=details, public_attrs=["program", "zid", "birthday", "full_name", "friends"], image_path=image_path, pcr=pcr)

def getUserDetails(z_id):
    return query_db("select * from users where z_id=?", [z_id], one=True)


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
                comment["replies"].append(reply)
            post["comments"].append(comment)
        pcr.append(post)
    return pcr

if __name__ == '__main__':
    app.secret_key = os.urandom(12)
    app.run(debug=True)
