#!/web/cs2041/bin/python3.6.3

# written by andrewt@cse.unsw.edu.au October 2017
# as a starting point for COMP[29]041 assignment 2
# https://cgi.cse.unsw.edu.au/~cs2041/assignments/UNSWtalk/
import smtplib
import os
import re
import pathlib
import sqlite3
import uuid
from flask import Flask, render_template, session, g, request, redirect, make_response, url_for, flash
from datetime import datetime
from flask import Markup

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

# http://flask.pocoo.org/snippets/37/
def insert(table, date, fields=(), values=()):
    # g.db is the database connection
    cur = g.db.cursor()
    # if the field requires a date field
    # assumes date is the final value
    if date:
        query = 'INSERT INTO %s (%s) VALUES (%s)' % (
            table,
            ', '.join(fields),
            ', '.join(['?'] * (len(values)-1)) + ', DATETIME(?)',
        )
    else:
        query = 'INSERT INTO %s (%s) VALUES (%s)' % (
        table,
        ', '.join(fields),
        ', '.join(['?'] * len(values))
        )
    cur.execute(query, values)
    g.db.commit()
    id = cur.lastrowid
    cur.close()
    return id

# deletes items based
def delete(table, conditions=()):
    # g.db is the database connection
    cur = g.db.cursor()
    query = 'DELETE FROM %s WHERE %s ' % (
        table,
        ' and '.join(conditions)
    )
    cur.execute(query)
    g.db.commit()
    cur.close()
    return id

def update(table, fields, condition):
    # g.db is the database connection
    cur = g.db.cursor()
    query = 'UPDATE %s SET %s where %s' % (
        table,
        ', '.join(fields),
        condition
    )
    cur.execute(query)
    g.db.commit()
    cur.close()
    return id

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
    if request.method == 'POST':
        z_id = request.form.get('z_id', '')
        password = request.form.get('password', '')
        user = query_db("select * from users where z_id=? and password=?",[z_id, password], one=True)
        if user:
            # sign them in
            if user["verified"]:
                session["current_user"] = z_id
                response = make_response(redirect(url_for("home")))
                return response
            # send them home and dont sign in if not verified
            else:
                flash("Please verify your email address before continuing")
                response = make_response(redirect(url_for("landing")))
                return response
        else:
            flash("Unknown username or password")
            response = make_response(render_template('login.html'))
            return response
    else:
        return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email', '')
        password = request.form.get('password', '')
        z_id = request.form.get('z_id', '')
        name = request.form.get('name', '')
        existing_user = query_db("select * from users where z_id=?",[z_id], one=True)
        if existing_user:
            flash("A user with this zid has already made an account")
            response = make_response(render_template('signup.html'))
            return response
        else:
            insert("users", False, ["z_id", "email", "password", "name", "image_path","verified"], [z_id, email, password, name, 'images/defaultprofile.png', 0])
            sendmail(email, "Verify Account", verificationEmailText(z_id))
            flash("Please verify your email address before continuing")
            response = make_response(redirect(url_for("landing")))
            return response
    else:
        return render_template('signup.html')

@app.route('/forgot', methods=['GET', 'POST'])
def forgot():
    if request.method == 'POST':
        z_id = request.form.get('z_id', '')
        user = query_db("select * from users where z_id=?", [z_id], one=True)
        sendmail(user["email"], "Password Reset", passwordResetEmailText(z_id))
        flash("Password Reset sent")
        return make_response(redirect(url_for("landing")))
    else:
        return render_template('forgot.html')

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    if "current_user" in session:
        session.pop("current_user", None)
        response = make_response(redirect(url_for('landing')))
        return response
    else:
        response = make_response(redirect(url_for('landing')))
        return response


