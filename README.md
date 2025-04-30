# ThreatLens

**Automated STRIDE-Based Threat Modeling Powered by LLMs**

ThreatLens ingests system documentation such as SSPs, CMDB entries, or textual descriptions, and generates structured STRIDE threat models. It is designed to support cybersecurity analysts, compliance teams, and security architects looking to automate and standardize threat modeling workflows.

---

## Features

- Upload SSP, CMDB, or freeform `.txt`, `.docx`, `.pdf` files
- Choose between OpenAI or local LLM inference (LLaMA-2 supported)
- Outputs JSON-structured STRIDE threat model with:
  - Title, Description, Mitigation
  - Mapped NIST 800-53 controls
  - Justifications for why each control applies
- Download threat models for reuse or audit
- Embedding pipeline for real-time context-aware reasoning
- Clean dark-mode UI with sidebar workflow

---

## Getting Started

```bash
git clone https://github.com/YOUR_USERNAME/ThreatLens.git
cd ThreatLens

python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt

echo "OPENAI_API_KEY=sk-..." > .env

streamlit run app/app.py
```

---

## Prerequisites

- Python 3.9 or higher
- Git installed
- A valid OpenAI API key (if using OpenAI models)

---

## Configuration

Set the following environment variables, either in a `.env` file or in your shell:

- `OPENAI_API_KEY`: Your OpenAI API token
- `HF_MODEL_ID` (optional): Hugging Face model ID for local inference, e.g. `meta-llama/Llama-2-7b-chat-hf`
- `HUGGINGFACE_TOKEN` (optional): Hugging Face access token for private models

---

## Directory Layout

```
ThreatLens/
├── app/                # Streamlit application code
├── core/               # Core threat modeling and embedding logic
├── data/               # Example inputs and static data
├── .streamlit/         # Streamlit configuration
├── README.md           # Project overview and setup instructions
└── requirements.txt    # Python dependencies
```

---

## Testing

To run unit tests (once implemented), use:

```bash
pytest tests/
```

---

## Example Use Case

**User Input (system description):**

```
System Name: Credit Union Core Banking Platform
Vendor: Corelation, Inc.
Hosting: On-premises Red Hat Linux with PostgreSQL
Interfaces: Online banking, mobile app, ACH gateway
Data Types: Member PII, financial transactions
Authentication: OAuth 2.0 with MFA
Encryption: TLS 1.2 in transit, full-disk encryption at rest
Known Risks:
- Developers have read access to production logs
- WAF rules partially cover mobile endpoints
Compliance: GLBA, PCI-DSS, NIST SP 800-53
```

**AI Output:**

```json
{
  "Information Disclosure": [
    {
      "title": "PII Exposure in Core Database",
      "description": "PostgreSQL stores member PII without full audit logging.",
      "mitigation": "Enable immutable logging and enforce encryption with access control.",
      "controls": [
        {
          "id": "NIST AU-4",
          "reason": "Applies to the core PostgreSQL database storing PII; ensures access logging is tamper-evident."
        }
      ]
    }
  ]
}
```

This example shows how ThreatLens ingests a system description (like a CMDB entry) and outputs a STRIDE-based threat model with controls that mitigate identified risks, tying each control back to a specific component.

---

## Roadmap

- [ ] Grounded retrieval from embedded NIST 800-53 corpus
- [ ] System component-to-control explanation mapping
- [ ] SQLite or Qdrant vector DB integration
- [ ] Upload support for `.json` SSPs or OSCAL format
- [ ] Multi-system batch mode

---

## Contributing

Contributions are welcome. Please open an issue before submitting a pull request to discuss changes.

---

## Support

For questions or feedback, contact James Massengille at massengillejames@gmail.com.

---

## Credits

Built by [James Massengille](https://github.com/jmassengille) using Streamlit, FAISS, HuggingFace, and OpenAI.

MIT License. Use responsibly.
