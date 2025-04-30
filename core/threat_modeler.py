import os
import json
from dotenv import load_dotenv
from functools import lru_cache
from transformers import pipeline
from openai import OpenAI
from core.formatter import parse_stride_output
from core.control_index import ControlIndex

# Load environment variables
load_dotenv()

# Model identifiers
LOCAL_MODEL_ID = os.getenv("HF_MODEL_ID", "meta-llama/Llama-2-7b-chat-hf")
HUGGINGFACE_TOKEN = os.getenv("HUGGINGFACE_TOKEN")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

@lru_cache(maxsize=1)
def get_local_pipeline():
    try:
        return pipeline(
            task="text-generation",
            model=LOCAL_MODEL_ID,
            tokenizer=LOCAL_MODEL_ID,
            device=-1,
            framework="pt",
            return_full_text=False,
            use_auth_token=HUGGINGFACE_TOKEN,
        )
    except Exception as e:
        raise RuntimeError(f"Failed to initialize local pipeline: {e}")

local_pipe = get_local_pipeline()
client = OpenAI(api_key=OPENAI_API_KEY)

_control_index = None

def _get_control_index():
    global _control_index
    if _control_index is None:
        _control_index = ControlIndex()
        _control_index.load_controls()
        _control_index.build_faiss_index()
    return _control_index

def generate_threat_model(system_description: str, use_local: bool = False, context_chunks=None) -> str:
    if context_chunks:
        joined_context = "\n\n".join(context_chunks)
        system_description += f"\n\nAdditional context:\n{joined_context}"

    # Prompt with strict structure and sample JSON
    prompt = f"""
You are a security assistant. Given the system description below, generate a threat model using the STRIDE framework.

Respond only with a valid JSON object using the structure below.
Do not add any Markdown formatting, explanation, or backticks. Return only pure JSON.

Each STRIDE category should be a key with a list of threats.
Each threat must include: title, description, mitigation, system_component, and a list of controls.
Each control must include: id (NIST control identifier) and a reason explaining why it applies.

Example format:
{{
  "System Name": "Payment Processing API",
  "Spoofing": [
    {{
      "title": "OAuth Token Abuse",
      "description": "An attacker may abuse token issuance via misconfigured OAuth 2.0 flows.",
      "mitigation": "Restrict grant types and validate token scopes.",
      "system_component": "OAuth 2.0 authentication",
      "controls": [
        {{
          "id": "AC-3",
          "reason": "OAuth requires enforcing access rights per session and user role."
        }}
      ]
    }}
  ],
  "Tampering": [],
  "Repudiation": [],
  "Information Disclosure": [],
  "Denial of Service": [],
  "Elevation of Privilege": []
}}

System Description:
{system_description}
"""

    try:
        if use_local:
            result = local_pipe(prompt, max_new_tokens=1024, do_sample=True, temperature=0.7)
            raw = result[0]['generated_text'] if result else ""
        else:
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a security assistant."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
            )
            raw = response.choices[0].message.content.strip()

        # Try parsing
        try:
            threats = parse_stride_output(raw)
        except ValueError:
            return json.dumps({"error": "Failed to parse model output", "raw": raw})

        # Enrich threats with grounded controls
        ci = _get_control_index()
        for category, items in threats.items():
            if isinstance(items, list):
                for threat in items:
                    if isinstance(threat, dict):
                        desc = threat.get("description", "")
                        controls = ci.query(desc, top_k=3)
                        threat["controls"] = [
                            {"id": c["id"], "reason": c["text"][:200]} for c in controls
                        ]

        return json.dumps(threats, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)})
