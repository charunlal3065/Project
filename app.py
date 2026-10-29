from flask import Flask, render_template, request, redirect, session
import mysql.connector
import pickle
import numpy as np
import os

app = Flask(__name__)
app.secret_key = "student_secret_key"

import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="sklearn")
warnings.filterwarnings("ignore", module="sklearn.base", message="Trying to unpickle estimator")

db_config = {
    "host": "127.0.0.1",
    "port": 3307,
    "user": "root",
    "password": "123456",
    "database": "educate_db2"
}

# ── DB pool: lazily created on first use ────────────────────────────────────
_db_pool = None

def get_db_pool():
    global _db_pool
    if _db_pool is None:
        try:
            _db_pool = mysql.connector.pooling.MySQLConnectionPool(
                pool_name="educate_pool",
                pool_size=5,
                pool_reset_session=True,
                **db_config
            )
            print("[INFO] MySQL connection pool created successfully.")
        except mysql.connector.Error as e:
            print(f"[ERROR] Cannot connect to MySQL: {e}")
            print("[ERROR] Make sure MySQL is running on port 3307 and 'educate_db2' exists.")
            raise
    return _db_pool

# Custom classes to load RandomForestRegressor and DecisionTreeRegressor
# without importing scikit-learn binary DLLs (which may be blocked by system policies)
class MockDecisionTreeRegressor:
    def __init__(self):
        pass
    def __setstate__(self, state):
        self.__dict__.update(state)

class MockRandomForestRegressor:
    def __init__(self):
        pass
    def __setstate__(self, state):
        self.__dict__.update(state)

class CustomUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        if module.startswith("sklearn.ensemble"):
            if "RandomForestRegressor" in name:
                return MockRandomForestRegressor
        elif module.startswith("sklearn.tree") and name == "DecisionTreeRegressor":
            return MockDecisionTreeRegressor
        return super().find_class(module, name)

class PurePythonRandomForestRegressor:
    def __init__(self, trees):
        self.trees = trees
        
    def predict(self, X):
        preds = []
        for x in X:
            tree_preds = []
            for tree in self.trees:
                left = tree["children_left"]
                right = tree["children_right"]
                feat = tree["feature"]
                thresh = tree["threshold"]
                val = tree["value"]
                
                node = 0
                while left[node] != -1:
                    if x[feat[node]] <= thresh[node]:
                        node = left[node]
                    else:
                        node = right[node]
                tree_preds.append(val[node, 0, 0])
            preds.append(np.mean(tree_preds))
        return np.array(preds)

def load_pure_model(path):
    with open(path, "rb") as f:
        m = CustomUnpickler(f).load()
    trees = []
    for est in m.estimators_:
        t = est.tree_
        trees.append({
            "children_left": t.children_left,
            "children_right": t.children_right,
            "feature": t.feature,
            "threshold": t.threshold,
            "value": t.value
        })
    return PurePythonRandomForestRegressor(trees)

# ── Model: lazily loaded on first prediction request ────────────────────────
_model = None
_model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "model", "student_performance.pkl")

def get_model():
    global _model
    if _model is None:
        print("[INFO] Loading ML model (this may take a moment)...")
        _model = load_pure_model(_model_path)
        print("[INFO] ML model loaded successfully.")
    return _model

def get_db():
    return get_db_pool().get_connection()

