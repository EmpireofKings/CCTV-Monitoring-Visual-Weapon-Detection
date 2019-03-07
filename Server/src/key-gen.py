import uuid
import MySQLdb as sql
import os

db = sql.connect(os.environ["DBHOST"], os.environ["DBUSER"], os.environ["DBPASS"], os.environ["DBNAME"])
cursor = db.cursor()

count = None

while count != 0:
	id = uuid.uuid4().hex
	cursor.execute("select * from productKey where activationKey = %s", (id,))
	count = cursor.rowcount

cursor.execute("insert into productKey (activationKey) values (%s)", (id,))
db.commit()

print("Activation Key:", id)
