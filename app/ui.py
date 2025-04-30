import streamlit as st
import json
from pathlib import Path

def load_examples():
    """
    Load sample systems from data/examples.json and return a dict mapping names to descriptions.
    Supports JSON that is either a dict or list.
    """
    examples_path = Path(__file__).parent.parent / "data" / "examples.json"
    if not examples_path.exists():
        return {}

    try:
        data = json.loads(examples_path.read_text())
        if isinstance(data, dict):
            return data
        if isinstance(data, list):
            return {
                f"Example {i+1}": (item if isinstance(item, str) else json.dumps(item, indent=2))
                for i, item in enumerate(data)
            }
        st.warning("examples.json format not recognized; ignoring examples.")
        return {}
    except Exception as e:
        st.warning(f"Failed to load examples.json: {e}")
        return {}


def render_inputs():
    """
    Render input controls in the main column.
    Returns a tuple (system_description: str, use_local: bool) when the user clicks the button, otherwise None.
    """
    st.subheader("ThreatLens Input")

    # Toggle between local Llama-2 and OpenAI API
    use_local = st.checkbox("Use local model (Llama-2)", value=False)

    st.markdown("---")
    st.write("**Examples / Upload**")

    # Example selector
    examples = load_examples()
    example_keys = [""] + list(examples.keys())
    example_key = st.selectbox("Choose an example system:", example_keys)

    if example_key:
        system_description = examples.get(example_key, "")
    else:
        # File uploader for JSON input
        uploaded = st.file_uploader("Upload system JSON", type=["json"])
        if uploaded:
            try:
                data = json.load(uploaded)
                system_description = json.dumps(data, indent=2)
            except Exception as e:
                st.error(f"Invalid JSON file: {e}")
                return None
        else:
            system_description = st.text_area(
                "Paste or type system description", height=200
            )

    if not system_description:
        return None

    # Generate button
    if st.button("Generate Threat Model"):
        return system_description, use_local

    return None