def get_user_data(username):
    try:
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        
        # First retrieve user_id
        cur.execute("SELECT user_id FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        if not user:
            cur.close()
            conn.close()
            return [], {"total": 0, "avg": 0, "high_risk": 0}
            
        user_id = user["user_id"]
        
        # Fetch prediction history
        cur.execute(
            """
            SELECT study_hours, attendance, online_courses, assignment_completion, stress_level, predicted_score, created_at
            FROM predictions
            WHERE user_id = %s
            ORDER BY created_at DESC
            """,
            (user_id,)
        )
        history = cur.fetchall()
        
        cur.close()
        conn.close()
        
        # Calculate stats
        total = len(history)
        if total > 0:
            avg = round(sum(row["predicted_score"] for row in history) / total, 2)
            high_risk = sum(1 for row in history if row["predicted_score"] < 60)
        else:
            avg = 0
            high_risk = 0
            
        stats = {
            "total": total,
            "avg": avg,
            "high_risk": high_risk
        }
        return history, stats
    except Exception as e:
        print("Database error in get_user_data:", e)
        return [], {"total": 0, "avg": 0, "high_risk": 0}

@app.route("/")
def index():
    return render_template("landing.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        try:
            conn = get_db()
            cur = conn.cursor()

            cur.execute(
                "INSERT INTO users(username,email,password) VALUES(%s,%s,%s)",
                (username, email, password)
            )

            conn.commit()
            cur.close()
            conn.close()

            return redirect("/login")
        except mysql.connector.Error as e:
            # Handle duplicate entry (Error 1062)
            if e.errno == 1062:
                return render_template("signup.html", error="Username or email already exists!")
            else:
                return render_template("signup.html", error="An error occurred during registration.")

    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()
        cur = conn.cursor(dictionary=True)

        cur.execute(
            "SELECT * FROM users WHERE email=%s AND password=%s",
            (email, password)
        )

        user = cur.fetchone()

        cur.close()
        conn.close()

        if user:
            session["username"] = user["username"]
            session["user_id"] = user["user_id"]

            # Record login event in login_history table
            try:
                conn_log = get_db()
                cur_log = conn_log.cursor()
                ip_addr = request.remote_addr or '127.0.0.1'
                cur_log.execute(
                    """
                    INSERT INTO login_history (user_id, username, login_time, ip_address, status)
                    VALUES (%s, %s, NOW(), %s, 'ACTIVE')
                    """,
                    (user["user_id"], user["username"], ip_addr)
                )
                conn_log.commit()
                session["session_id"] = cur_log.lastrowid
                cur_log.close()
                conn_log.close()
            except Exception as e:
                print("Error recording login_history:", e)

            return redirect("/dashboard")

        return render_template("login.html", error="Invalid email or password")

    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "username" not in session or "user_id" not in session:
        return redirect("/login")

    history, stats = get_user_data(session["username"])
    prediction = None
    graph_data = None
    if history:
        latest = history[0]
        prediction = round(float(latest["predicted_score"]), 2)
        graph_data = [
            float(latest["study_hours"]),
            float(latest["attendance"]),
            float(latest["online_courses"]),
            float(latest["assignment_completion"]),
            float(latest["stress_level"]),
            float(latest["predicted_score"])
        ]
    return render_template(
        "dashboard.html",
        username=session["username"],
        history=history,
        stats=stats,
        prediction=prediction,
        graph_data=graph_data
    )

@app.route("/predict", methods=["POST"])
def predict():
    if "username" not in session or "user_id" not in session:
        return redirect("/login")

    try:
        study_hours = float(request.form["StudyHours"])
        attendance = float(request.form["Attendance"])
        online_courses = float(request.form["OnlineCourses"])
        assignment = float(request.form["AssignmentCompletion"])
        stress = float(request.form["StressLevel"])
    except (KeyError, ValueError) as e:
        history, stats = get_user_data(session["username"])
        return render_template(
            "dashboard.html",
            username=session["username"],
            error="Please fill in all input fields with valid numbers.",
            history=history,
            stats=stats
        )

    input_data = np.array([[study_hours, attendance, online_courses, assignment, stress]])
    prediction = get_model().predict(input_data)[0]

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO predictions
        (user_id, study_hours, attendance, online_courses, assignment_completion, stress_level, predicted_score)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
        """,
        (session["user_id"], study_hours, attendance, online_courses, assignment, stress, float(prediction))
    )

    conn.commit()
    cur.close()
    conn.close()

    # Recalculate and update individual_performance summary
    try:
        conn_perf = get_db()
        cur_perf = conn_perf.cursor(dictionary=True)
        cur_perf.execute("SELECT predicted_score FROM predictions WHERE user_id = %s", (session["user_id"],))
        all_scores = [r["predicted_score"] for r in cur_perf.fetchall()]
        if all_scores:
            tot = len(all_scores)
            avg_score = round(sum(all_scores) / tot, 2)
            hi_score = round(max(all_scores), 2)
            lo_score = round(min(all_scores), 2)
            risk = 'High Risk' if avg_score < 60 else ('Moderate Risk' if avg_score < 75 else 'Low Risk')

            cur_perf.execute(
                """
                INSERT INTO individual_performance (user_id, total_scenarios_run, average_predicted_score, highest_score, lowest_score, risk_level)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    total_scenarios_run = VALUES(total_scenarios_run),
                    average_predicted_score = VALUES(average_predicted_score),
                    highest_score = VALUES(highest_score),
                    lowest_score = VALUES(lowest_score),
                    risk_level = VALUES(risk_level)
                """,
                (session["user_id"], tot, avg_score, hi_score, lo_score, risk)
            )
            conn_perf.commit()
        cur_perf.close()
        conn_perf.close()
    except Exception as e:
        print("Error updating individual_performance:", e)

    history, stats = get_user_data(session["username"])
    graph_data = [study_hours, attendance, online_courses, assignment, stress, float(prediction)]

    return render_template(
        "dashboard.html",
        username=session["username"],
        prediction=round(float(prediction), 2),
        graph_data=graph_data,
        history=history,
        stats=stats
    )

@app.route("/logout")
def logout():
    session_id = session.get("session_id")
    if session_id:
        try:
            conn_log = get_db()
            cur_log = conn_log.cursor()
            cur_log.execute(
                """
                UPDATE login_history
                SET exit_time = NOW(), status = 'LOGGED_OUT'
                WHERE session_id = %s
                """,
                (session_id,)
            )
            conn_log.commit()
            cur_log.close()
            conn_log.close()
        except Exception as e:
            print("Error recording logout exit timing:", e)

    session.clear()
    return redirect("/login")

@app.route('/favicon.ico')
def favicon():
    return "", 204

if __name__ == "__main__":
    print("[INFO] Starting Educate Flask app...")
    print("[INFO] Visit http://127.0.0.1:5000 in your browser.")
    app.run(debug=True, use_reloader=False)