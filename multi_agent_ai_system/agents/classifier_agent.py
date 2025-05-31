# --------------------------------------------------------------------
# Classifier Agent, to route to different agents based on user input.
# --------------------------------------------------------------------

import instructor
from pydantic import BaseModel, Field
from openai import OpenAI
from enum import Enum
import os
import logging
from dotenv import find_dotenv, load_dotenv
import fitz

logger = logging.getLogger(__name__)
formatter = logging.Formatter(fmt="%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
handler = logging.FileHandler('/Users/sanilparmar/Desktop/multi_agent_ai_system/logs/classifier_agent.log', "a")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# --------------------------------------------------------------
# Step 1: Objectives
# --------------------------------------------------------------
"""
Objective:
This module provides a robust classifier agent that:
- Accepts raw input (PDF text, JSON string, or email content).
- Uses LLM (OpenAI/GROQ) to classify:
    1. Format → pdf / json / email.
    2. Intent → invoice, rfq, complaint, regulation, other.
    3. Confidence → float between 0–1.

Design Goals:
- Structured output using Pydantic models.
- High reliability: retries, timeouts, logging.
- Can be imported and reused in main orchestrator or tests.
"""

# --------------------------------------------------------------
# Step 2: Patching LLM with instructor
# --------------------------------------------------------------
dotenv_path = find_dotenv()
load_dotenv(dotenv_path)
API_KEY = os.getenv("GROQ_API_KEY")

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=API_KEY
)
MODEL  = "llama-3.3-70b-versatile"

client = instructor.patch(client)

# --------------------------------------------------------------
# Step 3: Define Pydantic data models
# --------------------------------------------------------------
"""
This code defines a structured data model for classifying prompts using Pydantic and Python's Enum class. 
It specifies relevant information as predefined options or constrained fields. 
This structure ensures data consistency, enables automatic validation, and facilitates easy integration with AI models.
"""

class InputFormat(str, Enum):
    JSON = "json"
    EMAIL = "email"
    PDF = "pdf"

class InputIntent(str, Enum):
    INVOICE = "invoice"
    RFQ = "rfq"
    COMPLAINT = "complaint"
    REGULATION = "regulation"
    OTHER = "other"

# --------------------------------------------------------------
# Step 4: Output Model Definition
# --------------------------------------------------------------

class ClassificationResult(BaseModel):
    intent: InputIntent
    format: InputFormat
    confidence: float = Field(ge=0, le=1, description="Confidence score for the classification")

# --------------------------------------------------------------
# Step 5: System Prompt for LLM
# --------------------------------------------------------------
SYSTEM_PROMPT = """
You are an AI classifier. Given an input (PDF content, JSON string, or email text), your tasks are:
1. Classify its format → one of: pdf, json, email.
2. Classify its intent → one of: invoice, rfq, complaint, regulation, other.
3. Provide a confidence score (0–1).

Important:
- Only use the information provided.
- Try to find sender address, intent and issue in priority.
- If unsure, lower the confidence score.
- Do not invent or assume extra details.

Output must strictly follow the defined structured format.
Analyze the following input and provide the requested information in the specified format.
"""

# --------------------------------------------------------------
# Step 6: Classification Function
# --------------------------------------------------------------

def classify_input(text: str) -> ClassificationResult:
    """
    Runs LLM classification on input text.

    Args:
        text (str): Raw input content (PDF extracted text, JSON string, or email body).

    Returns:
    ClassificationResult: Structured Pydantic object with format, intent, and confidence fields.
    """
    try:
        logger.info("Running classifier on input...")
        logger.debug(f"Input text: {text}")
        response = client.chat.completions.create(
            model=MODEL,
            response_model= ClassificationResult,
            temperature=0,
            max_retries=3,
            messages= [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ]
        )
        logger.info(f"Classification completed: Format={response.format}, Intent={response.intent}, Confidence={response.confidence}")
        return response
    except Exception as e:
        logger.error(f"Error during classification: {e}")
        raise RuntimeError(f"Classification failed: {e}")


def main():
    test_cases = {
        "invoice_json": """
        {
          "invoice_number": 12345,
          "invoice_date": "2025-05-30",
          "items": [
            {"description": "Widget A", "quantity": 10, "unit_price": 15.0, "total_price": 150.0}
          ],
          "total_amount": 150.0
        }
        """,
        "rfq_email": """
        From: supplier@example.com
        Subject: RFQ for electronic components

        Dear team,
        Please provide a quote for 100 resistors and 50 capacitors by next Friday.

        Best,
        Supplier
        """,
        "complaint_pdf_text": """
        Customer complaint report:
        The delivered product was defective and did not meet the promised specifications.
        Immediate replacement requested.
        """,
        "regulation_text": """
        According to regulation 2025-05-15, all suppliers must comply with new safety standards.
        """,
        "other_text": "This is a miscellaneous note with no specific format or intent."
    }

    for name, input_text in test_cases.items():
        print(f"\n--- Testing case: {name} ---")
        try:
            result = classify_input(input_text)
            print(f"Format: {result.format}")
            print(f"Intent: {result.intent}")
            print(f"Confidence: {result.confidence:.2f}")
        except Exception as e:
            print(f"Error in test case {name}: {e}")

if __name__ == "__main__":
    main()
