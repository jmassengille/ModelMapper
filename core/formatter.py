import json
import streamlit as st
from typing import Dict, Any

def parse_stride_output(model_output: str) -> Dict[str, Any]:
    """
    Attempt to parse model output as JSON.
    If parsing fails, raise ValueError.
    """
    try:
        parsed = json.loads(model_output)
        if not isinstance(parsed, dict):
            raise ValueError("Parsed output is not a JSON object.")
        return parsed
    except Exception as e:
        raise ValueError(f"Failed to parse model output as JSON: {e}")

def render_threat_model(threat_dict: Dict[str, Any]):
    """
    Display parsed STRIDE threat model using Streamlit expanders.
    """
    for category in [
        "Spoofing", "Tampering", "Repudiation",
        "Information Disclosure", "Denial of Service", "Elevation of Privilege"
    ]:
        threats = threat_dict.get(category, [])
        with st.expander(category):
            if not threats:
                st.markdown("*No threats identified in this category.*")
            for threat in threats:
                title = threat.get("title", "Untitled Threat")
                description = threat.get("description", "No description.")
                mitigation = threat.get("mitigation", "No mitigation provided.")
                controls = ", ".join(threat.get("controls", []))

                st.markdown(f"**{title}**")
                st.markdown(f"- **Description:** {description}")
                st.markdown(f"- **Mitigation:** {mitigation}")
                st.markdown(f"- **Controls:** {controls}")
                st.markdown("---")

def render_download_button(threat_dict: Dict[str, Any]):
    """
    Add a download button to export the threat model as JSON.
    """
    json_data = json.dumps(threat_dict, indent=2)
    st.download_button(
        label="Download Threat Model (JSON)",
        data=json_data,
        file_name="threat_model.json",
        mime="application/json"
    )