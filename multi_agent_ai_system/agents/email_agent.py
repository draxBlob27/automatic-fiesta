import instructor
from pydantic import BaseModel, Field, EmailStr
from enum import Enum
from openai import OpenAI
import os
import logging
from dotenv import find_dotenv, load_dotenv

# ---------------------------------
# Logging Configuration
# ---------------------------------
logger = logging.getLogger(__name__)
handler = logging.FileHandler('/Users/sanilparmar/Desktop/multi_agent_ai_system/logs/email_agent.log', "a")
formatter = logging.Formatter(fmt="%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# ---------------------------------
# GROQ Client Setup
# ---------------------------------
dotenv_path = find_dotenv()
load_dotenv(dotenv_path)
API_KEY = os.getenv("GROQ_API_KEY")

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=API_KEY
)
MODEL = "llama-3.3-70b-versatile"
client = instructor.patch(client)

# ---------------------------------
# Enum and Schema Definitions
# ---------------------------------
class EmailIntent(str, Enum):
    INVOICE = "invoice"
    RFQ = "rfq"
    COMPLAINT = "complaint"
    REGULATION = "regulation"
    OTHER = "other"

class EmailUrgency(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class EmailExtractionResult(BaseModel):
    sender_email: EmailStr
    intent: EmailIntent
    urgency: EmailUrgency
    confidence: float = Field(ge=0, le=1, description="Confidence score for the classification")
    extracted_summary: str = Field(description="Brief summary extracted from the email")

    def to_crm_dict(self) -> dict:
        return {
            "sender": self.sender_email,
            "intent": self.intent.value,
            "urgency": self.urgency.value,
            "summary": self.extracted_summary,
            "confidence": self.confidence
        }

# ---------------------------------
# Prompt
# ---------------------------------
SYSTEM_PROMPT = """
You are an AI email assistant. Given raw email text, extract the following:
1. Sender email address
2. Intent of the email (choose from invoice, rfq, complaint, regulation, other)
3. Urgency of the email (low, medium, high, critical)
4. Provide a brief summary of the email content

If information is missing, return empty strings or 'other' as appropriate.
Provide a confidence score (0-1) for your extraction.
"""

# ---------------------------------
# Main Extraction Logic
# ---------------------------------
def extract_email_info(email_text: str) -> EmailExtractionResult:
    """
    Extracts structured info from raw email text.

    Args:
        email_text (str): Full email content.

    Returns:
        EmailExtractionResult: Extracted structured data.
    """
    try:
        logger.info("Running email extraction...")
        logger.debug(f"Email preview: {email_text[:200]}...")  # Log only first 200 chars

        response = client.chat.completions.create(
            model=MODEL,
            response_model=EmailExtractionResult,
            temperature=0,
            max_retries=3,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": email_text}
            ]
        )

        logger.info(f"Extraction successful | Sender={response.sender_email}, Intent={response.intent}, Urgency={response.urgency}")
        return response

    except Exception as e:
        logger.error(f"Email extraction failed: {e}")
        return EmailExtractionResult(
            sender_email="unknown@example.com",
            intent=EmailIntent.OTHER,
            urgency=EmailUrgency.LOW,
            confidence=0.0,
            extracted_summary="Extraction failed as content is not an email."
        )

def main():
    test_emails = {
        "invoice": """
        From: billing@vendorcorp.com

        Hello,

        Please find attached the invoice #45678 for the recent purchase. The total amount due is $2,350 and the due date is June 15, 2025.

        Let us know if you have any questions.

        Best regards,
        VendorCorp Billing Team
        """,

        "rfq": """
        From: procurement@techfirm.com

        Dear Supplier,

        We are requesting a quotation for the following items:
        - 50 units of Model X processors
        - 100 SSD drives (512GB)

        Please send us your best price and delivery timelines by end of this week.

        Thanks,
        TechFirm Procurement
        """,

        "complaint": """
        From: jane.doe@customer.com

        Hi,

        I recently received my order and noticed the item was defective. The screen is cracked and the product doesn’t turn on.

        I would like a replacement or a refund. Please treat this as urgent.

        Regards,
        Jane Doe
        """,

        "regulation": """
        From: compliance@regagency.gov

        To all vendors,

        As per the updated environmental compliance regulations (effective July 1st), all electronic products must meet RoHS standards. Failure to comply may result in penalties.

        Please review the attached document for full requirements.

        Sincerely,
        Regulatory Agency
        """,

        "other": """
        From: newsletter@somecompany.com

        Hey there,

        Here's our monthly roundup of tech news, industry updates, and team highlights. No action required.

        Enjoy reading!

        The SomeCompany Team
        """
    }

    for label, email in test_emails.items():
        print(f"\n--- Testing intent: {label.upper()} ---")
        result = extract_email_info(email)
        print(result.model_dump_json(indent=2))

if __name__ == "__main__":
    main()