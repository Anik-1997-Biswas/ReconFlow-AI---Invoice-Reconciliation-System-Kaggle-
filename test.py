import pipeline as p

# =========================
# STEP 0: INIT
# =========================
invoice_agent = p.InvoiceAgent()
po_agent = p.POAgent()

tools = p.FinanceTools(p.purchase_orders)
planner = p.MockPlannerLLM()
logger = p.AgentLogger()

agent = p.ToolCallingAgent(tools, planner, logger)
decision_agent = p.DecisionAgent()

# =========================
# STEP 1: LOAD INVOICE
# =========================
invoice = invoice_agent.extract_invoice("INV002")

state = p.AgentState()
state.invoice = invoice
state.invoice_id = invoice["invoice_id"]

logger.log("SYSTEM", f"Loaded invoice {state.invoice_id}")

# =========================
# STEP 2: PO MATCH (BASELINE)
# =========================
match = po_agent.match_invoice_with_po(invoice)
state.po = match

print("\n=== BASELINE PO MATCH ===")
print(match)

# =========================
# STEP 3: PLAN
# =========================
plan = agent.plan(state)

print("\n=== PLAN ===")
print(plan)

# =========================
# STEP 4: EXECUTE TOOLS
# =========================
results = agent.execute(plan, state)
state.tool_results = results

print("\n=== TOOL RESULTS ===")
print(results)

# =========================
# STEP 5: DECISION
# =========================
decision = decision_agent.decide(results)
decision["invoice_id"] = state.invoice["invoice_id"]
state.decision = decision

print("\n=== DECISION ===")
print(decision)

# =========================
# STEP 6: EMAIL
# =========================
email = p.EmailAgent().generate_email(decision)
state.email = email

print("\n=== EMAIL ===")
print(email)

# =========================
# STEP 7: STATE
# =========================
print("\n=== FINAL STATE ===")
print(state)

# =========================
# STEP 8: LOGS
# =========================
logger.log("SYSTEM", f"Final decision: {decision['decision']}")

print("\n=== AGENT LOGS ===")
logger.show()

# =========================
# STEP 9: VALIDATION
# =========================
print("\n=== VALIDATION CHECKS ===")

print(
    "PO vs TOOL MATCH:",
    match["status"],
    "| TOOL PO FOUND:",
    results["po_lookup"]["found"]
)

print(
    "Amount consistency:",
    match["po"]["Amount"] == invoice["amount"]
)

print(
    "Decision correctness:",
    "PASS" if decision["decision"] in ["APPROVE", "REJECT", "ESCALATE"] else "FAIL"
)

# =========================
# STEP 10: ANALYTICS
# =========================
analytics = p.AnalyticsEngine()

analytics.log_result(
    invoice_id=state.invoice_id,
    decision=decision,
    match=match
)

print("\n=== ANALYTICS SUMMARY ===")
print(analytics.summary())