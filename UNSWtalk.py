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
    pcr = getPCR()

    return render_template('profile.html', details=details, public_attrs=["program", "zid", "birthday", "full_name", "friends"], image_filename=image_filename)

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
def getPCR():
    for student in sorted(os.listdir(students_dir)):
        print(student)
        post_counter = 0
        # set path to comment: static/dataset-small/z5191824/0.txt
        post_path =  os.path.join(students_dir, student, "%d.txt" % post_counter)
        print("initial %s" % post_path)
        while pathlib.Path(post_path).is_file():
            print("found post %d" % post_counter)
            comment_counter = 0
            comment_path =  os.path.join(students_dir, student, "%d-%d.txt" % (post_counter, comment_counter))
            while pathlib.Path(comment_path).is_file():
                print("found comment %d on post %d" % (comment_counter, post_counter))
                reply_counter = 0
                reply_path = os.path.join(students_dir, student, "%d-%d-%d.txt" % (post_counter, comment_counter, reply_counter))
                while pathlib.Path(reply_path).is_file():
                    print("found reply %d on comment %d on post %d" % (reply_counter, comment_counter, post_counter))
                    reply_counter+=1
                    reply_path = os.path.join(students_dir, student, "%d-%d-%d.txt" % (post_counter, comment_counter, reply_counter))
                comment_counter+=1
                comment_path =  os.path.join(students_dir, student, "%d-%d.txt" % (post_counter, comment_counter))
            post_counter+=1
            post_path =  os.path.join(students_dir, student, "%d.txt" % post_counter)
    return 11

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
