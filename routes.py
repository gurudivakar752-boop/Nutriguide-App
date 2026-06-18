from flask import Blueprint, request, jsonify
from app import db
from app.models import User, DietPlan, ExerciseLog, ChatHistory
from app.ai_service import AIService
from functools import wraps
import jwt
import os
from datetime import datetime, timedelta

main_bp = Blueprint('main', __name__, url_prefix='/api/v1')
ai_service = AIService()

# Authentication decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]
        
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        
        try:
            data = jwt.decode(token, os.getenv('SECRET_KEY', 'nutriguide-secret-key-2025'), algorithms=['HS256'])
            current_user = User.query.get(data['user_id'])
        except:
            return jsonify({'message': 'Token is invalid!'}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

@main_bp.route('/')
def index():
    return jsonify({'message': 'NutriGuide API v1.0', 'status': 'running'})

# Authentication Routes
@main_bp.route('/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # Check if user exists
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'User already exists!'}), 400
    
    # Create new user
    user = User(
        email=data['email'],
        name=data['name'],
        age=data.get('age'),
        gender=data.get('gender'),
        height=data.get('height'),
        weight=data.get('weight'),
        activity_level=data.get('activity_level', 'Moderately Active'),
        goal=data.get('goal', 'Balanced Diet'),
        medical_history=data.get('medical_history'),
        allergies=data.get('allergies')
    )
    
    user.set_password(data['password'])
    user.calculate_bmi()
    user.calculate_calorie_needs()
    
    db.session.add(user)
    db.session.commit()
    
    token = user.generate_token()
    
    return jsonify({
        'message': 'User registered successfully!',
        'token': token,
        'user': {
            'id': user.user_id,
            'name': user.name,
            'email': user.email,
            'bmi': user.bmi,
            'daily_calorie_target': user.daily_calorie_target
        }
    }), 201

@main_bp.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    
    user = User.query.filter_by(email=data['email']).first()
    
    if not user or not user.check_password(data['password']):
        return jsonify({'message': 'Invalid credentials!'}), 401
    
    token = user.generate_token()
    
    return jsonify({
        'message': 'Login successful!',
        'token': token,
        'user': {
            'id': user.user_id,
            'name': user.name,
            'email': user.email,
            'bmi': user.bmi,
            'daily_calorie_target': user.daily_calorie_target
        }
    })

# User Profile Routes
@main_bp.route('/user/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    return jsonify({
        'user': {
            'id': current_user.user_id,
            'name': current_user.name,
            'email': current_user.email,
            'age': current_user.age,
            'gender': current_user.gender,
            'height': current_user.height,
            'weight': current_user.weight,
            'bmi': current_user.bmi,
            'activity_level': current_user.activity_level,
            'goal': current_user.goal,
            'medical_history': current_user.medical_history,
            'allergies': current_user.allergies,
            'daily_calorie_target': current_user.daily_calorie_target,
            'protein_target': current_user.protein_target,
            'carbs_target': current_user.carbs_target,
            'fat_target': current_user.fat_target
        }
    })

@main_bp.route('/user/profile', methods=['PUT'])
@token_required
def update_profile(current_user):
    data = request.get_json()
    
    # Update user fields
    updatable_fields = ['name', 'age', 'gender', 'height', 'weight', 
                       'activity_level', 'goal', 'medical_history', 'allergies']
    
    for field in updatable_fields:
        if field in data:
            setattr(current_user, field, data[field])
    
    # Recalculate BMI and calorie needs
    current_user.calculate_bmi()
    current_user.calculate_calorie_needs()
    
    db.session.commit()
    
    return jsonify({
        'message': 'Profile updated successfully!',
        'bmi': current_user.bmi,
        'daily_calorie_target': current_user.daily_calorie_target
    })

