from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
import json
from datetime import datetime
import logging

# Setup logging
logger = logging.getLogger(__name__)

router = APIRouter()

# Models
class HealthParameter(BaseModel):
    name: str
    value: Any
    unit: Optional[str] = None

class RiskFactor(BaseModel):
    factor: str
    value: float
    recommendation: str

class RiskAssessmentRequest(BaseModel):
    age: int = Field(..., gt=0, lt=120, example=35)
    gender: str = Field(..., example="male")
    height: float = Field(..., gt=0, example=175.0)  # in cm
    weight: float = Field(..., gt=0, example=70.0)  # in kg
    systolic_bp: Optional[int] = Field(None, gt=0, example=120)  # systolic blood pressure
    diastolic_bp: Optional[int] = Field(None, gt=0, example=80)  # diastolic blood pressure
    cholesterol: Optional[float] = Field(None, ge=0, example=180.0)  # total cholesterol
    hdl: Optional[float] = Field(None, ge=0, example=50.0)  # HDL cholesterol
    ldl: Optional[float] = Field(None, ge=0, example=100.0)  # LDL cholesterol
    triglycerides: Optional[float] = Field(None, ge=0, example=150.0)
    fasting_glucose: Optional[float] = Field(None, ge=0, example=85.0)
    smoking: bool = Field(False, example=False)
    alcohol_consumption: Optional[str] = Field(None, example="moderate")
    exercise_minutes_per_week: Optional[int] = Field(None, ge=0, example=150)
    family_history: Optional[Dict[str, bool]] = Field(None, example={"heart_disease": True, "diabetes": False})
    chronic_conditions: Optional[List[str]] = Field(None, example=["asthma"])
    medications: Optional[List[str]] = Field(None, example=["ibuprofen"])
    sleep_hours: Optional[float] = Field(None, ge=0, le=24, example=7.5)
    stress_level: Optional[int] = Field(None, ge=0, le=10, example=5)
    
    class Config:
        schema_extra = {
            "example": {
                "age": 35,
                "gender": "male",
                "height": 175.0,
                "weight": 70.0,
                "systolic_bp": 120,
                "diastolic_bp": 80,
                "cholesterol": 180.0,
                "hdl": 50.0,
                "ldl": 100.0,
                "triglycerides": 150.0,
                "fasting_glucose": 85.0,
                "smoking": False,
                "alcohol_consumption": "moderate",
                "exercise_minutes_per_week": 150,
                "family_history": {"heart_disease": True, "diabetes": False},
                "chronic_conditions": ["asthma"],
                "medications": ["ibuprofen"],
                "sleep_hours": 7.5,
                "stress_level": 5
            }
        }

class RiskAssessmentResponse(BaseModel):
    bmi: float
    bmi_category: str
    health_age: Optional[int] = None
    overall_risk_score: float
    risk_categories: Dict[str, Dict[str, Any]]
    recommendations: List[str]
    next_steps: List[str]
    
    class Config:
        schema_extra = {
            "example": {
                "bmi": 22.9,
                "bmi_category": "Normal weight",
                "health_age": 33,
                "overall_risk_score": 25.0,
                "risk_categories": {
                    "cardiovascular": {
                        "risk_score": 2,
                        "risk_level": "Low",
                        "risk_factors": []
                    },
                    "metabolic": {
                        "risk_score": 1,
                        "risk_level": "Low",
                        "risk_factors": []
                    }
                },
                "recommendations": [
                    "Maintain your current healthy lifestyle",
                    "Regular check-ups are recommended"
                ],
                "next_steps": [
                    "Consult with a healthcare provider to discuss these results",
                    "Set up regular health check-ups"
                ]
            }
        }

# Helper functions for risk assessment calculations
def calculate_bmi(weight: float, height: float) -> float:
    """Calculate BMI (weight in kg, height in cm)"""
    height_m = height / 100  # Convert cm to meters
    return round(weight / (height_m * height_m), 1)

def get_bmi_category(bmi: float) -> str:
    """Determine BMI category"""
    if bmi < 18.5:
        return "Underweight"
    elif bmi < 25:
        return "Normal weight"
    elif bmi < 30:
        return "Overweight"
    else:
        return "Obesity"

