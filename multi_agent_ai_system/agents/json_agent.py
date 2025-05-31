import os
import json
import logging
from typing import List, Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field, EmailStr, constr, ValidationError
import instructor
from openai import OpenAI

logger = logging.getLogger(__name__)
handler = logging.FileHandler('/Users/sanilparmar/Desktop/multi_agent_ai_system/logs/json_agent.log', "w")
formatter = logging.Formatter(fmt="%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.environ.get("GROQ_API_KEY")
)
MODEL = "llama-3.3-70b-versatile"
client = instructor.patch(client)

# --------------------------
# Intent Enum
# --------------------------
class JSONIntent(str, Enum):
    INVOICE = "invoice"
    RFQ = "rfq"
    COMPLAINT = "complaint"
    REGULATION = "regulation"
    OTHER = "other"

# --------------------------
# Data Models per intent
# --------------------------
class InvoiceItem(BaseModel):
    description: str = Field(description= "Description of the invoice item")
    quantity: int = Field(ge=0, description= "Quantity of the item")
    unit_price: float = Field(ge=0.0, description= "Unit price of the item")
    total_price: float = Field(ge=0.0, description= "Total price of the item")

class InvoiceData(BaseModel):
    invoice_number: int = Field(description= "Invoice number")
    invoice_date: str = Field(description= "Invoice date (YYYY-MM-DD)")
    items: List[InvoiceItem] = Field(default_factory=list, description= "Invoice items")
    total_amount: float = Field(ge=0.0, description= "Total amount")

class RFQData(BaseModel):
    rfq_number: int = Field(description= "RFQ number")
    requester_name: str = Field(description= "Requester name")
    requested_items: List[str] = Field(default_factory=list, description= "Requested items")
    deadline: Optional[str] = Field(None, description= "Deadline (YYYY-MM-DD)")

class ComplaintData(BaseModel):
    complaint_id: int = Field(description= "Complaint ID")
    customer_name: str = Field(description= "Customer name")
    complaint_text: str = Field(description= "Complaint text")
    urgency: Optional[str] = Field(description= "Complaint priority")

class OtherData(BaseModel):
    raw_data: Dict[str, Any] = Field(default_factory=dict, description="Raw unclassified JSON data")

# --------------------------
# Extraction Result model
# --------------------------
class JSONExtractionResult(BaseModel):
    intent: JSONIntent = Field(description= "Intent of the JSON input")
    extracted_data: Dict[str, Any] = Field(default_factory=dict, description= "Extracted/reformatted data")
    anomalies: List[str] = Field(default_factory=list, description= "Flagged anomalies or missing fields")
    confidence: float = Field(ge=0, le=1, description= "Confidence score")

# --------------------------
# System prompt for LLM
# --------------------------
SYSTEM_PROMPT = """
You are an AI JSON extraction assistant.

Given a raw JSON string, you must:
1. Detect the intent: one of invoice, rfq, complaint, regulation, other.
2. Extract and reformat the JSON to a structured schema depending on intent.
3. Identify missing or anomalous fields.
4. Provide a confidence score between 0 and 1.

Return a JSON object with keys:
- intent: detected intent
- extracted_data: reformatted structured data
- anomalies: list of anomaly descriptions
- confidence: confidence score (0-1)

If data is missing, mention it in anomalies and reflect empty or default values.

Only use the data provided, do not invent information.
"""

def process_json_input(raw_json_str: str) -> JSONExtractionResult:
    """
    Processes raw JSON string input, calls LLM to classify & extract info,
    then validates and reformats data using Pydantic models.

    Args:
        raw_json_str (str): Raw input JSON string.

    Returns:
        JSONExtractionResult: final structured extraction result.
    """
    try:
        logger.info("Starting JSON input processing...")
        logger.debug(f"JSON input: {raw_json_str}")
        # Validating JSON format first
        try:
            raw_json = json.loads(raw_json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON input: {e}")
            return JSONExtractionResult(
                intent=JSONIntent.OTHER,
                extracted_data={},
                anomalies=[f"Invalid JSON: {e}"],
                confidence=0.0,
            )


        response = client.chat.completions.create(
            model=MODEL,
            response_model=JSONExtractionResult,
            temperature=0,
            max_retries=3,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": raw_json_str}
            ],
        )

        logger.info(f"Response: Intent= {response.intent}, Confidence= {response.confidence}")

        anomalies = response.anomalies or []
        extracted_data = response.extracted_data or {}

        try:
            if response.intent == JSONIntent.INVOICE:
                validated = InvoiceData(**extracted_data)
                extracted_data = validated.model_dump()
            elif response.intent == JSONIntent.RFQ:
                validated = RFQData(**extracted_data)
                extracted_data = validated.model_dump()
            elif response.intent == JSONIntent.COMPLAINT:
                validated = ComplaintData(**extracted_data)
                extracted_data = validated.model_dump()
            else:
                validated = OtherData(raw_data=extracted_data)
                extracted_data = validated.model_dump()
        except ValidationError as ve:
            logger.warning(f"Validation errors for extracted data: {ve}")
            anomalies.append(f"Validation errors: {ve}")

        final_result = JSONExtractionResult(
            intent=response.intent,
            extracted_data=extracted_data,
            anomalies=anomalies,
            confidence=response.confidence,
        )


        logger.info(f"Final JSON extraction result: {final_result}")
        return final_result

    except Exception as e:
        logger.error(f"Error processing JSON input: {e}")
        raise RuntimeError(f"JSON Agent failed: {e}")

def main():
    test_cases = {
        "Invoice": json.dumps({
            "invoice_number": 1234,
            "invoice_date": "2024-10-15",
            "items": [
                {"description": "Widget A", "quantity": 2, "unit_price": 50.0, "total_price": 100.0},
                {"description": "Widget B", "quantity": 1, "unit_price": 75.0, "total_price": 75.0}
            ],
            "total_amount": 175.0
        }),

        "RFQ": json.dumps({
            "rfq_number": 987,
            "requester_name": "Alice Smith",
            "requested_items": ["Steel rods", "Copper wires", "PVC pipes"],
            "deadline": "2024-11-01"
        }),

        "Complaint": json.dumps({
            "complaint_id": 456,
            "customer_name": "John Doe",
            "complaint_text": "Received a damaged product.",
            "urgency": "high"
        }),

        "Regulation": json.dumps({
            "document_title": "Environmental Policy Update 2025",
            "policy_section": "Section 3.2",
            "effective_date": "2025-01-01",
            "notes": "Mandatory compliance for all factories."
        }),

        "Other": json.dumps({
            "random_key": "random_value",
            "misc_data": [1, 2, 3]
        })
    }

    for label, raw_json in test_cases.items():
        print(f"\n--- Testing {label} JSON Input ---")
        try:
            result = process_json_input(raw_json)
            print(result.model_dump_json(indent=2))
        except Exception as e:
            print(f"Failed to process {label}: {e}")

if __name__ == "__main__":
    main()