@app.route('/search', methods=['GET', 'POST'])
def search():
    # redirect back to login if not authenticated
    if not "current_user" in session:
        flash("You must be logged in to access that page")
        return redirect(url_for("login"))
    # extract the thing we are searching for
    search_query = request.form.get('search_query', '')
    # find matched user
    matched_users = query_db("select * from users where z_id like ? and verified=1", ['%'+search_query+'%'])
    # find matching pcrs
    pcrs = getPCRThatMention(search_query)
    # sort them by date
    pcrs = sorted(pcrs, key=lambda k: datetime.strptime(k['created_at'], '%Y-%m-%d %H:%M:%S'), reverse=True)
    # sanitize them
    for i in pcrs: sanitizePCR(i)
    return render_template('search.html', matched_users=matched_users, pcrs=pcrs)


@app.route('/profile/<z_id>', methods=['GET', 'POST'])
def profile(z_id):
    # redirect back to login if not authenticated
    if not "current_user" in session:
        flash("You must be logged in to access that page")
        return redirect(url_for("login"))
    # get the users details
    user_details = getUserDetails(z_id)
    # get the posts, comments and replies.
    pcrs = getPCRofUser(z_id)
    # sanitize them
    for i in pcrs: sanitizePCR(i)
    # get the users friend details
    friends = getFriends(z_id)
    # check if the current user is friends with this user
    # check if they are already friends
    already_friends = query_db("select * from friends where reference=? and friend=?",[session["current_user"], z_id], one=True)
    return render_template('profile.html', profile_z_id=z_id ,user_details=user_details, public_attrs=["program", "zid", "birthday", "name", "friends", "bio"], pcrs=pcrs, friends=friends, already_friends=already_friends)

# gets a users personal details


def getUserDetails(z_id):
    a = query_db("select * from users where z_id=?", [z_id], one=True)
    return a

# gets all of a users friends


def getFriends(z_id):
    # redirect back to login if not authenticated
    if not "current_user" in session:
        flash("You must be logged in to access that page")
        return redirect(url_for("login"))
    friends = []
    # find the users friends from the friends table
    results = query_db("select friend from friends where reference=?", [z_id])
    # find info on each friend
    for result in results:
        friend_data = query_db(
            "select * from users where z_id=?", [result["friend"]], one=True)
        friends.append(friend_data)
    return friends


# gets the comments, posts and replies for a user
def getPCRofUser(z_id):
    posts = query_db(
        "select * from posts where user=? order by created_at DESC", [z_id])
    return posts


def sanitizePCR(object):
    sanitizeTime(object)
    replaceTagsWithLinks(object)
    sanitizeNewLines(object)

def sanitizeNewLines(object):
    object["message"] = Markup(re.sub(r"\\n", "<br>", object["message"]))


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
    # check user is logged in
    if not "current_user" in session:
        flash("You must be logged in to access that page")
        return redirect(url_for("login"))
    # get the feed content, and set source and identifier so we can print appropriately on feed
    friends_content = setObjectSource(setObjectType(getFriendsPosts(session["current_user"]), "post"),"friend")
    mentions = setObjectSource(getPCRThatMention(session["current_user"]), "mention")
    users_posts = setObjectSource(setObjectType(getRecentPostsOfUser(session["current_user"]), "post"), "self")
    # group the elements into a single list
    feed = friends_content + users_posts + mentions
    # sort them by date
    feed = sorted(feed, key=lambda k: datetime.strptime(k['created_at'], '%Y-%m-%d %H:%M:%S'), reverse=True)
    # sanitize them
    for i in feed: sanitizePCR(i)
    return render_template('home.html', feed=feed)

def getRecentPostsOfUser(z_id):
    posts = query_db("select * from posts where user=? order by created_at DESC", [z_id])
    return posts


def getCommentsAndRepliesOfPost(post):
    sanitizePCR(post)
    # get the comments for each post
    post["comments"] = []
    for comment in query_db("select * from comments where post=?  order by created_at DESC", [post["id"]]):
        sanitizePCR(comment)
        # get the replies for each comment
        comment["replies"] = []
        for reply in query_db("select * from replies where comment=?  order by created_at DESC", [comment["id"]]):
            sanitizePCR(reply)
            # append to parent objects
            comment["replies"].append(reply)
        post["comments"].append(comment)
    return post

