from database import get_db, init_db

init_db()

data = {
    "Python": [
        ("Which keyword defines a function in Python?", "func", "def", "function", "define", "B", "easy"),
        ("What is the output of len([1, 2, 3])?", "2", "3", "4", "Error", "B", "easy"),
        ("Which data type is immutable?", "list", "dict", "tuple", "set", "C", "easy"),
        ("What does the // operator do?", "Float division", "Floor division", "Modulus", "Power", "B", "medium"),
        ("Which block is used to handle exceptions?", "try-except", "if-else", "for-while", "switch", "A", "easy"),
    ],
    "C": [
        ("Which operator gives the address of a variable?", "*", "&", "#", "@", "B", "easy"),
        ("Typical size of int on modern compilers?", "2 bytes", "4 bytes", "8 bytes", "1 byte", "B", "medium"),
        ("Which function prints output in C?", "cout", "print", "printf", "echo", "C", "easy"),
        ("Array index in C starts from?", "0", "1", "-1", "Depends", "A", "easy"),
        ("Header file needed for printf?", "stdlib.h", "stdio.h", "string.h", "math.h", "B", "easy"),
    ],
    "Java": [
        ("Which keyword is used for inheritance?", "implements", "extends", "inherits", "super", "B", "easy"),
        ("Which method is the entry point of a Java program?", "main", "start", "run", "init", "A", "easy"),
        ("Which of these is NOT a primitive type?", "int", "boolean", "String", "char", "C", "medium"),
        ("JVM stands for?", "Java Virtual Machine", "Java Variable Method", "Joint Virtual Machine", "Java Verified Module", "A", "easy"),
        ("Which keyword prevents a method from being overridden?", "static", "final", "const", "abstract", "B", "medium"),
    ],
    "DBMS": [
        ("Which SQL command retrieves data?", "INSERT", "SELECT", "UPDATE", "DELETE", "B", "easy"),
        ("A primary key must be?", "Nullable", "Duplicate", "Unique and not null", "Multiple per table", "C", "easy"),
        ("Purpose of normalization?", "Increase redundancy", "Reduce redundancy", "Slow queries", "Delete data", "B", "medium"),
        ("Which is a DDL command?", "SELECT", "INSERT", "CREATE", "UPDATE", "C", "medium"),
        ("In ACID, 'A' stands for?", "Atomicity", "Accuracy", "Availability", "Authorization", "A", "medium"),
    ],
}

conn = get_db()
for topic, questions in data.items():
    conn.execute("INSERT OR IGNORE INTO topics (name) VALUES (?)", (topic,))
    topic_id = conn.execute("SELECT id FROM topics WHERE name = ?", (topic,)).fetchone()["id"]

    # Already questions irundha thirumba add aagaadhu
    count = conn.execute("SELECT COUNT(*) FROM questions WHERE topic_id = ?", (topic_id,)).fetchone()[0]
    if count == 0:
        for q in questions:
            conn.execute(
                """INSERT INTO questions
                   (topic_id, question, option_a, option_b, option_c, option_d, correct_option, difficulty)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (topic_id, *q),
            )
conn.commit()
conn.close()
print("Seed data added.")