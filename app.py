import os
import sqlite3
import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

def get_db_connection():
    conn = sqlite3.connect('nutriguide.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    if not os.path.exists('nutriguide.db'):
        conn = get_db_connection()
        with open('database_schema.sql') as f:
            conn.executescript(f.read())
        conn.close()
        print("Initialized database.")

# --- Helpers ---
def calculate_bmr(weight, height, age, gender):
    # Mifflin-St Jeor
    if gender == 'male':
        return 10 * weight + 6.25 * height - 5 * age + 5
    else:
        return 10 * weight + 6.25 * height - 5 * age - 161

def calculate_tdee(bmr, activity_level):
    multipliers = {
        'sedentary': 1.2,
        'lightly_active': 1.375,
        'moderately_active': 1.55,
        'very_active': 1.725,
        'extra_active': 1.9
    }
    return bmr * multipliers.get(activity_level, 1.2)

def generate_daily_tasks(user_id, goal):
    conn = get_db_connection()
    today = datetime.date.today().isoformat()
    
    # Check if tasks exist for today
    existing = conn.execute('SELECT count(*) FROM daily_tasks WHERE user_id = ? AND created_date = ?', (user_id, today)).fetchone()[0]
    
    if existing == 0:
        tasks = [
            "Drink 2 liters of water",
            "Eat at least 3 servings of vegetables"
        ]
        
        if goal == 'lose':
            tasks.append("Do 20 mins of cardio")
            tasks.append("No sugar after 8 PM")
        elif goal == 'gain':
            tasks.append("Eat a high-protein snack")
            tasks.append("Do 30 mins of strength training")
        else:
            tasks.append("Walk 5,000 steps")
            
        for task in tasks:
            conn.execute('INSERT INTO daily_tasks (user_id, task_text) VALUES (?, ?)', (user_id, task))
        conn.commit()
    
    conn.close()

# --- Routes ---

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Simple validation
        if not username or not password:
            flash('Username and password are required.')
            return redirect(url_for('register'))

        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO user (username, password) VALUES (?, ?)',
                         (username, generate_password_hash(password)))
            conn.commit()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username already registered.')
        finally:
            conn.close()
            
    return render_template('register.html')

@app.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM user WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('dashboard'))
        else:
            flash('Incorrect username or password.')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM user WHERE id = ?', (session['user_id'],)).fetchone()
    
    # Generate tasks if needed
    generate_daily_tasks(user['id'], user['goal'])
    
    # Get tasks
    today = datetime.date.today().isoformat()
    tasks = conn.execute('SELECT * FROM daily_tasks WHERE user_id = ? AND created_date = ?', (user['id'], today)).fetchall()

    # Get today's stats
    calories_consumed = conn.execute('SELECT SUM(calories) FROM diet_log WHERE user_id = ? AND log_date = ?', 
                                   (session['user_id'], today)).fetchone()[0] or 0
    calories_burned = conn.execute('SELECT SUM(calories_burned) FROM exercise_log WHERE user_id = ? AND log_date = ?', 
                                 (session['user_id'], today)).fetchone()[0] or 0
    
    conn.close()
    
    return render_template('dashboard.html', 
                           user=user, 
                           tasks=tasks,
                           calories_consumed=calories_consumed, 
                           calories_burned=calories_burned)

@app.route('/profile', methods=('GET', 'POST'))
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    if request.method == 'POST':
        age = int(request.form['age'])
        gender = request.form['gender']
        height = float(request.form['height'])
        weight = float(request.form['weight'])
        activity = request.form['activity_level']
        goal = request.form['goal']
        
        # Calculate target calories
        bmr = calculate_bmr(weight, height, age, gender)
        tdee = calculate_tdee(bmr, activity)
        
        if goal == 'lose':
            target = tdee - 500
        elif goal == 'gain':
            target = tdee + 500
        else:
            target = tdee
            
        conn.execute('''
            UPDATE user 
            SET age = ?, gender = ?, height = ?, weight = ?, activity_level = ?, goal = ?, target_calories = ?
            WHERE id = ?
        ''', (age, gender, height, weight, activity, goal, int(target), session['user_id']))
        conn.commit()
        flash('Profile updated!')
        
    user = conn.execute('SELECT * FROM user WHERE id = ?', (session['user_id'],)).fetchone()
    conn.close()
    return render_template('profile.html', user=user)

@app.route('/toggle_task/<int:task_id>', methods=['POST'])
def toggle_task(task_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
        
    conn = get_db_connection()
    task = conn.execute('SELECT * FROM daily_tasks WHERE id = ? AND user_id = ?', (task_id, session['user_id'])).fetchone()
    
    if task:
        new_status = not task['is_completed']
        conn.execute('UPDATE daily_tasks SET is_completed = ? WHERE id = ?', (new_status, task_id))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'new_status': new_status})
    
    conn.close()
    return jsonify({'error': 'Task not found'}), 404

# --- Feature Placeholders & AI ---

@app.route('/ai-chat', methods=['POST'])
def ai_chat():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    user_message = data.get('message', '').lower()
    
    # Simple simulated AI response logic
    response = "I'm still learning, but keeping active and eating whole foods is always good!"
    
    if "hello" in user_message or "hi" in user_message:
        response = "Hello! How can I help you with your health goals today?"
    elif "weight" in user_message:
        response = "To manage weight effectively, aim for a balanced diet and regular exercise. Tracking your calories here is a great start!"
    elif "diet" in user_message or "food" in user_message:
        response = "Remember to include plenty of vegetables and protein in your meals. Need a specific recipe idea?"
    elif "exercise" in user_message or "workout" in user_message:
        response = "Regular movement is key. Even a 30-minute walk makes a difference!"
    
    return jsonify({'response': response})

@app.route('/diet')
def diet_plan():
    if 'user_id' not in session: return redirect(url_for('login'))
    return render_template('diet_plan.html')

@app.route('/exercises')
def exercises():
    if 'user_id' not in session: return redirect(url_for('login'))
    return render_template('exercises.html')

@app.route('/notifications')
def notifications():
    if 'user_id' not in session: return redirect(url_for('login'))
    return render_template('notifications.html')

@app.route('/progress')
def progress():
    if 'user_id' not in session: return redirect(url_for('login'))
    return render_template('progress.html')

@app.route('/ai_assistant')
def ai_assistant_page():
    if 'user_id' not in session: return redirect(url_for('login'))
    return render_template('ai_assistant.html')


if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
