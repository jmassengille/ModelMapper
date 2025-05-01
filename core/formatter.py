import json
import streamlit as st

def parse_stride_output(model_output):
    try:
        parsed = json.loads(model_output)
        return parsed
    except Exception as e:
        raise ValueError(f"Failed to parse model output as JSON: {e}")

def render_threat_model(threats):
    system_name = threats.get("System Name")
    if system_name:
        st.header(f"System Name: {system_name}")
        st.markdown("---")

        # Summary block
        total_threats = 0
        unique_controls = set()
        stride_categories = [
            "Spoofing", "Tampering", "Repudiation",
            "Information Disclosure", "Denial of Service", "Elevation of Privilege"
        ]

        for category in stride_categories:
            items = threats.get(category, [])
            total_threats += len(items)
            for threat in items:
                for ctl in threat.get("controls", []):
                    unique_controls.add(ctl.get("id"))

        st.info(
            f"**Compliance Target:** {threats.get('Compliance Target', 'N/A')}  \n"
            f"**Detected Threat Categories:** {sum(1 for cat in stride_categories if threats.get(cat))}  \n"
            f"**Total Mapped Threats:** {total_threats}  \n"
            f"**Unique Controls Mapped:** {len(unique_controls)}"
        )
        st.markdown("---")

    for category in [
        "Spoofing", "Tampering", "Repudiation",
        "Information Disclosure", "Denial of Service", "Elevation of Privilege"
    ]:
        items = threats.get(category)
        if not items:
            continue

        st.subheader(category)
        for threat in items:
            title = threat.get("title", "[No Title]")
            description = threat.get("description", "")
            mitigation = threat.get("mitigation", "")
            component = threat.get("system_component", "Unknown component")
            controls = threat.get("controls", [])

            st.markdown(f"**Threat:** {title}")
            st.markdown(f"**Component:** {component}")
            st.markdown(f"**Description:** {description}")
            st.markdown(f"**Mitigation:** {mitigation}")

            if controls:
                st.markdown("**Mapped Controls:**")
                for ctl in controls:
                    cid = ctl.get("id")
                    reason = ctl.get("reason", "")
                    short_reason = reason[:250] + "..." if len(reason) > 250 else reason
                    st.markdown(f"- `{cid}`: {short_reason}")

            st.markdown("---")

def render_download_button(threats):
    st.download_button(
        label="Download JSON",
        data=json.dumps(threats, indent=2),
        file_name="threat_model.json",
        mime="application/json",
    )