# Diet Plan Routes
@main_bp.route('/diet/generate', methods=['POST'])
@token_required
def generate_diet_plan(current_user):
    data = request.get_json()
    days = data.get('days', 7)
    
    # Get user data for AI
    user_data = {
        'age': current_user.age,
        'gender': current_user.gender,
        'weight': current_user.weight,
        'height': current_user.height,
        'activity_level': current_user.activity_level,
        'goal': current_user.goal,
        'daily_calorie_target': current_user.daily_calorie_target,
        'allergies': current_user.allergies,
        'medical_history': current_user.medical_history
    }
    
    # Generate diet plan using AI
    ai_result = ai_service.generate_diet_plan(user_data, current_user.goal)
    
    if ai_result['success']:
        # Save diet plan to database
        today = datetime.today().date()
        for i in range(days):
            plan_date = today + timedelta(days=i)
            
            # Create sample meals for the day
            meals = [
                ('Breakfast', 'Healthy Breakfast', 400),
                ('Lunch', 'Balanced Lunch', 500),
                ('Dinner', 'Light Dinner', 450),
                ('Snack', 'Evening Snack', 200)
            ]
            
            for meal_type, meal_name, calories in meals:
                diet_plan = DietPlan(
                    user_id=current_user.user_id,
                    plan_date=plan_date,
                    meal_type=meal_type,
                    meal_name=meal_name,
                    calories=calories,
                    protein=calories * 0.3 / 4,
                    carbs=calories * 0.4 / 4,
                    fat=calories * 0.3 / 9,
                    food_items=['Item1', 'Item2', 'Item3']
                )
                db.session.add(diet_plan)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Diet plan generated successfully!',
            'ai_plan': ai_result['diet_plan'],
            'meal_schedule': ai_result['meal_schedule']
        })
    else:
        return jsonify({
            'message': 'Generated basic diet plan',
            'plan': ai_result['fallback_plan']
        }), 200

@main_bp.route('/diet/plans', methods=['GET'])
@token_required
def get_diet_plans(current_user):
    date_str = request.args.get('date')
    
    if date_str:
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            plans = DietPlan.query.filter_by(
                user_id=current_user.user_id,
                plan_date=target_date
            ).order_by(DietPlan.meal_type).all()
        except:
            return jsonify({'message': 'Invalid date format!'}), 400
    else:
        # Get today's plans
        today = datetime.today().date()
        plans = DietPlan.query.filter_by(
            user_id=current_user.user_id,
            plan_date=today
        ).order_by(DietPlan.meal_type).all()
    
    plans_data = []
    for plan in plans:
        plans_data.append({
            'id': plan.plan_id,
            'date': plan.plan_date.isoformat(),
            'meal_type': plan.meal_type,
            'meal_name': plan.meal_name,
            'description': plan.description,
            'calories': plan.calories,
            'protein': plan.protein,
            'carbs': plan.carbs,
            'fat': plan.fat,
            'food_items': plan.food_items,
            'is_completed': plan.is_completed
        })
    
    return jsonify({'plans': plans_data})

# AI Health Assistant Routes
@main_bp.route('/ai/chat', methods=['POST'])
@token_required
def ai_chat(current_user):
    data = request.get_json()
    message = data.get('message', '')
    message_type = data.get('type', 'general')
    
    if not message:
        return jsonify({'message': 'Message is required!'}), 400
    
    # Get AI response
    context = {
        'user_id': current_user.user_id,
        'user_name': current_user.name,
        'user_goal': current_user.goal
    }
    
    ai_response = ai_service.chat_health_assistant(current_user.user_id, message, context)
    
    # Save chat history
    chat = ChatHistory(
        user_id=current_user.user_id,
        user_message=message,
        ai_response=ai_response['response'],
        message_type=message_type
    )
    db.session.add(chat)
    db.session.commit()
    
    return jsonify({
        'response': ai_response['response'],
        'suggestions': ai_response.get('suggestions', []),
        'chat_id': chat.chat_id
    })

@main_bp.route('/ai/symptoms', methods=['POST'])
@token_required
def check_symptoms(current_user):
    data = request.get_json()
    symptoms = data.get('symptoms', [])
    
    if not symptoms:
        return jsonify({'message': 'Symptoms are required!'}), 400
    
    # Prepare user data
    user_data = {
        'age': current_user.age,
        'gender': current_user.gender,
        'medical_history': current_user.medical_history
    }
    
    # Analyze symptoms
    analysis = ai_service.symptom_checker(symptoms, user_data)
    
    return jsonify({
        'analysis': analysis['analysis'],
        'severity': analysis['severity'],
        'recommendations': analysis.get('recommendations', {})
    })