def calculate_cardiovascular_risk(data: RiskAssessmentRequest) -> Dict[str, Any]:
    """Calculate cardiovascular risk based on input parameters"""
    risk_score = 0
    risk_factors = []
    
    # Age factor
    if data.age > 55:
        risk_score += 2
        risk_factors.append({
            "factor": "Age",
            "value": data.age,
            "recommendation": "Age is a non-modifiable risk factor. Focus on other health parameters."
        })
    
    # Blood pressure factor
    if data.systolic_bp and data.systolic_bp > 140:
        risk_score += 3
        risk_factors.append({
            "factor": "High Blood Pressure",
            "value": data.systolic_bp,
            "recommendation": "Consider dietary changes and regular monitoring."
        })
    
    # Cholesterol factors
    if data.cholesterol and data.cholesterol > 200:
        risk_score += 2
        risk_factors.append({
            "factor": "High Total Cholesterol",
            "value": data.cholesterol,
            "recommendation": "Limit saturated fats and increase physical activity."
        })
    
    # Smoking factor
    if data.smoking:
        risk_score += 4
        risk_factors.append({
            "factor": "Smoking",
            "value": 1.0,  # Converted to float for type consistency
            "recommendation": "Quitting smoking significantly reduces cardiovascular risk."
        })
    
    return {
        "risk_score": risk_score,
        "risk_level": "High" if risk_score > 5 else "Moderate" if risk_score > 2 else "Low",
        "risk_factors": risk_factors
    }

def calculate_metabolic_risk(data: RiskAssessmentRequest) -> Dict[str, Any]:
    """Calculate metabolic risk based on input parameters"""
    risk_score = 0
    risk_factors = []
    
    # BMI factor
    bmi = calculate_bmi(data.weight, data.height)
    if bmi > 30:
        risk_score += 3
        risk_factors.append({
            "factor": "Obesity", 
            "value": float(bmi),  # Ensure it's a float
            "recommendation": "Focus on weight management through diet and exercise."
        })
    elif bmi > 25:
        risk_score += 1
        risk_factors.append({
            "factor": "Overweight",
            "value": float(bmi),  # Ensure it's a float
            "recommendation": "Modest weight loss can improve metabolic health."
        })
    
    # Glucose factor
    if data.fasting_glucose and data.fasting_glucose > 100:
        risk_score += 2
        risk_factors.append({
            "factor": "Elevated Fasting Glucose",
            "value": float(data.fasting_glucose),  # Ensure it's a float
            "recommendation": "Monitor blood sugar and consider dietary adjustments."
        })
    
    return {
        "risk_score": risk_score,
        "risk_level": "High" if risk_score > 4 else "Moderate" if risk_score > 1 else "Low",
        "risk_factors": risk_factors
    }

# Endpoints
@router.post("/assess", response_model=RiskAssessmentResponse)
async def assess_health_risks(data: RiskAssessmentRequest = Body(...)):
    """
    Assess health risks based on provided health parameters.
    Returns risk scores, categories, and recommendations.
    """
    try:
        logger.info(f"Processing risk assessment request for age: {data.age}, gender: {data.gender}")
        
        # Calculate BMI
        bmi = calculate_bmi(data.weight, data.height)
        bmi_category = get_bmi_category(bmi)
        
        # Calculate different risk categories
        cardiovascular_risk = calculate_cardiovascular_risk(data)
        metabolic_risk = calculate_metabolic_risk(data)
        
        # Calculate overall risk score (weighted average of category risks)
        category_weights = {
            "cardiovascular": 0.4,
            "metabolic": 0.3,
            # Add more categories with their weights if needed
        }
        
        category_scores = {
            "cardiovascular": cardiovascular_risk["risk_score"],
            "metabolic": metabolic_risk["risk_score"],
            # Add more category scores if needed
        }
        
        sum_weights = sum(category_weights.values())
        if sum_weights > 0:  # Prevent division by zero
            overall_score = sum(
                category_scores[cat] * weight 
                for cat, weight in category_weights.items()
            ) / sum_weights
        else:
            overall_score = 0
        
        # Scale to 0-100
        normalized_score = min(100, max(0, overall_score * 10))
        
        # Generate recommendations based on risk factors
        all_risk_factors = cardiovascular_risk["risk_factors"] + metabolic_risk["risk_factors"]
        recommendations = [factor["recommendation"] for factor in all_risk_factors]
        
        # Add general recommendations based on the profile
        if data.exercise_minutes_per_week is None or data.exercise_minutes_per_week < 150:
            recommendations.append("Aim for at least 150 minutes of moderate exercise per week.")
        
        if not recommendations:  # If no specific recommendations
            recommendations.append("Maintain your current healthy lifestyle.")
            recommendations.append("Regular check-ups are recommended.")
        
        # Next steps
        next_steps = [
            "Consult with a healthcare provider to discuss these results",
            "Set up regular health check-ups",
            "Track your progress using our health tracker"
        ]
        
        # Calculate health age (simplified algorithm)
        health_age = data.age
        if bmi > 30:
            health_age += 5
        if data.smoking:
            health_age += 7
        if data.exercise_minutes_per_week and data.exercise_minutes_per_week > 150:
            health_age -= 3
        
        # Compile the response
        response = RiskAssessmentResponse(
            bmi=bmi,
            bmi_category=bmi_category,
            health_age=health_age,
            overall_risk_score=float(normalized_score),  # Ensure it's a float
            risk_categories={
                "cardiovascular": cardiovascular_risk,
                "metabolic": metabolic_risk,
                # Add more categories if needed
            },
            recommendations=list(set(recommendations)),  # Remove duplicates
            next_steps=next_steps
        )
        
        logger.info(f"Risk assessment completed successfully, overall score: {normalized_score}")
        return response
        
    except Exception as e:
        logger.error(f"Error in risk assessment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing risk assessment: {str(e)}")

