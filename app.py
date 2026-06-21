import streamlit as st
from pipeline import *

# =========================
# INIT SYSTEM
# =========================

invoice_agent = InvoiceAgent()
po_agent = POAgent()
tools = FinanceTools(purchase_orders)
planner = MockPlannerLLM()
logger = AgentLogger()

tool_agent = ToolCallingAgent(tools, planner, logger)
decision_agent = DecisionAgent()
email_agent = EmailAgent()

# =========================
# UI
# =========================

st.set_page_config(page_title="ReconFlow AI", layout="wide")

st.title("🧠 ReconFlow AI - Invoice Reconciliation System")

invoice_id = st.text_input("Enter Invoice ID", "INV002")

run = st.button("Run Pipeline")

# =========================
# RUN PIPELINE
# =========================

if run:

    st.subheader("📄 Step 1: Invoice Extraction")
    invoice = invoice_agent.extract_invoice(invoice_id)
    st.json(invoice)

    state = AgentState()
    state.invoice = invoice

    st.subheader("📑 Step 2: PO Match")
    match = po_agent.match_invoice_with_po(invoice)
    state.po = match
    st.json(match)

    st.subheader("🧠 Step 3: Tool Planning")
    plan = tool_agent.plan(state)
    st.json(plan)

    st.subheader("⚙️ Step 4: Tool Execution")
    results = tool_agent.execute(plan, state)
    state.tool_results = results
    st.json(results)

    st.subheader("📊 Step 5: Decision Engine")
    decision = decision_agent.decide(results)
    decision["invoice_id"] = invoice["invoice_id"]
    state.decision = decision
    st.json(decision)

    st.subheader("📧 Step 6: Email Generation")
    email = email_agent.generate_email(decision)
    state.email = email

    st.write("**Subject:**", email["subject"])
    st.text(email["body"])

    st.subheader("📜 Logs")
    logger.log("SYSTEM", f"Processed {invoice_id}")
    logger.show()
