import openai
import os
import json
from typing import Dict, List, Optional

class AIService:
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        if self.api_key:
            openai.api_key = self.api_key
    
    def generate_diet_plan(self, user_data: Dict, goal: str) -> Dict:
        """Generate personalized diet plan using AI"""
        prompt = f"""
        Generate a personalized diet plan for:
        - Age: {user_data.get('age')}
        - Gender: {user_data.get('gender')}
        - Weight: {user_data.get('weight')} kg
        - Height: {user_data.get('height')} cm
        - Activity Level: {user_data.get('activity_level')}
        - Goal: {goal}
        - Daily Calorie Target: {user_data.get('daily_calorie_target')}
        - Allergies: {user_data.get('allergies', 'None')}
        - Medical Conditions: {user_data.get('medical_history', 'None')}
        
        Please provide a detailed day's meal plan including:
        1. Breakfast
        2. Lunch
        3. Dinner
        4. 2 Snacks
        
        For each meal, include:
        - Meal name
        - Ingredients
        - Preparation instructions
        - Calories
        - Macronutrients (protein, carbs, fat)
        
        Ensure the plan is balanced, nutritious, and suitable for the user's goals.
        """
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a professional nutritionist and dietitian."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            return {
                "success": True,
                "diet_plan": response.choices[0].message.content,
                "meal_schedule": self._parse_meal_schedule(response.choices[0].message.content)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "fallback_plan": self._generate_fallback_plan(user_data, goal)
            }
    
    def chat_health_assistant(self, user_id: int, message: str, context: Dict = None) -> Dict:
        """AI Health Assistant Chat"""
        system_prompt = """
        You are NutriGuide AI, a professional health and nutrition assistant.
        Provide accurate, helpful, and safe health advice.
        Always recommend consulting a doctor for serious symptoms.
        Focus on nutrition, exercise, and lifestyle improvements.
        """
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            return {
                "success": True,
                "response": response.choices[0].message.content,
                "suggestions": self._extract_suggestions(response.choices[0].message.content)
            }
        except Exception as e:
            return {
                "success": False,
                "response": "I'm currently unavailable. Please try again later.",
                "error": str(e)
            }
    
    def symptom_checker(self, symptoms: List[str], user_data: Dict) -> Dict:
        """AI Symptom Checker"""
        symptom_text = ", ".join(symptoms)
        prompt = f"""
        User reports these symptoms: {symptom_text}
        
        User Profile:
        - Age: {user_data.get('age')}
        - Gender: {user_data.get('gender')}
        - Medical History: {user_data.get('medical_history', 'None')}
        
        Provide:
        1. Possible causes (common conditions)
        2. Recommended home remedies
        3. When to see a doctor
        4. Dietary recommendations
        5. Lifestyle adjustments
        """
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a medical assistant. Always advise seeing a doctor for serious symptoms."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.6,
                max_tokens=800
            )
            
            return {
                "success": True,
                "analysis": response.choices[0].message.content,
                "severity": self._assess_severity(symptoms),
                "recommendations": self._extract_recommendations(response.choices[0].message.content)
            }
        except Exception as e:
            return {
                "success": False,
                "analysis": "Unable to analyze symptoms at this time.",
                "severity": "Unknown",
                "error": str(e)
            }
    
    def _generate_fallback_plan(self, user_data: Dict, goal: str) -> Dict:
        """Generate basic diet plan without AI"""
        # Basic meal templates based on goals
        templates = {
            "Weight Loss": {
                "breakfast": "Oatmeal with berries (300 cal)",
                "lunch": "Grilled chicken salad (400 cal)",
                "dinner": "Baked fish with vegetables (450 cal)",
                "snacks": ["Greek yogurt (150 cal)", "Apple (95 cal)"]
            },
            "Muscle Gain": {
                "breakfast": "Protein smoothie with banana (450 cal)",
                "lunch": "Chicken rice bowl (600 cal)",
                "dinner": "Lean beef with sweet potato (550 cal)",
                "snacks": ["Protein bar (200 cal)", "Cottage cheese (180 cal)"]
            },
            "Balanced Diet": {
                "breakfast": "Whole grain toast with avocado (350 cal)",
                "lunch": "Quinoa salad with chickpeas (450 cal)",
                "dinner": "Salmon with broccoli and rice (500 cal)",
                "snacks": ["Mixed nuts (200 cal)", "Fruit salad (150 cal)"]
            }
        }
        
        return templates.get(goal, templates["Balanced Diet"])
    
    def _parse_meal_schedule(self, ai_response: str) -> List[Dict]:
        """Parse AI response into structured meal schedule"""
        # This is a simplified parser - in production, use more robust parsing
        meals = []
        lines = ai_response.split('\n')
        
        current_meal = None
        for line in lines:
            line = line.strip()
            if line.lower().startswith(('breakfast', 'lunch', 'dinner', 'snack')):
                if current_meal:
                    meals.append(current_meal)
                current_meal = {"name": line, "details": []}
            elif current_meal and line:
                current_meal["details"].append(line)
        
        if current_meal:
            meals.append(current_meal)
        
        return meals
    
    def _assess_severity(self, symptoms: List[str]) -> str:
        """Simple severity assessment"""
        severe_symptoms = ['chest pain', 'difficulty breathing', 'severe bleeding', 'loss of consciousness']
        moderate_symptoms = ['fever', 'persistent vomiting', 'severe headache']
        
        for symptom in symptoms:
            symptom_lower = symptom.lower()
            if any(severe in symptom_lower for severe in severe_symptoms):
                return "High - Seek immediate medical attention"
            elif any(moderate in symptom_lower for moderate in moderate_symptoms):
                return "Moderate - Consult a doctor"
        
        return "Low - Monitor and consider home care"
    
    def _extract_suggestions(self, response: str) -> List[str]:
        """Extract actionable suggestions from AI response"""
        suggestions = []
        lines = response.split('\n')
        
        for line in lines:
            if line.strip().startswith(('-', '•', '*', '1.', '2.', '3.')):
                suggestions.append(line.strip())
        
        return suggestions[:5]  # Return top 5 suggestions
    
    def _extract_recommendations(self, response: str) -> Dict:
        """Extract structured recommendations"""
        return {
            "dietary": [],
            "lifestyle": [],
            "medical": []
        }
    