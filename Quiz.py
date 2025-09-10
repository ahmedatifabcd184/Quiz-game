import os
import csv
import random
import datetime
from pathlib import Path

# ---------------------- CONFIG ----------------------
QUIZ_FOLDER = "quizzes"         # where subject files live
DATA_FOLDER = "data"            # where results.csv lives
RESULTS_FILE = os.path.join(DATA_FOLDER, "results.csv")
PASS_THRESHOLD = 60             # percent needed to pass (change as you like)
NUM_QUESTIONS = None            # set an integer to limit questions per quiz (e.g., 10); None = use all
# ----------------------------------------------------

def ensure_dirs():
    Path(QUIZ_FOLDER).mkdir(parents=True, exist_ok=True)
    Path(DATA_FOLDER).mkdir(parents=True, exist_ok=True)
    if not os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["date", "student", "subject", "score", "total", "percent"])

def list_subjects():
    files = [f for f in os.listdir(QUIZ_FOLDER) if f.endswith(".txt")]
    files.sort()
    return files

def load_questions(subject_file):
    """Returns list of (question, [A..D], correct_letter)"""
    questions = []
    with open(os.path.join(QUIZ_FOLDER, subject_file), "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split("|")
            if len(parts) != 6:
                print(f"⚠️ Skipping malformed line in {subject_file}: {line}")
                continue
            question = parts[0]
            options = parts[1:5]  # strings like "A) Text"
            correct = parts[5].strip().upper()
            # validate options labels
            if not all(opt.strip().startswith(lbl) for opt, lbl in zip(options, ["A)", "B)", "C)", "D)"])):
                print(f"⚠️ Bad option labels in {subject_file}: {line}")
                continue
            if correct not in ["A", "B", "C", "D"]:
                print(f"⚠️ Bad correct letter in {subject_file}: {line}")
                continue
            questions.append((question, options, correct))
    return questions

def shuffle_question(question_tuple):
    """Shuffle options while keeping track of correct letter."""
    question, options, correct = question_tuple
    # Map labels to text (without 'X) ')
    labeled = []
    for opt in options:
        label = opt[:2]  # "A)"
        text = opt[3:] if len(opt) > 3 else ""
        labeled.append((label[0], text))  # ("A","Option text")

    random.shuffle(labeled)

    # Rebuild options with new order and new labels A-D
    rebuilt = []
    new_correct_letter = None
    for i, (orig_letter, text) in enumerate(labeled):
        new_label = ["A", "B", "C", "D"][i]
        rebuilt.append(f"{new_label}) {text}")
        if orig_letter == correct:
            new_correct_letter = new_label

    return question, rebuilt, new_correct_letter

def take_quiz(student, subject_file):
    all_qs = load_questions(subject_file)
    if not all_qs:
        print("❌ No questions found for this subject.")
        return

    random.shuffle(all_qs)
    if NUM_QUESTIONS is not None:
        all_qs = all_qs[:NUM_QUESTIONS]

    score = 0
    total = len(all_qs)
    subject_name = subject_file.replace(".txt", "").replace("_", " ").title()

    print(f"\n🎯 Starting Quiz — {subject_name}\n(Pass threshold: {PASS_THRESHOLD}% )\n")

    for i, q in enumerate(all_qs, start=1):
        q_text, opts, correct = shuffle_question(q)
        print(f"Q{i}: {q_text}")
        for o in opts:
            print(o)
        ans = input("Your answer (A/B/C/D): ").strip().upper()

        while ans not in ["A", "B", "C", "D"]:
            ans = input("Please enter A/B/C/D: ").strip().upper()

        if ans == correct:
            print("✅ Correct!\n")
            score += 1
        else:
            print(f"❌ Wrong! Correct answer is {correct}.\n")

    percent = round(score * 100 / total, 2)
    status = "✅ PASSED" if percent >= PASS_THRESHOLD else "❌ FAILED"
    print(f"🏁 Result: {score}/{total}  ({percent}%)  → {status}")

    save_result(student, subject_name, score, total, percent)

def save_result(student, subject, score, total, percent):
    date = datetime.date.today().isoformat()
    with open(RESULTS_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([date, student, subject, score, total, percent])

def view_my_history(student):
    found = False
    print(f"\n📜 Results for: {student}")
    with open(RESULTS_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = [r for r in reader if r["student"] == student]
        if not rows:
            print("No attempts yet.")
            return
        found = True
        for r in rows:
            print(f"{r['date']} | {r['subject']} | {r['score']}/{r['total']} | {r['percent']}%")
    if found:
        # Show quick averages
        percents = [float(r["percent"]) for r in rows]
        avg = round(sum(percents) / len(percents), 2)
        best = max(percents)
        print(f"\n📊 Attempts: {len(rows)} | Avg: {avg}% | Best: {best}%")

def view_leaderboard(top_n=10, subject_filter=None):
    print("\n🏆 Leaderboard")
    with open(RESULTS_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if subject_filter:
        rows = [r for r in rows if r["subject"].lower() == subject_filter.lower()]

    # For leaderboard, we’ll rank by percent (desc), then by date (recent first)
    rows.sort(key=lambda r: (float(r["percent"]), r["date"]), reverse=True)

    if not rows:
        print("No results yet.")
        return

    print(f"{'Rank':<5}{'Date':<12}{'Student':<20}{'Subject':<22}{'Score':<9}{'Percent':<8}")
    for i, r in enumerate(rows[:top_n], start=1):
        print(f"{i:<5}{r['date']:<12}{r['student']:<20}{r['subject']:<22}{r['score']+'/'+r['total']:<9}{r['percent']+'%':<8}")

def choose_subject():
    subs = list_subjects()
    if not subs:
        print("❌ No subject files found in 'quizzes/'. Add .txt files first.")
        return None
    print("\n📚 Available Subjects:")
    for i, s in enumerate(subs, start=1):
        print(f"{i}. {s.replace('.txt','').replace('_',' ').title()}")
    ch = input("Choose a subject number: ").strip()
    if ch.isdigit() and 1 <= int(ch) <= len(subs):
        return subs[int(ch) - 1]
    print("❌ Invalid choice.")
    return None

def main_menu(student):
    while True:
        print("\n===== Quiz Menu =====")
        print("1) Take Quiz")
        print("2) My Results History")
        print("3) Leaderboard (Overall)")
        print("4) Leaderboard (By Subject)")
        print("5) Exit")
        choice = input("Choose an option: ").strip()

        if choice == "1":
            sub = choose_subject()
            if sub:
                take_quiz(student, sub)
        elif choice == "2":
            view_my_history(student)
        elif choice == "3":
            view_leaderboard()
        elif choice == "4":
            sub = choose_subject()
            if sub:
                subj_name = sub.replace(".txt", "").replace("_", " ").title()
                view_leaderboard(subject_filter=subj_name)
        elif choice == "5":
            print("Goodbye!")
            break
        else:
            print("❌ Invalid choice. Try again.")

def welcome():
    ensure_dirs()
    print("🎓 Study Assistant – MCQ Quiz System")
    print("Tip: Use a consistent student name/ID so your history stays together.")
    student = input("Enter your Name or Student ID: ").strip()
    if not student:
        student = "Anonymous"
    main_menu(student)

if __name__ == "__main__":
    welcome()
