#!/web/cs2041/bin/python3.6.3
# creates the database


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
		id TEXT PRIMARY KEY,
		user TEXT REFERENCES Orders(ID),
		created_at TEXT,
		message TEXT,
		latitude REAL,
		longitude REAL,
		path TEXT NOT NULL)""")
c.execute("DROP TABLE IF EXISTS comments")
c.execute("""CREATE TABLE IF NOT EXISTS comments(
		id TEXT PRIMARY KEY,
		post REFERENCES posts(ID),
		user TEXT REFERENCES Orders(ID),
		created_at TEXT,
		message TEXT,
		path TEXT NOT NULL)""")
c.execute("DROP TABLE IF EXISTS replies")
c.execute("""CREATE TABLE IF NOT EXISTS replies(
		id TEXT PRIMARY KEY,
		comment REFERENCES comments(ID),
		user TEXT REFERENCES users(ID),
		created_at TEXT,
		message TEXT,
		path TEXT NOT NULL)""")

students_dir = "static/dataset-small"

# itterate over each user folder and extract data
for z_id in sorted(os.listdir(students_dir)):
	# open the student.txt file
	with open(os.path.join(students_dir, z_id, "student.txt")) as f:
		user_details = f.readlines()
	#get user image or set to default
	image_path = os.path.join(students_dir, z_id, "img.jpg")
	if not pathlib.Path(image_path).is_file():
		image_path = "static/images/defaultprofile.png"
	# extract user profile data
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
			courses = re.search(r'\((.*)\)', line)
			courses = courses.group(1)
	#store in database
	c.execute("INSERT INTO users (z_id, name, program, birthday, suburb, email, password, image_path, latitude, longitude, friends, courses) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (z_id, name, program, birthday, suburb, email, password, image_path, home_latitude, home_longitude, friends, courses))

	# start at 0 and count up looking for posts, comments and replies
	post_counter = 0
	# set path to post: static/dataset-small/z5191824/x.txt
	while pathlib.Path(os.path.join(students_dir, z_id, "%d.txt" % post_counter)).is_file():
		comment_counter = 0
		# open the post, and store in db
		with open(os.path.join(students_dir, z_id, "%d.txt" % post_counter)) as f:
			post = f.readlines()
		# extract data and save to database
		for line in post:
			if 'z_id: ' in line:
				z_id = line.rstrip('\n').split(': ')[1]
			if 'time: ' in line:
				created_at = line.rstrip('\n').split(': ')[1]
			if 'message: ' in line:
				message = line.rstrip('\n').split(': ')[1]
			if 'latitude: ' in line:
				latitude = line.rstrip('\n').split(': ')[1]
			if 'longitude: ' in line:
				longitude = line.rstrip('\n').split(': ')[1]
		#generate uuid
		post_id = str(uuid.uuid4()).replace('-','');
		c.execute("INSERT INTO posts (id, user, created_at, message, latitude, longitude, path) VALUES (?, ?, ?, ?, ?, ?, ?)", (post_id, z_id, created_at, message, latitude, longitude, os.path.join(students_dir, z_id, "%d.txt" % post_counter)))

		# look for comments on post
		# set path to comment: static/dataset-small/z5191824/x-y.txt
		while pathlib.Path(os.path.join(students_dir, z_id, "%d-%d.txt" % (post_counter, comment_counter))).is_file():
			reply_counter = 0
			# open the comment, and store in db
			with open(os.path.join(students_dir, z_id, "%d-%d.txt" % (post_counter, comment_counter))) as f:
				comment = f.readlines()

			for line in comment:
				if 'z_id: ' in line:
					z_id = line.rstrip('\n').split(': ')[1]
				if 'time: ' in line:
					created_at = line.rstrip('\n').split(': ')[1]
				if 'message: ' in line:
					message = line.rstrip('\n').split(': ')[1]
			comment_id = str(uuid.uuid4()).replace('-','');
			c.execute("INSERT INTO comments (id, post, user, created_at, message, path) VALUES (?, ?, ?, ?, ?, ?)", (comment_id, post_id, z_id, created_at, message,os.path.join(students_dir, z_id, "%d-%d.txt" % (post_counter, comment_counter))))

			# look for replies on comment
			# set path to comment: static/dataset-small/z5191824/x-y-z.txt
			while pathlib.Path(os.path.join(students_dir, z_id, "%d-%d-%d.txt" % (post_counter, comment_counter, reply_counter))).is_file():
				# open the reply, and store in db
				with open(os.path.join(students_dir, z_id, "%d-%d-%d.txt" % (post_counter, comment_counter, reply_counter))) as f:
					reply = f.readlines()
				for line in reply:
					if 'z_id: ' in line:
						z_id = line.rstrip('\n').split(': ')[1]
					if 'time: ' in line:
						created_at = line.rstrip('\n').split(': ')[1]
					if 'message: ' in line:
						message = line.rstrip('\n').split(': ')[1]
				reply_id = str(uuid.uuid4()).replace('-','');
				c.execute("INSERT INTO replies (id, comment, user, created_at, message, path) VALUES (?, ?, ?, ?, ?, ?)", (reply_id, comment_id, z_id, created_at, message,os.path.join(students_dir, z_id, "%d-%d-%d.txt" % (post_counter, comment_counter, reply_counter))))
				reply_counter+=1
			comment_counter+=1
		post_counter+=1


#commit and close connection
conn.commit()
c.close()
conn.close()
