#!/usr/bin/env python3.5
# creates the database


import sqlite3, glob, os, re, pathlib
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
		zid TEXT REFERENCES Orders(ID),
		created_at TEXT,
		message TEXT,
		latitude REAL,
		longitude REAL,
		path TEXT PRIMARY KEY NOT NULL)""")
c.execute("DROP TABLE IF EXISTS comments")
c.execute("""CREATE TABLE IF NOT EXISTS comments(
		post REFERENCES posts(ID),
		zid TEXT REFERENCES Orders(ID),
		created_at TEXT,
		message TEXT,
		path TEXT PRIMARY KEY NOT NULL)""")
c.execute("DROP TABLE IF EXISTS replies")
c.execute("""CREATE TABLE IF NOT EXISTS replies(
		comment REFERENCES comments(ID),
		zid TEXT REFERENCES users(ID),
		created_at TEXT,
		message TEXT,
		path TEXT PRIMARY KEY NOT NULL)""")

students_dir = "static/dataset-small"

for zid in sorted(os.listdir(students_dir)):
	with open(os.path.join(students_dir, zid, "student.txt")) as f:
		user_details = f.readlines()
	#get user image or set to default
	image_path = os.path.join(students_dir, zid, "img.jpg")
	if not pathlib.Path(image_path).is_file():
		image_path = "static/images/defaultprofile.png"
	for line in user_details:
		if 'name: ' in line:
			name = line.split(': ')[1]
		if 'program: ' in line:
			program = line.split(': ')[1]
		if 'birthday: ' in line:
			birthday = line.split(': ')[1]
		if 'home_suburb: ' in line:
			suburb = line.split(': ')[1]
		if 'email: ' in line:
			email = line.split(': ')[1]
		if 'password: ' in line:
			password = line.split(': ')[1]
		if 'home_latitude: ' in line:
			home_latitude = line.split(': ')[1]
		if 'home_longitude: ' in line:
			home_longitude = line.split(': ')[1]
		if 'friends: ' in line:
			friends = re.search(r'\((.*)\)', line)
			friends = friends.group(1)
		if 'courses: ' in line:
			courses = line

	c.execute("INSERT INTO users (zid, name, program, birthday, suburb, email, password, image_path, latitude, longitude, friends, courses) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (zid, name, program, birthday, suburb, email, password, image_path, home_latitude, home_longitude, friends, courses))

# def divideDetailsIntoHash(details):
#     hash = {}
#     # for each line, place a:b into format hash[a] = b;
#     for line in details:
#         split_string = line.split(': ', 1)
#         hash[split_string[0]] = split_string[1]
#     return hash

post_counter = 0
# set path to post: static/dataset-small/z5191824/x.txt
while pathlib.Path(os.path.join(students_dir, zid, "%d.txt" % post_counter)).is_file():
	# print("found post %d" % post_counter)
	comment_counter = 0
	# open the post, divide contents into hash
	with open(os.path.join(students_dir, zid, "%d.txt" % post_counter)) as f:
		post = f.readlines()
	print(os.path.join(students_dir, zid, "%d.txt" % post_counter))
	# # set path to comment: static/dataset-small/z5191824/x-y.txt
	# while pathlib.Path(os.path.join(students_dir, zid, "%d-%d.txt" % (post_counter, comment_counter))).is_file():
	# 	# print("found comment %d on post %d" % (comment_counter, post_counter))
	# 	reply_counter = 0
	# 	# open the comment, divide contents into hash
	# 	with open(os.path.join(students_dir, zid, "%d-%d.txt" % (post_counter, comment_counter))) as f:
	# 		comment = divideDetailsIntoHash(f.readlines())
	# 	comment["replies"] = []
	# 	# set path to comment: static/dataset-small/z5191824/x-y-z.txt
	# 	while pathlib.Path(os.path.join(students_dir, zid, "%d-%d-%d.txt" % (post_counter, comment_counter, reply_counter))).is_file():
	# 		# print("found reply %d on comment %d on post %d" % (reply_counter, comment_counter, post_counter))
	# 		# open the reply, divide contents into hash
	# 		with open(os.path.join(students_dir, zid, "%d-%d-%d.txt" % (post_counter, comment_counter, reply_counter))) as f:
	# 			reply = divideDetailsIntoHash(f.readlines())
	# 		comment["replies"].append(reply)
	# 		reply_counter+=1
	# 	post["comments"].append(comment)
	# 	comment_counter+=1
	for line in post:
		if 'zid: ' in line:
			zid = line.split(': ')[1]
		if 'time: ' in line:
			created_at = line.split(': ')[1]
		if 'message: ' in line:
			message = line.split(': ')[1]
		if 'latitude: ' in line:
			latitude = line.split(': ')[1]
		if 'longitude: ' in line:
			longitude = line.split(': ')[1]
	c.execute("INSERT INTO posts (zid, created_at, message, latitude, longitude, path) VALUES (?, ?, ?, ?, ?, ?)", (zid, created_at, message, latitude, longitude, os.path.join(students_dir, zid, "%d.txt" % post_counter)))
	post_counter+=1





conn.commit()
c.close()
conn.close()
