DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS diet_log;
DROP TABLE IF EXISTS exercise_log;
DROP TABLE IF EXISTS weight_log;

CREATE TABLE user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    age INTEGER,
    gender TEXT,
    height REAL, -- in cm
    weight REAL, -- in kg
    activity_level TEXT, -- sedentary, lightly_active, moderately_active, very_active, extra_active
    goal TEXT, -- lose, maintain, gain
    target_calories INTEGER
);

CREATE TABLE diet_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    meal_type TEXT NOT NULL, -- breakfast, lunch, dinner, snack
    food_name TEXT NOT NULL,
    calories INTEGER NOT NULL,
    log_date DATE DEFAULT (DATE('now')),
    FOREIGN KEY (user_id) REFERENCES user (id)
);

CREATE TABLE exercise_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    exercise_name TEXT NOT NULL,
    duration_minutes INTEGER NOT NULL,
    calories_burned INTEGER,
    log_date DATE DEFAULT (DATE('now')),
    FOREIGN KEY (user_id) REFERENCES user (id)
);

CREATE TABLE weight_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    weight REAL NOT NULL,
    log_date DATE DEFAULT (DATE('now')),
    FOREIGN KEY (user_id) REFERENCES user (id)
);
