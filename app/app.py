import streamlit as st
from app.ui import render_inputs
from core.threat_modeler import generate_threat_model
from core.embedding_pipeline import EmbeddingPipeline
from core.formatter import parse_stride_output, render_threat_model, render_download_button
import tempfile

pipeline = EmbeddingPipeline()

def main():
    st.set_page_config(page_title="ThreatLens", layout="wide")

    # Sidebar controls
    st.sidebar.title("ThreatLens Setup")
    uploaded_file = st.sidebar.file_uploader("Upload SSP / CMDB (.txt, .docx, .pdf)", type=["txt", "docx", "pdf"])
    use_local = st.sidebar.checkbox("Use local model (Llama-2)", value=False)
    generate = st.sidebar.button("Generate Threat Model")

    # Apply dark theme overrides
    st.markdown("""
        <style>
        body, .block-container {
            background-color: #0e1117;
            color: #fafafa;
        }
        h1 {
            color: #1f77b4;
            font-size: 2.6rem;
            margin-bottom: 0.2rem;
        }
        .subtitle {
            color: #c0c0c0;
            font-size: 1.05rem;
            margin-bottom: 1.5rem;
        }
        .stButton > button {
            background-color: #1f77b4;
            color: white;
        }
        .stTextArea textarea {
            background-color: #1a1d23;
            color: #fafafa;
        }
        .stTextInput input {
            background-color: #1a1d23;
            color: #fafafa;
        }
        .stMarkdown, .stExpanderContent {
            color: #fafafa;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<h1>ThreatLens</h1>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>Automated STRIDE Threat Modeling with LLMs</div>", unsafe_allow_html=True)

    # Input area in main panel
    st.subheader("System Description")
    manual_input = st.text_area("Paste or type system description", height=200)

    # Collect embedding context if file uploaded
    context_chunks = []
    if uploaded_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=uploaded_file.name) as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name
        try:
            pipeline.process_uploaded_file(tmp_path)
            top_chunks = pipeline.query("Generate a threat model", top_k=5)
            context_chunks = [chunk for chunk, _ in top_chunks]
            st.success(f"{len(pipeline.text_chunks)} chunks processed from uploaded file.")
            with st.expander("Preview Extracted Chunks"):
                for chunk, dist in top_chunks:
                    st.markdown(f"**Score:** {dist:.2f}\n\n{chunk}")
        except Exception as e:
            st.error(f"Failed to process uploaded file: {e}")

    # Main interaction output
    if generate and (manual_input or context_chunks):
        system_desc = manual_input if manual_input else "\n\n".join(context_chunks)
        try:
            output = generate_threat_model(system_desc, use_local, context_chunks=context_chunks)
            parsed = parse_stride_output(output)
        except ValueError:
            st.warning("Could not parse model output as structured JSON. Displaying raw output:")
            st.markdown(output)
        except RuntimeError as e:
            st.error(str(e))
        else:
            st.success("Threat model generated successfully.")
            render_threat_model(parsed)
            render_download_button(parsed)

if __name__ == "__main__":
    main()