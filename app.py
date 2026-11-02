from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import sqlite3
from database import init_db, get_db
from recommender import get_recommendations

app = Flask(__name__)
app.secret_key = "change-this-later"

init_db()

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login first.")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper

@app.route("/")
def home():
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        if not name or not email or len(password) < 6:
            flash("Ellaa fields-um fill pannunga. Password minimum 6 characters.")
            return render_template("register.html")

        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                (name, email, generate_password_hash(password)),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            flash("Indha email already register aagiduchu.")
            return render_template("register.html")
        finally:
            conn.close()

        flash("Registration successful! Ippo login pannunga.")
        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            return redirect(url_for("dashboard"))

        flash("Email illa password thappu.")
    return render_template("login.html")

@app.route("/dashboard")
@login_required
def dashboard():
    recs = get_recommendations(session["user_id"])
    return render_template("dashboard.html", name=session["user_name"], recs=recs)

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    conn = get_db()

    if request.method == "POST":
        department = request.form["department"].strip()
        year = request.form["year"]

        if not department or year not in ("1", "2", "3", "4"):
            flash("Department-um year-um correct-ah kudunga.")
        else:
            conn.execute(
                """INSERT INTO student_profiles (user_id, department, year)
                   VALUES (?, ?, ?)
                   ON CONFLICT(user_id) DO UPDATE SET
                   department = excluded.department, year = excluded.year""",
                (session["user_id"], department, int(year)),
            )
            conn.commit()
            flash("Profile updated!")

    user = conn.execute(
        "SELECT name, email, created_at FROM users WHERE id = ?",
        (session["user_id"],),
    ).fetchone()
    details = conn.execute(
        "SELECT department, year FROM student_profiles WHERE user_id = ?",
        (session["user_id"],),
    ).fetchone()

    # Real quiz stats
    stats = conn.execute(
        "SELECT COUNT(*) AS n, AVG(score * 100.0 / total) AS avg FROM attempts WHERE user_id = ?",
        (session["user_id"],),
    ).fetchone()
    conn.close()

    total_quizzes = stats["n"]
    avg_score = round(stats["avg"], 1) if stats["avg"] is not None else 0

    return render_template(
        "profile.html",
        user=user,
        details=details,
        total_quizzes=total_quizzes,
        avg_score=avg_score,
    )

# ---------------- QUIZ MODULE ----------------

@app.route("/quiz")
@login_required
def quiz_topics():
    conn = get_db()
    topics = conn.execute("SELECT id, name FROM topics ORDER BY name").fetchall()
    conn.close()
    return render_template("quiz_topics.html", topics=topics)

@app.route("/quiz/<int:topic_id>", methods=["GET", "POST"])
@login_required
def quiz(topic_id):
    conn = get_db()
    topic = conn.execute("SELECT * FROM topics WHERE id = ?", (topic_id,)).fetchone()
    if topic is None:
        conn.close()
        flash("Topic kidaikala.")
        return redirect(url_for("quiz_topics"))

    if request.method == "POST":
        # Indha topic-oda questions mattum check pannum
        rows = conn.execute("SELECT * FROM questions WHERE topic_id = ?", (topic_id,)).fetchall()
        by_id = {q["id"]: q for q in rows}

        qids = [int(i) for i in request.form.getlist("qid") if i.isdigit() and int(i) in by_id]
        if not qids:
            conn.close()
            flash("Quiz data sariyilla. Marubadi try pannunga.")
            return redirect(url_for("quiz_topics"))

        score = 0
        results = []
        for qid in qids:
            selected = request.form.get(f"q_{qid}")  # answer pannalana None
            if selected not in ("A", "B", "C", "D"):
                selected = None
            correct = 1 if selected == by_id[qid]["correct_option"] else 0
            score += correct
            results.append((qid, selected, correct))

        cur = conn.execute(
            "INSERT INTO attempts (user_id, topic_id, score, total) VALUES (?, ?, ?, ?)",
            (session["user_id"], topic_id, score, len(qids)),
        )
        attempt_id = cur.lastrowid
        for qid, selected, correct in results:
            conn.execute(
                "INSERT INTO answers (attempt_id, question_id, selected_option, is_correct) VALUES (?, ?, ?, ?)",
                (attempt_id, qid, selected, correct),
            )
        conn.commit()
        conn.close()
        return redirect(url_for("result", attempt_id=attempt_id))

    # GET: suggested difficulty questions mudhalil edukkum
    difficulty = request.args.get("difficulty")
    if difficulty not in ("easy", "medium", "hard"):
        difficulty = None

    if difficulty:
        # Kammiya irundha matha difficulty-la irundhu fill aagum
        questions = conn.execute(
            """SELECT * FROM questions WHERE topic_id = ?
               ORDER BY (difficulty = ?) DESC, RANDOM() LIMIT 5""",
            (topic_id, difficulty),
        ).fetchall()
    else:
        questions = conn.execute(
            "SELECT * FROM questions WHERE topic_id = ? ORDER BY RANDOM() LIMIT 5",
            (topic_id,),
        ).fetchall()
    conn.close()

    if not questions:
        flash("Indha topic-la innum questions illa.")
        return redirect(url_for("quiz_topics"))

    return render_template("quiz.html", topic=topic, questions=questions, difficulty=difficulty)

