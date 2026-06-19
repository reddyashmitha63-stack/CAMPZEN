from flask import Flask, request, render_template, redirect, url_for
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)

# ================= DATABASE =================
def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="campzen"
        )
        return conn
    except Error as e:
        print("Database Connection Error:", e)
        return None


# ================= AUTH =================
@app.route("/")
def home():
    return render_template("login1.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (email, password) VALUES (%s, %s)",
                (email, password)
            )
            conn.commit()
            cursor.close()
            conn.close()

        return redirect(url_for("home"))

    return render_template("signup.html")


@app.route("/login1", methods=["POST"])
def login1():
    email = request.form["email"]
    password = request.form["password"]

    conn = get_db_connection()
    if not conn:
        return "Database error. Try again."

    cursor = conn.cursor(dictionary=True, buffered=True)
    cursor.execute(
        "SELECT * FROM users WHERE email=%s AND password=%s",
        (email, password)
    )
    user = cursor.fetchone()

    cursor.close()
    conn.close()

    if user:
        return redirect(url_for("dashboard"))
    else:
        return "Invalid Login"


# ================= DASHBOARD =================
@app.route("/dashboard")
def dashboard():
    return render_template("dashboard1.html")


# ================= CANTEEN =================
@app.route("/canteen")
def canteen():
    return render_template("canteen.html")


@app.route("/place_order", methods=["POST"])
def place_order():
    idli = int(request.form.get("idli", 0))
    dosa = int(request.form.get("dosa", 0))
    samosa = int(request.form.get("samosa", 0))
    biryani = int(request.form.get("biryani", 0))
    payment_method = request.form["payment_method"]

    total = idli*30 + dosa*50 + samosa*20 + biryani*100

    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO orders 
            (idli, dosa, samosa, biryani, total_amount, payment_method)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (idli, dosa, samosa, biryani, total, payment_method))
        conn.commit()
        cursor.close()
        conn.close()

    return f"Order placed successfully! ₹{total}"


# ================= FORUM =================
@app.route("/forum")
def forum():
    conn = get_db_connection()
    if not conn:
        return "Database error"

    cursor = conn.cursor(dictionary=True, buffered=True)
    cursor.execute("SELECT * FROM questions ORDER BY created_at DESC")
    questions = cursor.fetchall()

    for q in questions:
        cursor.execute(
            "SELECT * FROM replies WHERE question_id=%s ORDER BY created_at ASC",
            (q["id"],)
        )
        q["replies"] = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("forum.html", questions=questions)


@app.route("/add_question", methods=["POST"])
def add_question():
    question = request.form["question"]

    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO questions (question) VALUES (%s)",
            (question,)
        )
        conn.commit()
        cursor.close()
        conn.close()

    return redirect(url_for("forum"))


@app.route("/add_reply/<int:question_id>", methods=["POST"])
def add_reply(question_id):
    reply = request.form["reply"]

    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO replies (question_id, reply) VALUES (%s, %s)",
            (question_id, reply)
        )
        conn.commit()
        cursor.close()
        conn.close()

    return redirect(url_for("forum"))


# ================= BOOKING =================
@app.route("/booking", methods=["GET", "POST"])
def booking_page():

    message = None

    conn = get_db_connection()
    if not conn:
        return "Database error"

    cursor = conn.cursor(dictionary=True, buffered=True)

    if request.method == "POST":
        date = request.form["date"]
        time = request.form["time"]
        classroom = request.form.get("classroom")
        lab = request.form.get("lab")

        resource = classroom if classroom else lab

        if not resource:
            message = "Please select a resource!"
        else:
            cursor.execute("""
                SELECT * FROM bookings
                WHERE date=%s AND time_slot=%s AND resource=%s
            """, (date, time, resource))

            if cursor.fetchone():
                message = "Already booked!"
            else:
                cursor.execute("""
                    INSERT INTO bookings (date, time_slot, resource)
                    VALUES (%s, %s, %s)
                """, (date, time, resource))
                conn.commit()
                message = "Booking successful!"

    cursor.execute("SELECT * FROM bookings ORDER BY id DESC")
    bookings = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("booking.html", message=message, bookings=bookings)


# ================= LOST & FOUND =================
@app.route("/lost_found")
def lost_found():
    conn = get_db_connection()
    if not conn:
        return "Database error"

    cursor = conn.cursor(dictionary=True, buffered=True)
    cursor.execute("SELECT * FROM lost_found ORDER BY created_at DESC")
    posts = cursor.fetchall()

    for p in posts:
        cursor.execute(
            "SELECT * FROM lost_found_replies WHERE post_id=%s ORDER BY created_at ASC",
            (p["id"],)
        )
        p["replies"] = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("lost_found.html", posts=posts)


@app.route("/add_lost_post", methods=["POST"])
def add_lost_post():
    type = request.form["type"]
    description = request.form["description"]
    location = request.form["location"]

    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO lost_found (type, description, location) VALUES (%s, %s, %s)",
            (type, description, location)
        )
        conn.commit()
        cursor.close()
        conn.close()

    return redirect(url_for("lost_found"))


@app.route("/add_lost_reply/<int:post_id>", methods=["POST"])
def add_lost_reply(post_id):
    reply = request.form["reply"]

    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO lost_found_replies (post_id, reply) VALUES (%s, %s)",
            (post_id, reply)
        )
        conn.commit()
        cursor.close()
        conn.close()

    return redirect(url_for("lost_found"))


# ================= NOTICE BOARD =================
@app.route("/notice")
def notice():
    conn = get_db_connection()
    if not conn:
        return "Database error"

    cursor = conn.cursor(dictionary=True, buffered=True)
    cursor.execute("SELECT * FROM notices ORDER BY created_at DESC")
    notices = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("notice.html", notices=notices)


@app.route("/add_notice", methods=["POST"])
def add_notice():
    title = request.form["title"]
    content = request.form["content"]

    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO notices (title, content) VALUES (%s, %s)",
            (title, content)
        )
        conn.commit()
        cursor.close()
        conn.close()

    return redirect(url_for("notice"))


# ================= FEEDBACK =================
@app.route("/feedback", methods=["GET", "POST"])
def feedback():
    if request.method == "POST":
        category = request.form["category"]
        message = request.form["message"]

        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO feedback (category, message) VALUES (%s, %s)",
                (category, message)
            )
            conn.commit()
            cursor.close()
            conn.close()

        return "Feedback submitted successfully!"

    return render_template("feedback.html")


# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True, port=8000)