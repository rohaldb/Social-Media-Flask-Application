#!/usr/bin/env python3.5
# creates the database


import sqlite3, glob, os, re
import shutil
conn = sqlite3.connect('database.db')
c = conn.cursor()

c.execute("DROP TABLE IF EXISTS users")
c.execute("""CREATE TABLE IF NOT EXISTS users(
		zid TEXT PRIMARY KEY NOT NULL,
		name TEXT,
		program TEXT,
		birthday TEXT,
		suburb TEXT,
		email TEXT,
		password TEXT NOT NULL,
		latitude REAL,
		longitude REAL,
		image_path TEXT,
		friends VARCHAR(100),
		courses VARCHAR(100))""")
c.execute("DROP TABLE IF EXISTS posts")
c.execute("""CREATE TABLE IF NOT EXISTS posts(
		zid TEXT NOT NULL,
		created_at TEXT,
		post_message TEXT,
		post_latitude REAL,
		post_longitude REAL,
		post_path TEXT PRIMARY KEY NOT NULL)""")
c.execute("DROP TABLE IF EXISTS comments")
c.execute("""CREATE TABLE IF NOT EXISTS comments(
		zid TEXT NOT NULL,
		created_at TEXT,
		comment_message TEXT,
		comment_path TEXT PRIMARY KEY NOT NULL)""")
c.execute("DROP TABLE IF EXISTS replies")
c.execute("""CREATE TABLE IF NOT EXISTS replies(
		zid TEXT NOT NULL,
		created_at TEXT,
		reply_message TEXT,
		reply_path TEXT PRIMARY KEY NOT NULL)""")

students_dir = "static/dataset-small";

for zid in sorted(os.listdir(students_dir)):
    with open(os.path.join(students_dir, zid, "student.txt")) as f:
        user_details = f.readlines()
	print(zid)
	for line in user_details:
			if 'name: ' in line:
				name = line.rstrip('\n').split(': ')[1]
			if 'program: ' in line:
				program = line.rstrip('\n').split(': ')[1]
			if 'birthday: ' in line:
				birthday = line.rstrip('\n').split(': ')[1]
			if 'home_suburb: ' in line:
				suburb = line.rstrip('\n').split(': ')[1]
			if 'email: ' in line:
				email = line.rstrip('\n').split(': ')[1]
			if 'password: ' in line:
				password = line.rstrip('\n').split(': ')[1]
			if 'home_latitude: ' in line:
				home_latitude = line.rstrip('\n').split(': ')[1]
			if 'home_longitude: ' in line:
				home_longitude = line.rstrip('\n').split(': ')[1]
			if 'friends: ' in line:
				friends = re.search(r'\((.*)\)', line)
				friends = friends.group(1)
			if 'courses: ' in line:
				courses = line
	c.execute("INSERT INTO users (zid, name, program, birthday, suburb, email, password, latitude, longitude, friends, courses) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (zid, name, program, birthday, suburb, email, password, home_latitude, home_longitude, friends, courses))

conn.commit()


c.close()
conn.close()

def divideDetailsIntoHash(details):
    hash = {}
    # for each line, place a:b into format hash[a] = b;
    for line in details:
        split_string = line.split(': ', 1)
        hash[split_string[0]] = split_string[1]
    return hash

# pcr = []
# post_counter = 0
# pcr.append
# # set path to post: static/dataset-small/z5191824/x.txt
# while pathlib.Path(os.path.join(students_dir, z_id, "%d.txt" % post_counter)).is_file():
# 	# print("found post %d" % post_counter)
# 	comment_counter = 0
# 	# open the post, divide contents into hash
# 	with open(os.path.join(students_dir, z_id, "%d.txt" % post_counter)) as f:
# 		post = divideDetailsIntoHash(f.readlines())
# 	post["comments"] = []
# 	# set path to comment: static/dataset-small/z5191824/x-y.txt
# 	while pathlib.Path(os.path.join(students_dir, z_id, "%d-%d.txt" % (post_counter, comment_counter))).is_file():
# 		# print("found comment %d on post %d" % (comment_counter, post_counter))
# 		reply_counter = 0
# 		# open the comment, divide contents into hash
# 		with open(os.path.join(students_dir, z_id, "%d-%d.txt" % (post_counter, comment_counter))) as f:
# 			comment = divideDetailsIntoHash(f.readlines())
# 		comment["replies"] = []
# 		# set path to comment: static/dataset-small/z5191824/x-y-z.txt
# 		while pathlib.Path(os.path.join(students_dir, z_id, "%d-%d-%d.txt" % (post_counter, comment_counter, reply_counter))).is_file():
# 			# print("found reply %d on comment %d on post %d" % (reply_counter, comment_counter, post_counter))
# 			# open the reply, divide contents into hash
# 			with open(os.path.join(students_dir, z_id, "%d-%d-%d.txt" % (post_counter, comment_counter, reply_counter))) as f:
# 				reply = divideDetailsIntoHash(f.readlines())
# 			comment["replies"].append(reply)
# 			reply_counter+=1
# 		post["comments"].append(comment)
# 		comment_counter+=1
# 	pcr.append(post)
# 	post_counter+=1
# print(pcr)
