import sys
import os
import uuid
import json
from datetime import datetime, timezone
from memory.memory_module import MemoryModule
from agents.classifier_agent import classify_input
from agents.json_agent import process_json_input
from agents.email_agent import extract_email_info
from dotenv import find_dotenv, load_dotenv
import fitz

dotenv_path = find_dotenv()
load_dotenv(dotenv_path)
redis_host = os.getenv("redis_host")
redis_port = int(os.getenv("redis_port"))
redis_password = os.getenv("redis_password")

CONFIDENCE_THRESHOLD = 0.7

def extract_text_from_pdf(pdf_path):
    text = ""
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text += page.get_text()
    return text

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 main.py '<input_content_or_file_path>'")
        sys.exit(1)

    input_arg = sys.argv[1]
    thread_id = str(uuid.uuid4())  # unique conversation/thread ID
    memory = MemoryModule(host=redis_host, port=redis_port, password=redis_password)

    if os.path.exists(input_arg):
        if os.path.isfile(input_arg):
            ext = os.path.splitext(input_arg)[1].lower()
            if ext == ".pdf":
                raw_content = extract_text_from_pdf(input_arg)
            else:
                with open(input_arg, 'r', encoding='utf-8') as f:
                    raw_content = f.read()
        else:
            print(f"Error: Path exists but is not a file: {input_arg}")
            sys.exit(1)
    else:
        if os.path.sep in input_arg or input_arg.endswith((".pdf", "txt", "json", "eml")):
            print(f"Error: File not found: {input_arg}")
            sys.exit(1)
        else:
            raw_content = input_arg

    # Classify input content
    classification_result = classify_input(raw_content)
    source_type = classification_result.format.value
    confidence = classification_result.confidence
    source_id = f"{source_type}_{uuid.uuid4()}"
    timestamp = datetime.now(timezone.utc).isoformat()

    if confidence < CONFIDENCE_THRESHOLD:
        print(f"Warning: Low confidence ({confidence:.2f}) in classification. Routing to manual review.")
        record = {
            "source_id": source_id,
            "source_type": source_type,
            "intent": classification_result.intent.value,
            "confidence": confidence,
            "timestamp": timestamp,
            "thread_id": thread_id,
            "extracted_fields": {},
            "anomalies_detected": ["low_classification_confidence"],
        }
        memory.store_context_bulk(thread_id, record)
        sys.exit(0)

    record = {}

    if source_type == "json":
        extraction = process_json_input(raw_content)
        record = {
            "source_id": source_id,
            "source_type": source_type,
            "intent": classification_result.intent.value,
            "confidence": extraction.confidence,
            "timestamp": timestamp,
            "thread_id": thread_id,
            "extracted_fields": extraction.extracted_data,
            "anomalies_detected": extraction.anomalies,
        }

    elif source_type == "email":
        extraction = extract_email_info(raw_content)
        record = {
            "source_id": source_id,
            "source_type": source_type,
            "intent": classification_result.intent.value,
            "confidence": extraction.confidence,
            "timestamp": timestamp,
            "thread_id": thread_id,
            "extracted_fields": {
                "sender_email": extraction.sender_email,
                "urgency": extraction.urgency,
                "extracted_summary": extraction.extracted_summary
            },
            "anomalies_detected": [],
        }

    elif source_type == "pdf":
        try:
            json_data = json.loads(raw_content)
            extraction = process_json_input(json.dumps(json_data))
            record = {
                "source_id": source_id,
                "source_type": "json",
                "intent": classification_result.intent.value,
                "confidence": extraction.confidence,
                "timestamp": timestamp,
                "thread_id": thread_id,
                "extracted_fields": extraction.extracted_data,
                "anomalies_detected": extraction.anomalies,
            }
        except json.JSONDecodeError:
            extraction = extract_email_info(raw_content)
            record = {
                "source_id": source_id,
                "source_type": "email",
                "intent": classification_result.intent.value,
                "confidence": extraction.confidence,
                "timestamp": timestamp,
                "thread_id": thread_id,
                "extracted_fields": {
                    "sender_email": extraction.sender_email,
                    "urgency": extraction.urgency,
                    "extracted_summary": extraction.extracted_summary
                },
                "anomalies_detected": [],
            }
    else:
        print(f"Unsupported input format: {source_type} with intent: {classification_result.intent.value}")
        sys.exit(1)

    memory.store_context_bulk(thread_id, record)
    print(f"Stored processed result in Redis under THREAD:{thread_id}")

    output = {
        "thread_id": thread_id,
        "classification": {
            "format": record["source_type"],
            "intent": record["intent"],
            "confidence": record["confidence"],
        },
        "extraction": {
            "extracted_fields": record["extracted_fields"],
            "anomalies_detected": record["anomalies_detected"],
        }
    }
    print(json.dumps(output, indent=2))

if __name__ == "__main__":
    main()
