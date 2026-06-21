# =====================================
# STEP 17: STREAMLIT DASHBOARD
# =====================================

import streamlit as st

st.set_page_config(page_title="ReconFlow AI", layout="wide")

st.title("🧠 ReconFlow AI - Finance Agent System")

st.write("Multi-Agent Invoice Reconciliation Platform")

# ----------------------------
# Load system (assumes notebook logic imported)
# ----------------------------

st.sidebar.header("Controls")

invoice_id = st.sidebar.text_input("Enter Invoice ID", "INV002")

run_button = st.sidebar.button("Run AI Agents")

# ----------------------------
# Run Pipeline
# ----------------------------

if run_button:

    st.subheader("🔄 Processing Invoice")

    # Step 1: Invoice Agent
    invoice = invoice_agent.extract_invoice(invoice_id)
    st.json(invoice)

    # Step 2: PO Agent
    match = po_agent.match_invoice_with_po(invoice)
    st.subheader("📑 PO Matching Result")
    st.json(match)

    # Step 3: Decision Agent
    decision = decision_agent.decide(match)
    st.subheader("🧠 AI Decision")
    st.json(decision)

    # Step 4: Email Agent
    email = email_agent.generate_email(decision)
    st.subheader("📧 Generated Email")

    st.write("**Subject:**", email["subject"])
    st.text(email["body"])

    # ----------------------------
    # Reasoning Timeline (if logger exists)
    # ----------------------------
    st.subheader("📊 Agent Reasoning Timeline")

    try:
        supervisor_result = supervisor.process_invoice(invoice_id)
        st.json(supervisor_result["logs"])
    except:
        st.warning("Run supervisor version for full logs")

