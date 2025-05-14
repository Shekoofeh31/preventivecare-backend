from fastapi import APIRouter, HTTPException, BackgroundTasks, Request, Depends
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Union
import json
import os
import time
import traceback
from dotenv import load_dotenv
import logging
from openai import OpenAI
import httpx  # Import httpx

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize router
router = APIRouter(
    prefix="/api/symptom-checker",  # Add prefix to match API path
    tags=["Symptom Checker"],
    responses={404: {"description": "Not found"}},
)

# Check for OpenAI API key
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    logger.warning("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")

# Configure Proxies (if needed)
proxy_url = os.getenv("PROXY_URL")
proxies = None
if proxy_url:
    proxies = {
        "http": proxy_url,
        "https": proxy_url,
    }
    logger.info(f"Using proxy: {proxy_url}")
else:
    logger.info("No proxy configured.")

# Initialize httpx client with proxy settings
timeout = 30.0
transport = httpx.HTTPTransport()
http_client = httpx.Client(transport=transport, timeout=timeout)

# Initialize OpenAI client, passing the httpx client
client = OpenAI(api_key=openai_api_key, http_client=http_client)

# Simple helper functions
def sanitize_input(input_data):
    """Simple sanitization stub"""
    return input_data

def log_api_request(endpoint, status_code, processing_time):
    """Simple logging stub"""
    logger.info(f"API Request: {endpoint}, Status: {status_code}, Processing Time: {processing_time:.4f}s")

# Models
class SymptomRequest(BaseModel):
    age: int = Field(..., description="Patient's age")
    gender: str = Field(..., description="Patient's gender")
    symptoms: List[str] = Field(..., description="List of symptoms")
    medical_history: Optional[List[str]] = Field(default=[], description="Optional medical history")
    allergies: Optional[List[str]] = Field(default=[], description="Optional allergies")
    medications: Optional[List[str]] = Field(default=[], description="Optional medications")

class Condition(BaseModel):
    condition: str = Field(..., description="Name of the condition")
    probability: str = Field(..., description="Probability level (High/Medium/Low)")

class SymptomResponse(BaseModel):
    possible_conditions: List[Condition] = Field(..., description="List of possible conditions")
    recommendations: List[str] = Field(..., description="List of recommendations")
    severity_level: str = Field(..., description="Severity level (Low/Medium/High)")
    seek_medical_attention: bool = Field(..., description="Whether medical attention should be sought")

# Helper function to log symptom checks
async def log_symptom_check(age: int, gender: str):
    """Log symptom check details without storing personal information."""
    age_group = f"{age//10*10}s" if age >= 10 else "child"
    logger.info(f"Symptom check performed: Age group: {age_group}, Gender: {gender}")

def create_symptom_prompt(data: SymptomRequest) -> str:
    """Create a detailed prompt from the symptom data."""
    prompt = f"""
    Patient Information:
    - Age: {data.age}
    - Gender: {data.gender}
    - Symptoms: {', '.join(data.symptoms)}
    """

    if data.medical_history and len(data.medical_history) > 0:
        prompt += f"- Medical History: {', '.join(data.medical_history)}\n"
    if data.allergies and len(data.allergies) > 0:
        prompt += f"- Allergies: {', '.join(data.allergies)}\n"
    if data.medications and len(data.medications) > 0:
        prompt += f"- Current Medications: {', '.join(data.medications)}\n"

    prompt += """
    Based on this information, provide:
    1. Possible conditions or diagnoses with probability estimates
    2. General recommendations for the patient
    3. Severity level (Low, Medium, High)
    4. Whether the patient should seek immediate medical attention

    Provide your response in a structured JSON format with these exact keys:
    {
      "possible_conditions": [
        {"condition": "Example Condition", "probability": "High/Medium/Low"}
      ],
      "recommendations": ["recommendation 1", "recommendation 2"],
      "severity_level": "Low/Medium/High",
      "seek_medical_attention": true/false
    }
    """

    return prompt

def create_fallback_response() -> dict:
    """Create a fallback response when parsing fails."""
    return {
        "possible_conditions": [{"condition": "Could not determine", "probability": "Unknown"}],
        "recommendations": ["Please consult with a healthcare professional."],
        "severity_level": "Unknown",
        "seek_medical_attention": True
    }