@app.route("/result/<int:attempt_id>")
@login_required
def result(attempt_id):
    conn = get_db()
    # Ungal attempt mattum paakka mudiyum
    attempt = conn.execute(
        """SELECT a.*, t.name AS topic_name FROM attempts a
           JOIN topics t ON t.id = a.topic_id
           WHERE a.id = ? AND a.user_id = ?""",
        (attempt_id, session["user_id"]),
    ).fetchone()
    if attempt is None:
        conn.close()
        flash("Result kidaikala.")
        return redirect(url_for("quiz_topics"))

    rows = conn.execute(
        """SELECT q.question, q.option_a, q.option_b, q.option_c, q.option_d,
                  q.correct_option, ans.selected_option, ans.is_correct
           FROM answers ans JOIN questions q ON q.id = ans.question_id
           WHERE ans.attempt_id = ?""",
        (attempt_id,),
    ).fetchall()
    conn.close()

    percent = round(attempt["score"] * 100 / attempt["total"], 1)
    return render_template("result.html", attempt=attempt, rows=rows, percent=percent)

# ---------------- PERFORMANCE TRACKING ----------------

@app.route("/performance")
@login_required
def performance():
    conn = get_db()
    # Ovvoru topic-kum ungal total attempts, correct answers, total questions
    rows = conn.execute(
        """SELECT t.name AS topic, COUNT(*) AS attempts,
                  SUM(a.score) AS correct, SUM(a.total) AS total
           FROM attempts a JOIN topics t ON t.id = a.topic_id
           WHERE a.user_id = ?
           GROUP BY t.id
           ORDER BY t.name""",
        (session["user_id"],),
    ).fetchall()

    # Line chart-ku: ovvoru quiz-oda score order-la
    history = conn.execute(
        """SELECT t.name AS topic, a.score, a.total
           FROM attempts a JOIN topics t ON t.id = a.topic_id
           WHERE a.user_id = ?
           ORDER BY a.taken_at, a.id""",
        (session["user_id"],),
    ).fetchall()
    conn.close()

    topic_stats = []
    for r in rows:
        accuracy = round(r["correct"] * 100 / r["total"], 1)

        # Weak / Average / Strong decide panra rule
        if accuracy < 60:
            level = "Weak"
        elif accuracy >= 80:
            level = "Strong"
        else:
            level = "Average"

        topic_stats.append({
            "topic": r["topic"],
            "attempts": r["attempts"],
            "correct": r["correct"],
            "total": r["total"],
            "accuracy": accuracy,
            "level": level,
        })

    topic_labels = [s["topic"] for s in topic_stats]
    topic_accuracy = [s["accuracy"] for s in topic_stats]
    history_labels = [f"Quiz {i + 1} ({h['topic']})" for i, h in enumerate(history)]
    history_scores = [round(h["score"] * 100 / h["total"], 1) for h in history]

    return render_template(
        "performance.html",
        topic_stats=topic_stats,
        topic_labels=topic_labels,
        topic_accuracy=topic_accuracy,
        history_labels=history_labels,
        history_scores=history_scores,
    )

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)