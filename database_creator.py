#!/web/cs2041/bin/python3.6.3
# This file handles the creation of our database on load. It traverses the file structure and pulls out relevant information
# Cases where A is friends with B, but not the other way round are interpreted as A has sent a pending friend request to B

import sqlite3, glob, os, re, pathlib, uuid
import shutil
# create connection
conn = sqlite3.connect('database.db')
conn.text_factory = str
c = conn.cursor()
# create nescesary tables
c.execute("DROP TABLE IF EXISTS users")
c.execute("""CREATE TABLE IF NOT EXISTS users(
		z_id TEXT PRIMARY KEY NOT NULL,
		name TEXT,
		bio TEXT,
		program TEXT,
		birthday TEXT,
		suburb TEXT,
		email TEXT,
		password TEXT NOT NULL,
		latitude REAL,
		longitude REAL,
		image_path TEXT,
		background_path TEXT,
		friends VARCHAR(100),
		courses VARCHAR(100),
		verified INTEGER
		)""")
c.execute("DROP TABLE IF EXISTS posts")
c.execute("""CREATE TABLE IF NOT EXISTS posts(
		id TEXT PRIMARY KEY,
		user TEXT REFERENCES Orders(ID),
		created_at DATE,
		message TEXT,
		latitude REAL,
		longitude REAL,
		media_type TEXT,
		content_path TEXT,
		path TEXT )""")
c.execute("DROP TABLE IF EXISTS comments")
c.execute("""CREATE TABLE IF NOT EXISTS comments(
		id TEXT PRIMARY KEY,
		post REFERENCES posts(ID),
		user TEXT REFERENCES Orders(ID),
		created_at DATE,
		message TEXT,
		media_type TEXT,
		content_path TEXT,
		path TEXT )""")
c.execute("DROP TABLE IF EXISTS replies")
c.execute("""CREATE TABLE IF NOT EXISTS replies(
		id TEXT PRIMARY KEY,
		comment REFERENCES comments(ID),
		user TEXT REFERENCES users(ID),
		post REFERENCES posts(ID),
		created_at DATE,
		message TEXT,
		content_path TEXT,
		media_type TEXT,
		path TEXT )""")
c.execute("DROP TABLE IF EXISTS friends")
c.execute("""CREATE TABLE IF NOT EXISTS friends(
		reference TEXT NOT NULL,
		friend TEXT NOT NULL,
		accepted INTEGER
		)""")
c.execute("DROP TABLE IF EXISTS courses")
c.execute("""CREATE TABLE IF NOT EXISTS courses(
		user TEXT NOT NULL,
		year TEXT NOT NULL,
		semester INTEGER NOT NULL,
		code TEXT NOT NULL
		)""")

students_dir = "static/dataset-medium"

