#!/usr/local/bin/python3.6

# written by andrewt@cse.unsw.edu.au October 2017
# as a starting point for COMP[29]041 assignment 2
# https://cgi.cse.unsw.edu.au/~cs2041/assignments/UNSWtalk/

import os, re, pathlib
from flask import Flask, render_template, session

students_dir = "static/dataset-small";

app = Flask(__name__)

# Show unformatted details for student "n"
# Increment n and store it in the session cookie

@app.route('/', methods=['GET','POST'])
@app.route('/start', methods=['GET','POST'])
def start():
    return render_template('start.html')

@app.route('/<z_id>', methods=['GET','POST'])
def student(z_id):
    # n = session.get('n', 0)
    # students = sorted(os.listdir(students_dir))
    # student_to_show = students[n % len(students)]
    # session['n'] = n + 1

    # get the users details
    with open(os.path.join(students_dir, z_id, "student.txt")) as f:
        details = divideDetailsIntoHash(f.readlines())
    # get the users image and set to default if it doesnt exist
    image_filename = os.path.join(students_dir, z_id, "img.jpg")
    if not pathlib.Path(image_filename).is_file(): image_filename = "static/images/defaultprofile.png"
    # get the posts, comments and replies.
    pcr = getPCR(z_id)
    return render_template('profile.html', details=details, public_attrs=["program", "zid", "birthday", "full_name", "friends"], image_filename=image_filename, pcr=pcr)

# returns nested objects of posts comments and replies.
# [
#   }
#     text:
#     date:...
#     comments: {
#       date..
#       replies: {
#
#       }
#     }
#   }
# ]
def getPCR(z_id):
    pcr = []
    post_counter = 0
    pcr.append
    # set path to post: static/dataset-small/z5191824/x.txt
    while pathlib.Path(os.path.join(students_dir, z_id, "%d.txt" % post_counter)).is_file():
        # print("found post %d" % post_counter)
        comment_counter = 0
        # open the post, divide contents into hash
        with open(os.path.join(students_dir, z_id, "%d.txt" % post_counter)) as f:
            post = divideDetailsIntoHash(f.readlines())
        post["comments"] = []
        # set path to comment: static/dataset-small/z5191824/x-y.txt
        while pathlib.Path(os.path.join(students_dir, z_id, "%d-%d.txt" % (post_counter, comment_counter))).is_file():
            # print("found comment %d on post %d" % (comment_counter, post_counter))
            reply_counter = 0
            # open the comment, divide contents into hash
            with open(os.path.join(students_dir, z_id, "%d-%d.txt" % (post_counter, comment_counter))) as f:
                comment = divideDetailsIntoHash(f.readlines())
            comment["replies"] = []
            # set path to comment: static/dataset-small/z5191824/x-y-z.txt
            while pathlib.Path(os.path.join(students_dir, z_id, "%d-%d-%d.txt" % (post_counter, comment_counter, reply_counter))).is_file():
                # print("found reply %d on comment %d on post %d" % (reply_counter, comment_counter, post_counter))
                # open the reply, divide contents into hash
                with open(os.path.join(students_dir, z_id, "%d-%d-%d.txt" % (post_counter, comment_counter, reply_counter))) as f:
                    reply = divideDetailsIntoHash(f.readlines())
                comment["replies"].append(reply)
                reply_counter+=1
            post["comments"].append(comment)
            comment_counter+=1
        pcr.append(post)
        post_counter+=1
    print(pcr)
    return pcr

def divideDetailsIntoHash(details):
    hash = {}
    # for each line, place a:b into format hash[a] = b;
    for line in details:
        split_string = line.split(':', 1)
        hash[split_string[0]] = split_string[1]
    return hash

if __name__ == '__main__':
    app.secret_key = os.urandom(12)
    app.run(debug=True)
