import pandas as pd
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Any
import json

# =========================
# SAMPLE DATA
# =========================

invoice_data = [
    {"invoice_id": "INV001", "po_id": "PO1001", "vendor": "ABC Supplies", "amount": 15000, "currency": "INR"},
    {"invoice_id": "INV002", "po_id": "PO1002", "vendor": "Global Tech", "amount": 30000, "currency": "INR"},
    {"invoice_id": "INV003", "po_id": "PO1003", "vendor": "Office World", "amount": 10000, "currency": "INR"}
]

invoice_df = pd.DataFrame(invoice_data)

purchase_orders = pd.DataFrame([
    {"PO_ID": "PO1001", "Vendor": "ABC Supplies", "Amount": 15000, "Status": "Approved"},
    {"PO_ID": "PO1002", "Vendor": "Global Tech", "Amount": 28000, "Status": "Approved"},
    {"PO_ID": "PO1003", "Vendor": "Office World", "Amount": 10000, "Status": "Approved"}
])

finance_policies = [
    {"text": "Amount mismatch above 5% must be escalated"},
    {"text": "Vendor mismatch leads to rejection"},
    {"text": "Approved PO required for all invoices"}
]

# =========================
# STATE
# =========================

@dataclass
class AgentState:
    invoice: Dict[str, Any] = field(default_factory=dict)
    po: Dict[str, Any] = field(default_factory=dict)
    tool_results: Dict[str, Any] = field(default_factory=dict)
    decision: Dict[str, Any] = field(default_factory=dict)
    email: Dict[str, Any] = field(default_factory=dict)
    current_step: str = "INIT"
    logs: List[str] = field(default_factory=list)
    invoice_id: str = ""

# =========================
# INVOICE AGENT
# =========================

class InvoiceAgent:
    def extract_invoice(self, invoice_id):
        row = invoice_df[invoice_df["invoice_id"] == invoice_id]
        if row.empty:
            raise Exception("Invoice not found")

        invoice = row.iloc[0].to_dict()
        invoice["extracted_at"] = str(datetime.now())
        return invoice

# =========================
# PO AGENT
# =========================

class POAgent:
    def match_invoice_with_po(self, invoice):
        po = purchase_orders[purchase_orders["PO_ID"] == invoice["po_id"]]

        if po.empty:
            return {
                "status": "NO_PO_FOUND",
                "issues": ["Purchase Order Missing"]
            }

        po = po.iloc[0].to_dict()

        issues = []
        if invoice["vendor"] != po["Vendor"]:
            issues.append("Vendor mismatch")
        if invoice["amount"] != po["Amount"]:
            issues.append("Amount mismatch")

        return {
            "status": "MATCH" if not issues else "PARTIAL_MATCH",
            "issues": issues,
            "invoice": invoice,
            "po": po
        }

# =========================
# FINANCE TOOLS
# =========================

class FinanceTools:

    def __init__(self, purchase_orders):
        self.purchase_orders = purchase_orders

    def lookup_po(self, po_id):
        po = self.purchase_orders[self.purchase_orders["PO_ID"] == po_id]

        if po.empty:
            return {"found": False}

        po = po.iloc[0]

        return {
            "found": True,
            "po_id": po["PO_ID"],
            "vendor": po["Vendor"],
            "amount": float(po["Amount"]),
            "status": po["Status"]
        }

    def validate_amount(self, invoice_amount, po_amount):
        return {
            "match": invoice_amount == po_amount,
            "difference": abs(invoice_amount - po_amount),
            "invoice_amount": invoice_amount,
            "po_amount": po_amount
        }

# =========================
# PLANNER
# =========================

class MockPlannerLLM:
    def plan(self, state):
        return [
            {"tool": "lookup_po", "args": {"po_id": state.invoice["po_id"]}},
            {"tool": "validate_amount", "args": {"invoice_amount": state.invoice["amount"]}}
        ]

# =========================
# TOOL AGENT
# =========================

class ToolCallingAgent:

    def __init__(self, tools, planner, logger=None):
        self.tools = tools
        self.planner = planner
        self.logger = logger

    def plan(self, state):
        return self.planner.plan(state)

    def execute(self, plan, state):

        results = {}
        po_info = None

        for step in plan:

            if step["tool"] == "lookup_po":
                po_info = self.tools.lookup_po(step["args"]["po_id"])
                results["po_lookup"] = po_info

            elif step["tool"] == "validate_amount":
                results["amount_check"] = self.tools.validate_amount(
                    step["args"]["invoice_amount"],
                    po_info["amount"] if po_info else 0
                )

        return results

# =========================
# DECISION AGENT
# =========================

class DecisionAgent:

    def decide(self, tool_results):

        po = tool_results.get("po_lookup", {})
        amt = tool_results.get("amount_check", {})

        if not po.get("found", False):
            decision = "REJECT"
            reason = "Purchase Order not found"

        elif not amt.get("match", False):
            decision = "REJECT"
            reason = "Amount mismatch"

        else:
            decision = "APPROVE"
            reason = "All checks passed"

        return {
            "decision": decision,
            "confidence": 0.9,
            "reasoning": reason,
            "invoice_id": po.get("po_id", "")
        }

# =========================
# EMAIL AGENT
# =========================

class EmailAgent:

    def generate_email(self, decision):

        if decision["decision"] == "APPROVE":
            return {
                "subject": f"Invoice {decision['invoice_id']} Approved",
                "body": "Invoice approved successfully."
            }

        return {
            "subject": f"Invoice {decision['invoice_id']} Rejected",
            "body": f"Reason: {decision['reasoning']}"
        }

# =========================
# LOGGER
# =========================

class AgentLogger:

    def __init__(self):
        self.logs = []

    def log(self, agent, message):
        self.logs.append({
            "time": datetime.now().strftime("%H:%M:%S"),
            "agent": agent,
            "message": message
        })

    def show(self):
        print("\n" + "=" * 60)
        print("RECONFLOW AI - LOGS")
        print("=" * 60)

        for log in self.logs:
            print(f"[{log['time']}] {log['agent']}: {log['message']}")

        print("=" * 60)

# =========================
# ANALYTICS ENGINE
# =========================

class AnalyticsEngine:

    def __init__(self):
        self.records = []

    def log_result(self, invoice_id, decision, match):
        self.records.append({
            "invoice_id": invoice_id,
            "decision": decision["decision"],
            "confidence": decision.get("confidence", 0),
            "status": match.get("status", "")
        })

    def summary(self):

        total = len(self.records)

        if total == 0:
            return {"message": "No data available"}

        approved = sum(1 for r in self.records if r["decision"] == "APPROVE")
        rejected = sum(1 for r in self.records if r["decision"] == "REJECT")

        return {
            "total": total,
            "approved": approved,
            "rejected": rejected,
            "approval_rate": approved / total if total else 0
        }