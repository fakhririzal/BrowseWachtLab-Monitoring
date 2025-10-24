from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_cors import CORS
from flask_bcrypt import Bcrypt
import mysql.connector
from mysql.connector import pooling, Error
import os
import random
import string

dbconfig = {
    "host": "localhost",
    "user": "root",
    "password": "dosen123",
    "database": "course",
    "port": 3306
}

try:
    connection_pool = pooling.MySQLConnectionPool(pool_name="mypool", pool_size=5, **dbconfig)
    print("✅ MySQL connection pool created successfully.")
except Error as e:
    print("❌ Error while connecting to MySQL:", e)

app = Flask(__name__)
app.secret_key = "pbl-308"
bcrypt = Bcrypt(app)
CORS(app, supports_credentials=True)

# Folder untuk menyimpan file upload
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def get_db_connection():
    """Mengambil koneksi baru dari pool"""
    try:
        conn = connection_pool.get_connection()
        return conn
    except Error as e:
        print("❌ Error getting connection:", e)
        return None

def generate_course_code():
    """Membuat kode acak 6 karakter campuran huruf dan angka"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

@app.route("/", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        role = request.form.get("role")
        username = request.form.get("username")
        password = request.form.get("password")

        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Gagal terhubung ke database"}), 500

        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username=%s AND role=%s", (username, role))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and bcrypt.check_password_hash(user["password_hash"], password):
            # Simpan sesi login
            session["role"] = user["role"]
            session["username"] = user["username"]
            session["name"] = user["name"]
            session["user_id"] = user["id"]  # Simpan user_id di session

            # Redirect berdasarkan role
            if role == "mahasiswa":
                return redirect("/mahasiswa_dashboard")
            elif role == "dosen":
                return redirect("/dosen_dashboard")
            elif role == "admin":
                return redirect("http://localhost:8080/admin")
        else:
            error = "Jenis User / Username / Password salah!"

    return render_template("login.html", error=error)

@app.route("/mahasiswa_dashboard")
def get_mahasiswa():
    return render_template("mahasiswa.html")

@app.route("/dosen_course")
def get_dosen_course():
    conn = get_db_connection()
    if not conn:
        return "Database connection failed", 500

    cursor = conn.cursor(dictionary=True)
    
    # Ambil semua course
    cursor.execute("SELECT * FROM courses")
    courses = cursor.fetchall()
    
    # Untuk setiap course, ambil task-nya
    for course in courses:
        cursor.execute("SELECT * FROM task WHERE course_code = %s", (course['course_code'],))
        tasks = cursor.fetchall()
        
        # Format deadline untuk setiap task
        for task in tasks:
            if task['deadline']:
                from datetime import datetime
                dt = task['deadline']
                # Format deadline menjadi string yang diinginkan
                task['deadline_display'] = dt.strftime('%d %B %Y, %H:%M')
                # Format untuk input datetime-local
                task['deadline_input'] = dt.strftime('%Y-%m-%dT%H:%M')
            else:
                task['deadline_display'] = 'N/A'
                task['deadline_input'] = ''
        
        course['tasks'] = tasks
    
    cursor.close()
    conn.close()
    
    return render_template("dosen.html", courses=courses)

# HAPUS DEFINISI ROUTE YANG PERTAMA (yang ini dihapus)
# @app.route("/mahasiswa_course")
# def get_mahasiswa_course():
#     return render_template("mahasiswa_course.html")

# GUNAKAN HANYA DEFINISI ROUTE YANG KEDUA (ini yang dipertahankan)
@app.route("/mahasiswa_course")
def get_mahasiswa_course():
    # Periksa apakah user sudah login dan role-nya mahasiswa
    if "role" not in session or session["role"] != "mahasiswa":
        return redirect(url_for("login"))
    
    # Ambil ID mahasiswa dari session
    mahasiswa_id = session.get("user_id")
    if not mahasiswa_id:
        # Jika tidak ada di session, ambil dari database
        conn = get_db_connection()
        if not conn:
            return "Database connection failed", 500
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id FROM users WHERE username=%s", (session["username"],))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user:
            mahasiswa_id = user["id"]
            session["user_id"] = mahasiswa_id
        else:
            return "User not found", 404
    
    # Ambil course yang diikuti oleh mahasiswa
    conn = get_db_connection()
    if not conn:
        return "Database connection failed", 500
    
    cursor = conn.cursor(dictionary=True)
    
    # Ambil course yang diikuti mahasiswa
    query = """
        SELECT c.course_code, c.nama, c.course_name
        FROM mahasiswa_courses mc
        JOIN courses c ON mc.course_code = c.course_code
        WHERE mc.mahasiswa_id = %s
    """
    cursor.execute(query, (mahasiswa_id,))
    courses = cursor.fetchall()
    
    # Untuk setiap course, ambil task-nya
    for course in courses:
        cursor.execute("SELECT * FROM task WHERE course_code = %s", (course['course_code'],))
        tasks = cursor.fetchall()
        
        # Format deadline untuk setiap task
        for task in tasks:
            if task['deadline']:
                from datetime import datetime
                dt = task['deadline']
                # Format deadline menjadi string yang diinginkan
                task['deadline_display'] = dt.strftime('%d %B %Y, %H:%M')
                # Format untuk input datetime-local
                task['deadline_input'] = dt.strftime('%Y-%m-%dT%H:%M')
            else:
                task['deadline_display'] = 'N/A'
                task['deadline_input'] = ''
        
        course['tasks'] = tasks
    
    cursor.close()
    conn.close()
    
    return render_template("mahasiswa_course.html", courses=courses)

@app.route("/api/mahasiswa")
def get_mahasiswa_data():
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Koneksi database gagal"}), 500

    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM courses")
    data = cursor.fetchall()
    cursor.close()
    conn.close()

    return jsonify(data)

@app.route("/api/join-course", methods=["POST"])
def join_course():
    data = request.get_json()
    mahasiswa_id = data.get("mahasiswa_id", 1)
    course_code = data.get("course_code")

    if not course_code:
        return jsonify({"error": "course_code is required"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Koneksi database gagal"}), 500

    cursor = conn.cursor(dictionary=True)

    # Pastikan course ada
    cursor.execute("SELECT * FROM courses WHERE course_code = %s", (course_code,))
    course = cursor.fetchone()
    if not course:
        cursor.close()
        conn.close()
        return jsonify({"error": "Kode course tidak ditemukan"}), 404

    # Cek apakah mahasiswa sudah join
    cursor.execute(
        "SELECT * FROM mahasiswa_courses WHERE mahasiswa_id = %s AND course_code = %s",
        (mahasiswa_id, course_code)
    )
    exists = cursor.fetchone()
    if exists:
        cursor.close()
        conn.close()
        return jsonify({"message": "Mahasiswa sudah terdaftar di course ini"}), 200
    
    cursor.execute(
        "INSERT INTO mahasiswa_courses (mahasiswa_id, course_code) VALUES (%s, %s)",
        (mahasiswa_id, course_code)
    )
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "Mahasiswa berhasil join course!"}), 200

@app.route("/api/joined-courses/<int:mahasiswa_id>", methods=["GET"])
def get_joined_courses(mahasiswa_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Koneksi database gagal"}), 500

    cursor = conn.cursor(dictionary=True)
    query = """
        SELECT c.course_code, c.nama, c.course_name
        FROM mahasiswa_courses mc
        JOIN courses c ON mc.course_code = c.course_code
        WHERE mc.mahasiswa_id = %s
    """
    cursor.execute(query, (mahasiswa_id,))
    data = cursor.fetchall()
    cursor.close()
    conn.close()

    return jsonify(data)

# === Tambahan baru untuk update otomatis task di course mahasiswa ===
@app.route("/api/refresh-course/<string:course_code>", methods=["GET"])
def refresh_course(course_code):
    """
    Endpoint agar halaman mahasiswa bisa memuat ulang daftar task terbaru
    sesuai course_code yang sama dengan dosen.
    """
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Koneksi database gagal"}), 500

    cursor = conn.cursor(dictionary=True)

    # Pastikan course valid
    cursor.execute("SELECT * FROM courses WHERE course_code = %s", (course_code,))
    course = cursor.fetchone()
    if not course:
        cursor.close()
        conn.close()
        return jsonify({"error": "Course tidak ditemukan"}), 404

    # Ambil semua task untuk course tersebut
    cursor.execute(
        "SELECT id, title, description, deadline, file, created_at FROM task WHERE course_code = %s ORDER BY created_at DESC",
        (course_code,)
    )
    tasks = cursor.fetchall()

    from datetime import datetime
    for t in tasks:
        t["deadline_display"] = (
            datetime.strftime(t["deadline"], "%A, %d %B %Y, %H:%M")
            if t["deadline"] else "-"
        )
        t["created_display"] = (
            datetime.strftime(t["created_at"], "%A, %d %B %Y, %H:%M")
            if t.get("created_at") else "-"
        )

    cursor.close()
    conn.close()

    return jsonify({
        "course_code": course_code,
        "course_name": course["course_name"],
        "modules": [
            {
                "id": "tugas_terbaru",
                "name": f"Daftar Tugas Terbaru - {course['course_name']}",
                "tasks": [
                    {
                        "title": t["title"],
                        "description": t["description"],
                        "open": t["created_display"],
                        "due": t["deadline_display"]
                    }
                    for t in tasks
                ]
            }
        ]
    }), 200



@app.route("/api/task", methods=["POST"])
def add_task():
    data = request.get_json()
    print("Data received:", data)  # Tambahkan logging untuk debugging
    
    course_code = data.get("course_code")
    title = data.get("title")
    description = data.get("description", "")
    deadline = data.get("deadline")
    file_json = data.get("file", "[]")

    # Validasi course_code
    if not course_code:
        return jsonify({"error": "course_code is required"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Koneksi database gagal"}), 500

    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO task (course_code, title, description, deadline, file) VALUES (%s, %s, %s, %s, %s)",
            (course_code, title, description, deadline, file_json)
        )
        conn.commit()
        task_id = cursor.lastrowid
        cursor.close()
        conn.close()
        return jsonify({"message": "Task berhasil ditambahkan", "task_id": task_id}), 201
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({"error": str(e)}), 500

@app.route("/api/task/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    data = request.get_json()
    title = data.get("title")
    description = data.get("description", "")
    deadline = data.get("deadline")
    file_json = data.get("file", "[]")

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Koneksi database gagal"}), 500

    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE task SET title=%s, description=%s, deadline=%s, file=%s WHERE id=%s",
            (title, description, deadline, file_json, task_id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "Task berhasil diperbarui"}), 200
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({"error": str(e)}), 500

@app.route("/api/task/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Koneksi database gagal"}), 500

    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM task WHERE id=%s", (task_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "Task berhasil dihapus"}), 200
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({"error": str(e)}), 500

@app.route("/api/upload-task/<int:task_id>", methods=["POST"])
def upload_task(task_id):
    # Periksa apakah user sudah login dan role-nya mahasiswa
    if "role" not in session or session["role"] != "mahasiswa":
        return jsonify({"error": "Unauthorized"}), 401
    
    # Ambil ID mahasiswa dari session
    mahasiswa_id = session.get("user_id")
    if not mahasiswa_id:
        return jsonify({"error": "Mahasiswa ID not found in session"}), 400
    
    # Periksa apakah task ada
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Koneksi database gagal"}), 500
    
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM task WHERE id=%s", (task_id,))
    task = cursor.fetchone()
    
    if not task:
        cursor.close()
        conn.close()
        return jsonify({"error": "Task not found"}), 404
    
    # Periksa apakah mahasiswa terdaftar di course yang memiliki task ini
    cursor.execute(
        "SELECT * FROM mahasiswa_courses WHERE mahasiswa_id=%s AND course_code=%s",
        (mahasiswa_id, task["course_code"])
    )
    enrollment = cursor.fetchone()
    
    if not enrollment:
        cursor.close()
        conn.close()
        return jsonify({"error": "Anda tidak terdaftar di course ini"}), 403
    
    # Simpan file upload (simulasi)
    # Dalam implementasi nyata, Anda akan menyimpan file ke sistem file atau cloud storage
    file_data = request.files.get("file")
    if not file_data:
        cursor.close()
        conn.close()
        return jsonify({"error": "No file uploaded"}), 400
    
    # Simpan informasi upload ke database
    try:
        # Simpan file ke folder uploads
        file_path = os.path.join(UPLOAD_FOLDER, f"{mahasiswa_id}_{task_id}_{file_data.filename}")
        file_data.save(file_path)
        
        # Simpan ke database
        cursor.execute(
            "INSERT INTO task_submissions (task_id, mahasiswa_id, file_path) VALUES (%s, %s, %s)",
            (task_id, mahasiswa_id, file_path)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "File uploaded successfully"}), 200
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({"error": str(e)}), 500
    

@app.route("/dosen_dashboard", methods=["GET", "POST"])
def get_dosen():
    if request.method == "POST":
        data = request.get_json()
        nama = data.get("nama")
        course_name = data.get("course_name")
        course_code = generate_course_code()

        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Koneksi database gagal"}), 500

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO courses (course_code, nama, course_name) VALUES (%s, %s, %s)",
            (course_code, nama, course_name)
        )
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"message": "Course Berhasil Ditambahkan!!", "course_code": course_code})

    if request.args.get("data") == "true":
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Koneksi database gagal"}), 500

        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM courses")
        data = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(data)

    return render_template("index.html")

@app.route("/api/delete-course/<string:course_code>", methods=["DELETE"])
def delete_course(course_code):
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Koneksi database gagal"}), 500

    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM mahasiswa_courses WHERE course_code = %s", (course_code,))
        cursor.execute("DELETE FROM courses WHERE course_code = %s", (course_code,))
        conn.commit()

        cursor.close()
        conn.close()    
        return jsonify({"message": f"Course dengan code {course_code} berhasil dihapus!"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/user")
def get_user():
    if "username" in session:
        return jsonify({
            "name": session.get("name"),
            "username": session.get("username"),
            "role": session.get("role"),
            "user_id": session.get("user_id")
        })
    return jsonify({"error": "Unauthorized"}), 401

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)