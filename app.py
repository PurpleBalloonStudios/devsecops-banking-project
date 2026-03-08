from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "supersecretkey"


def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            password TEXT,
            role TEXT,
            balance INTEGER
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT,
            receiver TEXT,
            amount INTEGER
        )
    """)

    # Create default admin if not exists
    cursor.execute("""
        INSERT OR IGNORE INTO users (id, username, password, role, balance)
        VALUES (1, 'admin', 'admin123', 'admin', 0)
    """)

    conn.commit()
    conn.close()


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute(f"""
            INSERT INTO users (username, password, role, balance)
            VALUES ('{username}', '{password}', 'user', 1000)
        """)

        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute(f"""
            SELECT * FROM users
            WHERE username = '{username}' AND password = '{password}'
        """)

        user = cursor.fetchone()
        conn.close()

        if user:
            session["username"] = user[1]
            session["role"] = user[3]
            return redirect("/dashboard")

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(f"""
        SELECT balance FROM users
        WHERE username = '{session["username"]}'
    """)

    balance = cursor.fetchone()[0]
    conn.close()

    return render_template(
        "dashboard.html",
        username=session["username"],
        balance=balance,
        role=session["role"]
    )


@app.route("/transfer", methods=["POST"])
def transfer():
    if "username" not in session:
        return redirect("/login")

    sender = session["username"]
    receiver = request.form["receiver"]
    amount = int(request.form["amount"])

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(f"""
        UPDATE users SET balance = balance - {amount}
        WHERE username = '{sender}'
    """)

    cursor.execute(f"""
        UPDATE users SET balance = balance + {amount}
        WHERE username = '{receiver}'
    """)

    cursor.execute(f"""
        INSERT INTO transactions (sender, receiver, amount)
        VALUES ('{sender}', '{receiver}', {amount})
    """)

    conn.commit()
    conn.close()

    return redirect("/dashboard")


@app.route("/search", methods=["POST"])
def search():
    if "username" not in session:
        return redirect("/login")

    search_term = request.form["search"]

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(f"""
        SELECT username, balance FROM users
        WHERE username = '{search_term}'
    """)

    result = cursor.fetchone()
    conn.close()

    return render_template("search.html", result=result)


# 🔒 ADMIN PANEL
@app.route("/admin")
def admin():
    if "username" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return "Access Denied"

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT username, role, balance FROM users")
    users = cursor.fetchall()

    cursor.execute("SELECT sender, receiver, amount FROM transactions")
    transactions = cursor.fetchall()

    conn.close()

    return render_template(
        "admin.html",
        users=users,
        transactions=transactions
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
