from flask_bcrypt import generate_password_hash
import mysql.connector

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="dosen123",
    database="course",
    port="3306"
)

cursor = db.cursor()

users = [
    ("Lia", "lia123"),
    ("dosen1", "passdosen")
]

for username, plain_pass in users:
    hashed = generate_password_hash(plain_pass).decode('utf-8')
    cursor.execute("UPDATE users SET password_hash=%s WHERE username=%s", (hashed, username))

db.commit()
cursor.close()
db.close()

print("✅ Semua password sudah di-hash di database!")