# Exercise Routes
@main_bp.route('/exercise/log', methods=['POST'])
@token_required
def log_exercise(current_user):
    data = request.get_json()
    
    exercise_log = ExerciseLog(
        user_id=current_user.user_id,
        exercise_date=datetime.today().date(),
        exercise_type=data['exercise_type'],
        duration_minutes=data['duration_minutes'],
        calories_burned=data.get('calories_burned', 0),
        intensity=data.get('intensity', 'Medium'),
        notes=data.get('notes', '')
    )
    
    db.session.add(exercise_log)
    db.session.commit()
    
    return jsonify({
        'message': 'Exercise logged successfully!',
        'log_id': exercise_log.log_id
    })

@main_bp.route('/exercise/history', methods=['GET'])
@token_required
def get_exercise_history(current_user):
    days = request.args.get('days', 30, type=int)
    
    start_date = datetime.today().date() - timedelta(days=days)
    
    logs = ExerciseLog.query.filter(
        ExerciseLog.user_id == current_user.user_id,
        ExerciseLog.exercise_date >= start_date
    ).order_by(ExerciseLog.exercise_date.desc()).all()
    
    history = []
    for log in logs:
        history.append({
            'date': log.exercise_date.isoformat(),
            'type': log.exercise_type,
            'duration': log.duration_minutes,
            'calories': log.calories_burned,
            'intensity': log.intensity,
            'notes': log.notes
        })
    
    return jsonify({'history': history})

# Progress Tracking Routes
@main_bp.route('/progress/summary', methods=['GET'])
@token_required
def get_progress_summary(current_user):
    # Get today's date
    today = datetime.today().date()
    
    # Get today's diet plans
    today_plans = DietPlan.query.filter_by(
        user_id=current_user.user_id,
        plan_date=today
    ).all()
    
    # Calculate totals
    total_calories_consumed = sum(plan.calories for plan in today_plans if plan.is_completed)
    completed_meals = sum(1 for plan in today_plans if plan.is_completed)
    total_meals = len(today_plans)
    
    # Get today's exercise
    today_exercise = ExerciseLog.query.filter_by(
        user_id=current_user.user_id,
        exercise_date=today
    ).all()
    
    total_calories_burned = sum(ex.calories_burned for ex in today_exercise)
    total_exercise_minutes = sum(ex.duration_minutes for ex in today_exercise)
    
    # Calculate progress
    calorie_goal = current_user.daily_calorie_target or 2000
    calorie_progress = min(100, (total_calories_consumed / calorie_goal) * 100) if calorie_goal > 0 else 0
    
    return jsonify({
        'date': today.isoformat(),
        'calories': {
            'consumed': total_calories_consumed,
            'burned': total_calories_burned,
            'goal': calorie_goal,
            'progress': calorie_progress
        },
        'meals': {
            'completed': completed_meals,
            'total': total_meals,
            'progress': (completed_meals / total_meals * 100) if total_meals > 0 else 0
        },
        'exercise': {
            'minutes': total_exercise_minutes,
            'calories_burned': total_calories_burned,
            'goal': 30,  # 30 minutes exercise goal
            'progress': min(100, (total_exercise_minutes / 30) * 100)
        },
        'water': {
            'consumed': 1500,  # Mock data
            'goal': 2000,
            'progress': 75
        }
    })

# Notification Routes
@main_bp.route('/notifications/schedule', methods=['POST'])
@token_required
def schedule_notification(current_user):
    data = request.get_json()
    
    # In production, integrate with Firebase Cloud Messaging or similar
    notification_types = ['meal', 'medication', 'exercise', 'water', 'meditation']
    
    if data['type'] not in notification_types:
        return jsonify({'message': 'Invalid notification type!'}), 400
    
    # Store notification schedule in database (simplified)
    # In production, use a proper notifications table
    
    return jsonify({
        'message': 'Notification scheduled successfully!',
        'type': data['type'],
        'time': data['time'],
        'enabled': True
    })

# Error handlers
@main_bp.errorhandler(404)
def not_found(error):
    return jsonify({'message': 'Endpoint not found!'}), 404

@main_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'message': 'Internal server error!'}), 500