# gets friends posts
def getFriendsPosts(z_id):
    query = """select * from posts where user in
    (select friend from friends where reference=?)
     order by created_at DESC"""
    friends_posts = query_db(query, [z_id])
    return friends_posts



# gets alll posts of posts comments or replies where a user is mentioned
def getPCRThatMention(z_id):
    # query to find all posts where the user is mentioned:
    post_query = "select * from posts where message like ? order by created_at desc"
    comment_query = "select * from comments where message like ? order by created_at desc"
    reply_query = "select * from replies where message like ? order by created_at desc"
    posts = setObjectType(query_db(post_query, ['%'+z_id+'%']), "post")
    comments = setObjectType(query_db(comment_query, ['%'+z_id+'%']), "comment")
    replies = setObjectType(query_db(reply_query, ['%'+z_id+'%']), "replies")
    return (posts + comments + replies)

# sets an identifier in the object to either post, comment or reply
def setObjectType(objects, type):
    for object in objects:
        object["type"] = type
    return objects

# sets source to either mention, friend or self to help with displaying on the ui
def setObjectSource(objects, type):
    for object in objects:
        object["source"] = type
    return objects

@app.route('/newpost', methods=['GET', 'POST'])
def newpost():
    message = request.form.get('message', '')
    # check user is logged in
    if not "current_user" in session:
        flash("You must be logged in to access that page")
        return redirect(url_for("login"))
    # otherwise we are good to post
    else:
        insert("posts", True, ["id", "user", "message", "created_at" ], [str(uuid.uuid4()).replace('-',''),session["current_user"], message, getCurrentDateTime()])
        return redirect(request.referrer)

@app.route('/newcomment', methods=['GET', 'POST'])
def newcomment():
    message = request.form.get('message', '')
    post_id = request.form.get('post_id', '')
    # check user is logged in
    if not "current_user" in session:
        flash("You must be logged in to access that page")
        return redirect(url_for("login"))
    # check if the message is empty
    elif not message:
        flash("Cannot comment an empty message")
        return redirect(request.referrer)
    # otherwise we are good to post
    else:
        insert("comments", True, ["id", "post", "user", "message", "created_at" ], [str(uuid.uuid4()).replace('-',''), post_id, session["current_user"], message, getCurrentDateTime()])
        return redirect(request.referrer)

@app.route('/newreply', methods=['GET', 'POST'])
def newreply():
    message = request.form.get('message', '')
    post_id = request.form.get('post_id', '')
    comment_id = request.form.get('post_id', '')
    # check user is logged in
    if not "current_user" in session:
        flash("You must be logged in to access that page")
        return redirect(url_for("login"))
    # check if the message is empty
    elif not message:
        flash("Cannot comment an empty message")
        return redirect(request.referrer)
    # otherwise we are good to post
    else:
        insert("replies", True, ["id", "comment", "post", "user", "message", "created_at" ], [str(uuid.uuid4()).replace('-',''), comment_id, post_id, session["current_user"], message, getCurrentDateTime()])
        return redirect(request.referrer)


# returns the current datetime in the database format
def getCurrentDateTime():
    d = datetime.now()
    return datetime.strftime(d, '%Y-%m-%d %H:%M:%S')

@app.route('/post/<id>', methods=['GET', 'POST'])
def viewpost(id):
    # check user is logged in
    if not "current_user" in session:
        flash("You must be logged in to access that page")
        return redirect(url_for("login"))
    # query the post based on id
    post = query_db("select * from posts where id=? order by created_at DESC",[id], one=True)
    # get comments and replies
    pcr = getCommentsAndRepliesOfPost(post)
    # render
    return render_template('post.html', pcr=pcr)

