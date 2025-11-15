import os
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

students_data = []

def calculate_results(phy, chem, math, cs, eng):
    total = phy + chem + math + cs + eng
    percentage = (total / 500) * 100
    cgpa = round(total / 50, 2)
    if cgpa > 10:
        cgpa = 10.0
    if percentage >= 90:
        grade = "A+"
    elif percentage >= 80:
        grade = "A"
    elif percentage >= 70:
        grade = "B"
    elif percentage >= 60:
        grade = "C"
    elif percentage >= 50:
        grade = "D"
    else:
        grade = "F"
    return total, percentage, cgpa, grade

@app.route("/", methods=["GET"])
def home():
    sorted_students = sorted(students_data, key=lambda x: x["percentage"], reverse=True)
    return render_template("index.html", students=sorted_students)

@app.route("/add", methods=["POST"])
def add_student():
    try:
        name = request.form.get("name").strip()
        phy = int(request.form.get("physics") or 0)
        chem = int(request.form.get("chemistry") or 0)
        math = int(request.form.get("math") or 0)
        cs = int(request.form.get("cs") or 0)
        eng = int(request.form.get("english") or 0)

        for mark, subject in zip([phy, chem, math, cs, eng], ["Physics","Chemistry","Math","CS","English"]):
            if mark < 0 or mark > 100:
                return f"<h3>Error: Invalid marks for {subject}. Must be 0-100.</h3><a href='/'>Go Back</a>"

    except ValueError:
        return "<h3>Error: Invalid input. Enter numbers only.</h3><a href='/'>Go Back</a>"

    total, percentage, cgpa, grade = calculate_results(phy, chem, math, cs, eng)

    # Update if exists
    for s in students_data:
        if s["name"].lower() == name.lower():
            s.update({
                "physics": phy, "chemistry": chem, "math": math,
                "cs": cs, "english": eng,
                "total": total, "percentage": percentage,
                "cgpa": cgpa, "grade": grade
            })
            break
    else:
        students_data.append({
            "name": name, "physics": phy, "chemistry": chem, "math": math,
            "cs": cs, "english": eng,
            "total": total, "percentage": percentage,
            "cgpa": cgpa,
            "grade": grade
        })

    return redirect(url_for("home"))

@app.route("/clear", methods=["POST"])
def clear_all():
    if students_data:
        top_student = max(students_data, key=lambda x: x["percentage"])
        students_data.clear()
        students_data.append(top_student)
    return redirect(url_for("home"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