# itterate over each user folder and extract data
for z_id in sorted(os.listdir(students_dir)):
	# open the student.txt file
	with open(os.path.join(students_dir, z_id, "student.txt")) as f:
		user_details = f.readlines()
	#get user image or set to default
	image_path = os.path.join("dataset-medium", z_id, "img.jpg")
	if not pathlib.Path('static/%s' % image_path).is_file():
		image_path = "images/defaultprofile.png"
	# extract user profile data
	for line in user_details:
		if re.match(r"^full_name\s*:", line):
			name = line.rstrip('\n').split(': ', 1)[1]
		if re.match(r"^program\s*:", line):
			program = line.rstrip('\n').split(': ', 1)[1]
		if re.match(r"^birthday\s*:", line):
			birthday = line.rstrip('\n').split(': ', 1)[1]
		if re.match(r"^home_suburb\s*:", line):
			suburb = line.rstrip('\n').split(': ', 1)[1]
		if re.match(r"^email\s*:", line):
			email = line.rstrip('\n').split(': ', 1)[1]
		if re.match(r"^password\s*:", line):
			password = line.rstrip('\n').split(': ', 1)[1]
		if re.match(r"^home_latitude\s*:", line):
			home_latitude = line.rstrip('\n').split(': ', 1)[1]
		if re.match(r"^home_longitude\s*:", line):
			home_longitude = line.rstrip('\n').split(': ', 1)[1]
		if re.match(r"^friends\s*:", line):
			# itterate over friends list and create friend instances
			friends = re.search(r'\((.*)\)', line)
			friends = friends.group(1)
			friend_ids = re.split(r"\s*,\s*", friends)
			for friend_id in friend_ids:
				c.execute("INSERT INTO friends (reference, friend, accepted) VALUES (?, ?, ?)", (z_id, friend_id, 0))
		if re.match(r"^courses\s*:", line):
			# itterate over course list and create friend instances
			courses = re.search(r'\((.*)\)', line)
			courses = courses.group(1)
			course_list = re.split(r",", courses)
			for course in course_list:
				course_info = course.split()
				c.execute("INSERT INTO courses (user, year, semester, code) VALUES (?, ?, ?, ?)", (z_id, course_info[0], course_info[1][1], course_info[2]))
	c.execute("INSERT INTO users (z_id, name, program, birthday, suburb, email, password, image_path, latitude, longitude, friends, courses, verified) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (z_id, name, program, birthday, suburb, email, password, image_path, home_latitude, home_longitude, friends, courses, 1))

	# start at 0 and count up looking for posts, comments and replies
	# eg start at 0.txt, then 1.txt etc
	post_counter = 0
	# set path to post: static/dataset-medium/z5191824/x.txt
	while pathlib.Path(os.path.join(students_dir, z_id, "%d.txt" % post_counter)).is_file():
		comment_counter = 0
		# open the post, and store in db
		with open(os.path.join(students_dir, z_id, "%d.txt" % post_counter)) as f:
			post = f.readlines()
		# extract data and save to database
		for line in post:
			if re.match(r"^from\s*:", line):
				z_id = line.rstrip('\n').split(': ', 1)[1]
			if re.match(r"^time\s*:", line):
				created_at = line.rstrip('\n').split(': ', 1)[1]
			if re.match(r"^message\s*:", line):
				message = line.rstrip('\n').split(': ', 1)[1]
			if re.match(r"^latitude\s*:", line):
				latitude = line.rstrip('\n').split(': ', 1)[1]
			if re.match(r"^longitude\s*:", line):
				longitude = line.rstrip('\n').split(': ', 1)[1]
		#generate uuid
		post_id = str(uuid.uuid4()).replace('-','');
		c.execute("INSERT INTO posts (id, user, created_at, message, latitude, longitude, media_type, path) VALUES (?, ?, DATETIME(?), ?, ?, ?, ?, ?)", (post_id, z_id, created_at[:-5], message, latitude, longitude, "text", os.path.join(students_dir, z_id, "%d.txt" % post_counter)))
		# look for comments on post
		# set path to comment: static/dataset-medium/z5191824/x-y.txt
		while pathlib.Path(os.path.join(students_dir, z_id, "%d-%d.txt" % (post_counter, comment_counter))).is_file():
			reply_counter = 0
			# open the comment, and store in db
			with open(os.path.join(students_dir, z_id, "%d-%d.txt" % (post_counter, comment_counter))) as f:
				comment = f.readlines()

			for line in comment:
				if re.match(r"^from\s*:", line):
					commenter_z_id = line.rstrip('\n').split(': ', 1)[1]
				if re.match(r"^time\s*:", line):
					created_at = line.rstrip('\n').split(': ', 1)[1]
				if re.match(r"^message\s*:", line):
					message = line.rstrip('\n').split(': ', 1)[1]
			comment_id = str(uuid.uuid4()).replace('-','');
			c.execute("INSERT INTO comments (id, post, user, created_at, message, media_type, path) VALUES (?, ?, ?, DATETIME(?), ?, ?, ?)", (comment_id, post_id, commenter_z_id, created_at[:-5], message, "text", os.path.join(students_dir, z_id, "%d-%d.txt" % (post_counter, comment_counter))))

			# look for replies on comment
			# set path to comment: static/dataset-medium/z5191824/x-y-z.txt
			while pathlib.Path(os.path.join(students_dir, z_id, "%d-%d-%d.txt" % (post_counter, comment_counter, reply_counter))).is_file():
				# open the reply, and store in db
				with open(os.path.join(students_dir, z_id, "%d-%d-%d.txt" % (post_counter, comment_counter, reply_counter))) as f:
					reply = f.readlines()
				for line in reply:
					if re.match(r"^from\s*:", line):
						replier_z_id = line.rstrip('\n').split(': ', 1)[1]
					if re.match(r"^time\s*:", line):
						created_at = line.rstrip('\n').split(': ', 1)[1]
					if re.match(r"^message\s*:", line):
						message = line.rstrip('\n').split(': ', 1)[1]
				reply_id = str(uuid.uuid4()).replace('-','');
				c.execute("INSERT INTO replies (id, comment, user, created_at, post, message, media_type,  path) VALUES (?, ?, ?, DATETIME(?), ?,?,  ?, ?)", (reply_id, comment_id, replier_z_id, created_at[:-5], post_id, message, "text", os.path.join(students_dir, z_id, "%d-%d-%d.txt" % (post_counter, comment_counter, reply_counter))))
				reply_counter+=1
			comment_counter+=1
		post_counter+=1

# set query function to help with the following
def query_db(query, args=(), one=False):
    cur = c.execute(query, args)
    rv = [dict((cur.description[idx][0], value)
               for idx, value in enumerate(row)) for row in cur.fetchall()]
    return (rv[0] if rv else None) if one else rv

# check for two way friendships and update them to be accepted
# for each friendship
for friendship in query_db("select * from friends f1"):
	# if we find it to be bi directional
	if query_db("select * from friends where reference=? and friend=?", [friendship["friend"], friendship["reference"]], one=True):
		# set to accepted to accepted
		c.execute("update friends set accepted=1 where reference=? and friend=?", [friendship["reference"], friendship["friend"]])

#commit and close connection
conn.commit()
c.close()
conn.close()