@router.get("/factors")
async def get_risk_factors():
    """Get a list of all risk factors that can be assessed."""
    return {
        "risk_factors": [
            {
                "id": "bmi",
                "name": "Body Mass Index",
                "description": "A measure of body fat based on height and weight",
                "input_parameters": ["height", "weight"]
            },
            {
                "id": "blood_pressure",
                "name": "Blood Pressure",
                "description": "The pressure of blood against the walls of arteries",
                "input_parameters": ["systolic_bp", "diastolic_bp"]
            },
            {
                "id": "cholesterol",
                "name": "Cholesterol Levels",
                "description": "Levels of lipids in the blood",
                "input_parameters": ["cholesterol", "hdl", "ldl", "triglycerides"]
            },
            # Add more risk factors
        ]
    }

@router.get("/recommendations/{risk_factor}")
async def get_recommendations_for_risk_factor(risk_factor: str):
    """Get detailed recommendations for a specific risk factor."""
    recommendations = {
        "bmi": {
            "underweight": [
                "Consult with a nutritionist for a healthy weight gain plan",
                "Focus on nutrient-dense foods",
                "Include strength training in your exercise routine"
            ],
            "normal": [
                "Maintain your current healthy habits",
                "Regular exercise and balanced diet"
            ],
            "overweight": [
                "Aim for 150-300 minutes of moderate exercise per week",
                "Focus on portion control",
                "Increase intake of fruits, vegetables and whole grains"
            ],
            "obesity": [  
                "Consult with healthcare provider for a personalized weight management plan",
                "Set realistic weight loss goals (1-2 pounds per week)",
                "Consider keeping a food and activity journal"
            ]
        },
        "blood_pressure": {
            "normal": [
                "Maintain healthy lifestyle habits",
                "Check blood pressure annually"
            ],
            "elevated": [
                "Reduce sodium intake",
                "Regular physical activity",
                "Monitor blood pressure monthly"
            ],
            "high": [
                "Consult with a healthcare provider",
                "DASH diet (Dietary Approaches to Stop Hypertension)",
                "Limit alcohol consumption",
                "Stress management techniques"
            ]
        }
        # Add more risk factors and their recommendations
    }
    
    if risk_factor not in recommendations:
        raise HTTPException(status_code=404, detail=f"Risk factor '{risk_factor}' not found")
    
    return {"risk_factor": risk_factor, "recommendations": recommendations[risk_factor]}

@router.post("/save-assessment")
async def save_assessment(assessment_data: Dict[str, Any] = Body(...)):
    """Save a completed risk assessment result."""
    # In a real application, this would save to a database
    # Here we'll just acknowledge the save
    
    # Generate a unique ID for this assessment
    assessment_id = f"assessment_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    return {
        "message": "Assessment saved successfully",
        "assessment_id": assessment_id,
        "timestamp": datetime.now().isoformat()
    }