@app.route('/removefriend', methods=['GET', 'POST'])
def removefriend():
    # check user is logged in
    if not "current_user" in session:
        flash("You must be logged in to access that page")
        return redirect(url_for("login"))
    #get the friend id from the form
    friend_id = request.form.get('friend_id', '')
    # delete the friend from current users list and delete current user from friends list
    delete("friends", ["reference = '%s'" % session["current_user"], "friend = '%s'" % friend_id])
    delete("friends", ["friend = '%s'" % session["current_user"], "reference = '%s'" % friend_id])
    # return to where we came from
    return redirect(request.referrer)

@app.route('/addfriend', methods=['GET', 'POST'])
def addfriend():
    # check user is logged in
    if not "current_user" in session:
        flash("You must be logged in to access that page")
        return redirect(url_for("login"))
    #get the friend id from the form
    insert("friends", False, ["reference", "friend"], [session["current_user"], friend_id])
    insert("friends", False, ["reference", "friend"], [friend_id, session["current_user"]])
    # return to where we came from
    return redirect(request.referrer)

@app.route('/verify/<z_id>', methods=['GET', 'POST'])
def verify(z_id):
    # set verified field to 1
    update("users", ["verified=1"], "z_id='%s'" % z_id)
    # log them in and go home
    session["current_user"] = z_id
    flash("Account successfully verified")
    return redirect(url_for("home"))

@app.route('/reset/<z_id>', methods=['GET', 'POST'])
def reset(z_id):
    if request.method == 'POST':
        #get the new password and z_id
        password = request.form.get('password', '')
        z_id = request.form.get('z_id', '')
        update("users", ["password='%s'"% password], "z_id='%s'" % z_id)
        # log them in and go home
        session["current_user"] = z_id
        flash("Password successfully reset")
        return redirect(url_for("home"))
    else:
        return render_template('reset.html', z_id=z_id)

def verificationEmailText(z_id):
    return """
Thanks for signing up %s!
Click the link below to verify your account:
http://127.0.0.1:5000%s
    """ % (z_id, url_for('verify', z_id=z_id))

def passwordResetEmailText(z_id):
    return """
Hi %s,
Click the link below to reset your email:
http://127.0.0.1:5000%s
    """ % (z_id, url_for('reset', z_id=z_id))

# https://stackoverflow.com/a/26191922/4803964
def sendmail(to, subject, message):
    to = to
    gmail_user = 'z5019999ass2'
    gmail_pwd = 'z5019999password'
    smtpserver = smtplib.SMTP("smtp.gmail.com",587)
    smtpserver.ehlo()
    smtpserver.starttls()
    smtpserver.ehlo()
    smtpserver.login(gmail_user, gmail_pwd)
    header = 'To:' + to + '\n' + 'From: ' + gmail_user + '\n' + 'Subject: ' + subject +  '\n'
    msg = header + '\n' + message + '\n\n'
    print(header)
    print(msg)
    smtpserver.sendmail(gmail_user, to, msg)
    print('done!')
    smtpserver.quit()

@app.route('/edit_profile/<z_id>', methods=['GET', 'POST'])
def edit_profile(z_id):
    # check user is logged in
    if not "current_user" in session:
        flash("You must be logged in to access that page")
        return redirect(url_for("login"))
    # check if the user owns this page
    if session["current_user"] != z_id:
        flash("You cannot edit someone else's profile")
        return redirect(url_for("home"))
    if request.method == 'POST':
        # check which values are not empty and update them
        fields = ["name","email","program","birthday","suburb","latitude","longitude", "bio"]
        fields_to_update = []
        for field in fields:
            if request.form.get(field):
                fields_to_update.append("%s='%s'" % (field, request.form.get(field)))
        update("users", fields_to_update, "z_id='%s'" % z_id)
        return redirect(request.referrer)

    else:
        # get the users info to prefill
        user = query_db("select * from users where z_id=?", [z_id], one=True)
        return render_template('edit_profile.html', z_id=z_id, user=user)


if __name__ == '__main__':
    app.secret_key = os.urandom(12)
    app.run(debug=True)