def validate_response_structure(result):
    """Validate and fix the response structure if needed."""
    if not isinstance(result, dict):
        return create_fallback_response()

    # Ensure possible_conditions exists and has correct structure
    if "possible_conditions" not in result or not isinstance(result["possible_conditions"], list):
        result["possible_conditions"] = [{"condition": "Unknown", "probability": "Unknown"}]
    else:
        # Ensure each condition has the right structure
        for i, condition in enumerate(result["possible_conditions"]):
            if not isinstance(condition, dict):
                result["possible_conditions"][i] = {"condition": str(condition), "probability": "Unknown"}
            elif "condition" not in condition:
                result["possible_conditions"][i]["condition"] = "Unknown condition"
            elif "probability" not in condition:
                result["possible_conditions"][i]["probability"] = "Unknown"

    if "recommendations" not in result or not isinstance(result["recommendations"], list):
        result["recommendations"] = ["Please consult with a healthcare professional."]

    if "severity_level" not in result or not isinstance(result["severity_level"], str):
        result["severity_level"] = "Unknown"

    if "seek_medical_attention" not in result or not isinstance(result["seek_medical_attention"], bool):
        result["seek_medical_attention"] = True

    return result

def parse_openai_response(response):
    """Parse the response from OpenAI API."""
    try:
        # Modern OpenAI API (v1.0.0+)
        content = response.choices[0].message.content
        logger.debug(f"Raw OpenAI response: {content}")

        # Try to extract JSON from the response
        try:
            # First, try direct JSON parsing
            result = json.loads(content)
        except json.JSONDecodeError:
            # If that fails, try to extract JSON from text
            import re
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', content) or re.search(r'```\s*([\s\S]*?)\s*```', content) or re.search(r'{[\s\S]*}', content)
            if json_match:
                try:
                    json_content = json_match.group(1) if '```' in json_match.group(0) else json_match.group(0)
                    # Clean up the extracted JSON string
                    cleaned_json = re.sub(r'^\s*```.*\n(.*\n)*?\s*```', '', json_content, flags=re.MULTILINE)
                    result = json.loads(cleaned_json)
                except json.JSONDecodeError:
                    # Fallback if JSON parsing fails
                    logger.error("Could not parse JSON from OpenAI response")
                    return create_fallback_response()
            else:
                # No JSON structure found
                logger.error("No JSON structure found in OpenAI response")
                return create_fallback_response()

        # Validate and ensure the structure
        return validate_response_structure(result)

    except Exception as e:
        logger.error(f"Error parsing OpenAI response: {str(e)}")
        logger.error(traceback.format_exc())
        return create_fallback_response()

@router.post("/analyze", response_model=SymptomResponse)
async def analyze_symptoms(symptom_data: SymptomRequest, background_tasks: BackgroundTasks, request: Request):
    """
    Analyze the provided symptoms and return possible conditions and recommendations.
    """
    start_time = time.time()
    try:
        if not openai_api_key:
            raise HTTPException(status_code=500, detail="OpenAI API key not configured on the server")

        # Sanitize input data
        sanitized_data = SymptomRequest(
            age=symptom_data.age,
            gender=symptom_data.gender,
            symptoms=[s for s in symptom_data.symptoms if isinstance(s, str)],
            medical_history=[m for m in symptom_data.medical_history if isinstance(m, str)] if symptom_data.medical_history else [],
            allergies=[a for a in symptom_data.allergies if isinstance(a, str)] if symptom_data.allergies else [],
            medications=[m for m in symptom_data.medications if isinstance(m, str)] if symptom_data.medications else []
        )

        # Prepare prompt for ChatGPT
        prompt = create_symptom_prompt(sanitized_data)

        try:
            # Call OpenAI API using the modern client
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful medical assistant. Analyze the symptoms provided and suggest possible conditions, recommendations, and whether medical attention should be sought. Format your response as JSON with keys 'possible_conditions' (array of objects with 'condition' and 'probability' fields), 'recommendations' (array of strings), 'severity_level' (string), and 'seek_medical_attention' (boolean)."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=1000
            )

            # Extract and parse the response
            result = parse_openai_response(response)

            # Log the interaction without personal details
            background_tasks.add_task(log_symptom_check, symptom_data.age, symptom_data.gender)

            # Log API request
            processing_time = time.time() - start_time
            background_tasks.add_task(log_api_request, "/api/symptom-checker/analyze", 200, processing_time)

            return result

        except Exception as api_error:
            logger.error(f"OpenAI API error: {str(api_error)}")
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(api_error)}")

    except HTTPException:
        # Re-raise HTTP exceptions without modification
        raise

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        logger.error(traceback.format_exc())  # Log the full traceback
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/test", response_model=SymptomResponse)
async def test_analyze(symptom_data: SymptomRequest):
    """Test endpoint that doesn't call OpenAI API."""
    return {
        "possible_conditions": [
            {"condition": "Test Condition", "probability": "Medium"}
        ],
        "recommendations": ["This is a test recommendation.", "Please consult with a healthcare professional."],
        "severity_level": "Low",
        "seek_medical_attention": False
    }
