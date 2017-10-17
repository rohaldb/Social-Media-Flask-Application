#!/usr/local/bin/python3.6

# written by andrewt@cse.unsw.edu.au October 2017
# as a starting point for COMP[29]041 assignment 2
# https://cgi.cse.unsw.edu.au/~cs2041/assignments/UNSWtalk/

import os
import re
from flask import Flask, render_template, session

students_dir = "dataset-small";

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
    details_filename = os.path.join(students_dir, z_id, "student.txt")
    with open(details_filename) as f:
        details = divideDetailsIntoHash(f.readlines())
    return render_template('profile.html', details=details, public_attrs=["program", "zid", "birthday", "full_name", "friends"])

def divideDetailsIntoHash(details):
    hash = {}
    for line in details:
        split_string = line.split(':', 1)
        hash[split_string[0]] = split_string[1]
    print(hash)
    return hash

if __name__ == '__main__':
    app.secret_key = os.urandom(12)
    app.run(debug=True)
