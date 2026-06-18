from app import db
from datetime import datetime
import bcrypt
import jwt
import os

class User(db.Model):
    __tablename__ = 'users'
    
    user_id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer)
    gender = db.Column(db.Enum('Male', 'Female', 'Other'))
    height = db.Column(db.Float)  # in cm
    weight = db.Column(db.Float)  # in kg
    bmi = db.Column(db.Float)
    activity_level = db.Column(db.Enum('Sedentary', 'Lightly Active', 'Moderately Active', 'Active'))
    goal = db.Column(db.Enum('Weight Loss', 'Muscle Gain', 'Balanced Diet', 'Maintenance'))
    medical_history = db.Column(db.Text)
    allergies = db.Column(db.Text)
    daily_calorie_target = db.Column(db.Integer)
    protein_target = db.Column(db.Integer)
    carbs_target = db.Column(db.Integer)
    fat_target = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    diet_plans = db.relationship('DietPlan', backref='user', lazy=True, cascade='all, delete-orphan')
    exercise_logs = db.relationship('ExerciseLog', backref='user', lazy=True, cascade='all, delete-orphan')
    chat_history = db.relationship('ChatHistory', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash password before storing"""
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password):
        """Verify password"""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    def generate_token(self):
        """Generate JWT token"""
        payload = {
            'user_id': self.user_id,
            'email': self.email,
            'exp': datetime.utcnow() + datetime.timedelta(days=7)
        }
        return jwt.encode(payload, os.getenv('SECRET_KEY', 'nutriguide-secret-key-2025'), algorithm='HS256')
    
    def calculate_bmi(self):
        """Calculate BMI"""
        if self.height and self.weight:
            height_m = self.height / 100  # convert cm to meters
            self.bmi = round(self.weight / (height_m ** 2), 2)
            return self.bmi
        return None
    
    def calculate_calorie_needs(self):
        """Calculate daily calorie needs using Mifflin-St Jeor equation"""
        if not all([self.age, self.gender, self.height, self.weight]):
            return None
        
        # Convert height to cm if needed
        height_cm = self.height
        
        # Mifflin-St Jeor equation
        if self.gender == 'Male':
            bmr = 10 * self.weight + 6.25 * height_cm - 5 * self.age + 5
        else:  # Female or Other
            bmr = 10 * self.weight + 6.25 * height_cm - 5 * self.age - 161
        
        # Activity multipliers
        activity_factors = {
            'Sedentary': 1.2,
            'Lightly Active': 1.375,
            'Moderately Active': 1.55,
            'Active': 1.725
        }
        
        daily_calories = bmr * activity_factors.get(self.activity_level, 1.2)
        
        # Adjust for goals
        goal_factors = {
            'Weight Loss': 0.85,
            'Muscle Gain': 1.15,
            'Balanced Diet': 1.0,
            'Maintenance': 1.0
        }
        
        daily_calories *= goal_factors.get(self.goal, 1.0)
        
        # Calculate macronutrients (40% carbs, 30% protein, 30% fat)
        self.daily_calorie_target = int(daily_calories)
        self.protein_target = int((daily_calories * 0.3) / 4)  # 4 calories per gram
        self.carbs_target = int((daily_calories * 0.4) / 4)   # 4 calories per gram
        self.fat_target = int((daily_calories * 0.3) / 9)     # 9 calories per gram
        
        return self.daily_calorie_target

class DietPlan(db.Model):
    __tablename__ = 'diet_plans'
    
    plan_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    plan_date = db.Column(db.Date, nullable=False)
    meal_type = db.Column(db.Enum('Breakfast', 'Lunch', 'Dinner', 'Snack'))
    meal_name = db.Column(db.String(100))
    description = db.Column(db.Text)
    calories = db.Column(db.Integer)
    protein = db.Column(db.Float)
    carbs = db.Column(db.Float)
    fat = db.Column(db.Float)
    food_items = db.Column(db.JSON)
    is_completed = db.Column(db.Boolean, default=False)

class ExerciseLog(db.Model):
    __tablename__ = 'exercise_logs'
    
    log_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    exercise_date = db.Column(db.Date, nullable=False)
    exercise_type = db.Column(db.String(50))
    duration_minutes = db.Column(db.Integer)
    calories_burned = db.Column(db.Integer)
    intensity = db.Column(db.Enum('Low', 'Medium', 'High'))
    notes = db.Column(db.Text)

class ChatHistory(db.Model):
    __tablename__ = 'chat_history'
    
    chat_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    user_message = db.Column(db.Text)
    ai_response = db.Column(db.Text)
    message_type = db.Column(db.Enum('symptom', 'diet', 'exercise', 'general'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)