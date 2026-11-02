from database import get_db

WEAK_LIMIT = 60     # accuracy idhukku keezha na Weak
STRONG_LIMIT = 80   # accuracy idhukku mela na Strong

def pick_difficulty(last_percent):
    """Last quiz score padi adutha difficulty."""
    if last_percent > 80:
        return "hard"
    if last_percent < 50:
        return "easy"
    return "medium"

def get_recommendations(user_id):
    conn = get_db()
    topics = conn.execute("SELECT id, name FROM topics ORDER BY name").fetchall()
    recs = []

    for t in topics:
        rows = conn.execute(
            """SELECT score, total FROM attempts
               WHERE user_id = ? AND topic_id = ?
               ORDER BY taken_at, id""",
            (user_id, t["id"]),
        ).fetchall()

        # Innum attempt pannala
        if not rows:
            recs.append({
                "topic_id": t["id"],
                "topic": t["name"],
                "accuracy": None,
                "level": "New",
                "priority": 2,
                "difficulty": "easy",
                "reason": f"You have not tried {t['name']} yet. Start with an easy quiz to find your level.",
            })
            continue

        correct = sum(r["score"] for r in rows)
        total = sum(r["total"] for r in rows)
        accuracy = round(correct * 100 / total, 1)

        last = rows[-1]
        last_percent = round(last["score"] * 100 / last["total"], 1)
        difficulty = pick_difficulty(last_percent)

        if accuracy < WEAK_LIMIT:
            level = "Weak"
            priority = 1
            reason = (f"Your accuracy in {t['name']} is {accuracy}%, which is below {WEAK_LIMIT}%. "
                      f"Your last score was {last_percent}%, so a {difficulty} quiz is suggested.")
        elif accuracy >= STRONG_LIMIT:
            level = "Strong"
            priority = 4
            reason = (f"You are doing well in {t['name']} ({accuracy}%). "
                      f"Your last score was {last_percent}%, so try a {difficulty} quiz to stay sharp.")
        else:
            level = "Average"
            priority = 3
            reason = (f"Your accuracy in {t['name']} is {accuracy}%. "
                      f"Your last score was {last_percent}%, so a {difficulty} quiz will help you improve.")

        recs.append({
            "topic_id": t["id"],
            "topic": t["name"],
            "accuracy": accuracy,
            "level": level,
            "priority": priority,
            "difficulty": difficulty,
            "reason": reason,
        })

    conn.close()

    # Weak first, then New, Average, Strong. Same level-la kuraivaana accuracy mudhalil
    recs.sort(key=lambda r: (r["priority"], r["accuracy"] if r["accuracy"] is not None else 0))
    return recs