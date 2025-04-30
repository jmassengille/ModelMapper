import os
from dotenv import load_dotenv
from functools import lru_cache
from transformers import pipeline
from openai import OpenAI

# Load environment variables (e.g., OPENAI_API_KEY, HF_MODEL_ID, HUGGINGFACE_TOKEN)
load_dotenv()

# Default model identifiers
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

def generate_threat_model(system_description: str, use_local: bool = False, context_chunks=None) -> str:
    if context_chunks:
        joined_context = "\n\n".join(context_chunks)
        system_description += f"\n\nAdditional context:\n{joined_context}"

    prompt = f"""
You are a security assistant. Analyze the system information below and produce a threat model using STRIDE categories.

Respond in the following JSON structure:
{{
  "Spoofing": [{{ "title": "...", "description": "...", "mitigation": "...", "controls": ["NIST AC-3"] }}],
  "Tampering": [...],
  "Repudiation": [...],
  "Information Disclosure": [...],
  "Denial of Service": [...],
  "Elevation of Privilege": [...]
}}

System Description:
{system_description}
"""

    if use_local:
        result = local_pipe(prompt, max_new_tokens=1024, do_sample=True, temperature=0.7)
        return result[0]['generated_text'] if result else "[No output]"
    else:
        try:
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a security assistant."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
            )
            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"OpenAI API call failed: {e}")
