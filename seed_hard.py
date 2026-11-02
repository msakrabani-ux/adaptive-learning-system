from database import get_db, init_db

init_db()

# (question, A, B, C, D, correct)
hard = {
    "Python": [
        ("What is the output of print(2 ** 3 ** 2)?", "64", "512", "36", "128", "B"),
        ("What does [1, 2, 3][::-1] return?", "[1, 2, 3]", "[3, 2, 1]", "[2, 1]", "Error", "B"),
        ("What is the output of bool('False')?", "False", "True", "Error", "None", "B"),
        ("Which keyword is used to create a generator function?", "return", "yield", "generate", "async", "B"),
    ],
    "C": [
        ("Which storage class keeps its value between function calls?", "auto", "register", "static", "extern", "C"),
        ("What does malloc return when memory allocation fails?", "0 as int", "NULL", "-1", "Garbage value", "B"),
        ("What is the value of 5 / 2 in C when both are integers?", "2.5", "2", "3", "2.0", "B"),
        ("What is sizeof(int *) on a 64-bit system?", "4", "8", "2", "16", "B"),
    ],
    "Java": [
        ("Which collection does not allow duplicate elements?", "List", "Set", "ArrayList", "Vector", "B"),
        ("What is the output of System.out.println(10 == 10.0)?", "true", "false", "Compile error", "10", "A"),
        ("Which block always executes after try-catch?", "catch", "finally", "throw", "throws", "B"),
        ("Which statement about String in Java is true?", "Mutable", "Immutable", "Primitive type", "Not an object", "B"),
    ],
    "DBMS": [
        ("Which normal form removes partial dependency?", "1NF", "2NF", "3NF", "BCNF", "B"),
        ("Which join returns all rows from the left table?", "INNER JOIN", "LEFT JOIN", "CROSS JOIN", "SELF JOIN", "B"),
        ("Which clause filters groups after GROUP BY?", "WHERE", "HAVING", "ORDER BY", "LIMIT", "B"),
        ("Which ACID property ensures committed data survives a crash?", "Atomicity", "Consistency", "Isolation", "Durability", "D"),
    ],
}

conn = get_db()
added = 0
for topic, questions in hard.items():
    row = conn.execute("SELECT id FROM topics WHERE name = ?", (topic,)).fetchone()
    if row is None:
        continue
    for q in questions:
        # Already irundha thirumba add aagaadhu
        exists = conn.execute(
            "SELECT 1 FROM questions WHERE topic_id = ? AND question = ?",
            (row["id"], q[0]),
        ).fetchone()
        if not exists:
            conn.execute(
                """INSERT INTO questions
                   (topic_id, question, option_a, option_b, option_c, option_d, correct_option, difficulty)
                   VALUES (?, ?, ?, ?, ?, ?, ?, 'hard')""",
                (row["id"], *q),
            )
            added += 1
conn.commit()
conn.close()
print(f"{added} hard questions added.")