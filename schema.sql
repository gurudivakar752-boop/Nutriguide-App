
CREATE DATABASE IF NOT EXISTS nutriguide_db;
USE nutriguide_db;


CREATE TABLE users (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    age INT,
    gender ENUM('Male', 'Female', 'Other'),
    height DECIMAL(5,2) COMMENT 'in cm',
    weight DECIMAL(5,2) COMMENT 'in kg',
    bmi DECIMAL(4,2),
    activity_level ENUM('Sedentary', 'Lightly Active', 'Moderately Active', 'Active'),
    goal ENUM('Weight Loss', 'Muscle Gain', 'Balanced Diet', 'Maintenance'),
    medical_history TEXT,
    allergies TEXT,
    daily_calorie_target INT,
    protein_target INT,
    carbs_target INT,
    fat_target INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Diet Plans Table
CREATE TABLE diet_plans (
    plan_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    plan_date DATE NOT NULL,
    meal_type ENUM('Breakfast', 'Lunch', 'Dinner', 'Snack'),
    meal_name VARCHAR(100),
    description TEXT,
    calories INT,
    protein DECIMAL(5,2),
    carbs DECIMAL(5,2),
    fat DECIMAL(5,2),
    food_items JSON,
    is_completed BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_user_date (user_id, plan_date)
);

-- Exercise Logs Table
CREATE TABLE exercise_logs (
    log_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    exercise_date DATE NOT NULL,
    exercise_type VARCHAR(50),
    duration_minutes INT,
    calories_burned INT,
    intensity ENUM('Low', 'Medium', 'High'),
    notes TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Water Intake Table
CREATE TABLE water_intake (
    intake_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    intake_date DATE NOT NULL,
    amount_ml INT DEFAULT 0,
    target_ml INT DEFAULT 2000,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Medication Reminders
CREATE TABLE medication_reminders (
    reminder_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    medication_name VARCHAR(100),
    dosage VARCHAR(50),
    frequency VARCHAR(50),
    time TIME,
    is_active BOOLEAN DEFAULT TRUE,
    last_taken TIMESTAMP NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Progress Reports
CREATE TABLE progress_reports (
    report_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    report_date DATE NOT NULL,
    weight DECIMAL(5,2),
    bmi DECIMAL(4,2),
    total_calories_consumed INT,
    total_calories_burned INT,
    water_intake_ml INT,
    exercise_minutes INT,
    notes TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Chat History for AI Assistant
CREATE TABLE chat_history (
    chat_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    user_message TEXT,
    ai_response TEXT,
    message_type ENUM('symptom', 'diet', 'exercise', 'general'),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Create indexes for performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_diet_user ON diet_plans(user_id);
CREATE INDEX idx_exercise_user ON exercise_logs(user_id);
CREATE INDEX idx_chat_user ON chat_history(user_id);