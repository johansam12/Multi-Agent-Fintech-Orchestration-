import _asyncio
from typing import TypedDict,Dict, Any, List
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from langgraph.graph import StateGraph, END
from redisClient import RedisStateManager
from mongodbClient import save_application_to_mongo  # Swapped from MySQL to MongoDB

# Initialize FastAPI and Redis
app = FastAPI(title="FinTech Agent Orchestration Hub (MongoDB)")
redis_manager = RedisStateManager(host='localhost', port=6379)

# --- 1. LangGraph Agent Workflow Definition ---
class LoanApplicationState(TypedDict):
    applicant_id: str
    applicant_name: str
    income: float
    requested_amount: float
    credit_score: int
    fraud_flag: bool
    risk_score: float
    approval_status: str
    audit_trail: List[str]

def credit_analysis_agent(state: LoanApplicationState) -> Dict[str, Any]:
    score = state['credit_score']
    ratio = state['requested_amount'] / (state['income'] * 0.5)
    risk_score = 0.85 if score < 600 or ratio > 2.0 else (0.45 if score < 700 else 0.15)
    trail = state['audit_trail'] + [f"Credit Agent evaluated risk score: {risk_score}"]
    return {"risk_score": risk_score, "audit_trail": trail}

def compliance_fraud_agent(state: LoanApplicationState) -> Dict[str, Any]:
    is_fraudulent = state['income'] < 10000 or state['credit_score'] < 400
    trail = state['audit_trail'] + [f"Compliance Agent check result - Fraud Flag: {is_fraudulent}"]
    return {"fraud_flag": is_fraudulent, "audit_trail": trail}

def decision_synthesis_agent(state: LoanApplicationState) -> Dict[str, Any]:
    if state['fraud_flag']:
        status = "REJECTED (Fraud Risk)"
    elif state['risk_score'] > 0.7:
        status = "REJECTED (High Financial Risk)"
    elif state['risk_score'] > 0.4:
        status = "PENDING_HUMAN_REVIEW"
    else:
        status = "APPROVED"
    trail = state['audit_trail'] + [f"Final Decision Reached: {status}"]
    return {"approval_status": status, "audit_trail": trail}

def route_after_compliance(state: LoanApplicationState) -> str:
    if state['fraud_flag']:
        return "synthesize"
    return "analyze_credit"

workflow = StateGraph(LoanApplicationState)
workflow.add_node("check_compliance", compliance_fraud_agent)
workflow.add_node("analyze_credit", credit_analysis_agent)
workflow.add_node("synthesize", decision_synthesis_agent)
workflow.set_entry_point("check_compliance")
workflow.add_conditional_edges("check_compliance", route_after_compliance, {"synthesize": "synthesize", "analyze_credit": "analyze_credit"})
workflow.add_edge("analyze_credit", "synthesize")
workflow.add_edge("synthesize", END)
app_graph = workflow.compile()

# --- 2. Pydantic Request Model ---
class LoanRequest(BaseModel):
    applicant_id: str
    applicant_name: str
    income: float
    requested_amount: float
    credit_score: int

# --- 3. API Endpoints ---
@app.post("/api/apply")
async def apply_loan(data: LoanRequest):
    initial_state = {
        "applicant_id": data.applicant_id,
        "applicant_name": data.applicant_name,
        "income": data.income,
        "requested_amount": data.requested_amount,
        "credit_score": data.credit_score,
        "fraud_flag": False,
        "risk_score": 0.0,
        "approval_status": "PROCESSING",
        "audit_trail": ["Application received into orchestration pipeline."]
    }
    
    # Save initial state in Redis
    redis_manager.save_session_state(data.applicant_id, initial_state)
    
    # Run LangGraph workflow asynchronously
    final_state = await app_graph.ainvoke(initial_state)
    
    # Update Redis cache
    redis_manager.save_session_state(data.applicant_id, final_state)
    for log in final_state["audit_trail"]:
        redis_manager.append_audit_scratchpad(data.applicant_id, log)
        
    # Permanently commit document to MongoDB
    save_application_to_mongo(final_state)
    return final_state

# --- 4. Frontend Web Dashboard UI ---
@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FinTech Multi-Agent Risk Hub (MongoDB)</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-900 text-slate-100 min-h-screen flex flex-col items-center py-10 px-4">
    <div class="w-full max-w-3xl bg-slate-800 border border-slate-700 rounded-xl shadow-2xl p-8">
        <header class="mb-8 border-b border-slate-700 pb-4">
            <h1 class="text-3xl font-bold tracking-tight text-emerald-400">FinTech Agent Risk Hub</h1>
            <p class="text-sm text-slate-400 mt-1">LangGraph Multi-Agent • Redis Cache • MongoDB Document Store</p>
        </header>

        <form id="loanForm" class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            <div>
                <label class="block text-sm font-medium text-slate-300 mb-1">Applicant ID</label>
                <input type="text" id="applicant_id" value="APP-8890" required class="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-slate-100 focus:outline-none focus:border-emerald-500">
            </div>
            <div>
                <label class="block text-sm font-medium text-slate-300 mb-1">Applicant Name</label>
                <input type="text" id="applicant_name" value="Marcus Wright" required class="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-slate-100 focus:outline-none focus:border-emerald-500">
            </div>
            <div>
                <label class="block text-sm font-medium text-slate-300 mb-1">Annual Income ($)</label>
                <input type="number" id="income" value="92000" required class="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-slate-100 focus:outline-none focus:border-emerald-500">
            </div>
            <div>
                <label class="block text-sm font-medium text-slate-300 mb-1">Requested Loan Amount ($)</label>
                <input type="number" id="amount" value="15000" required class="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-slate-100 focus:outline-none focus:border-emerald-500">
            </div>
            <div class="md:col-span-2">
                <label class="block text-sm font-medium text-slate-300 mb-1">Credit Score (300-850)</label>
                <input type="number" id="credit_score" value="780" required class="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-slate-100 focus:outline-none focus:border-emerald-500">
            </div>
            <div class="md:col-span-2">
                <button type="submit" id="submitBtn" class="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-semibold py-3 rounded-lg transition-all shadow-lg">
                    Dispatch Agent Pipeline (MongoDB)
                </button>
            </div>
        </form>

        <div id="resultCard" class="hidden bg-slate-900 border border-slate-700 rounded-xl p-6">
            <h2 class="text-xl font-semibold mb-4 text-emerald-300 flex items-center justify-between">
                <span>Orchestration Execution Results</span>
                <span id="statusBadge" class="text-xs px-3 py-1 rounded-full font-bold"></span>
            </h2>
            <div class="grid grid-cols-2 gap-4 mb-6 text-sm">
                <div class="bg-slate-800 p-3 rounded-lg border border-slate-700">
                    <span class="text-slate-400 block text-xs">Calculated Risk Score</span>
                    <span id="riskScoreVal" class="text-lg font-bold">--</span>
                </div>
                <div class="bg-slate-800 p-3 rounded-lg border border-slate-700">
                    <span class="text-slate-400 block text-xs">Fraud Flag Detected</span>
                    <span id="fraudVal" class="text-lg font-bold">--</span>
                </div>
            </div>
            <h3 class="text-sm font-medium text-slate-400 mb-2">Agent Audit Trail & Decision Logs:</h3>
            <ul id="auditTrailList" class="space-y-2 text-xs font-mono bg-slate-950 p-4 rounded-lg border border-slate-800 max-h-48 overflow-y-auto"></ul>
        </div>
    </div>

    <script>
        document.getElementById('loanForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = document.getElementById('submitBtn');
            btn.innerText = "Agents Working...";
            btn.disabled = true;

            const payload = {
                applicant_id: document.getElementById('applicant_id').value,
                applicant_name: document.getElementById('applicant_name').value,
                income: parseFloat(document.getElementById('income').value),
                requested_amount: parseFloat(document.getElementById('amount').value),
                credit_score: parseInt(document.getElementById('credit_score').value)
            };

            try {
                const response = await fetch('/api/apply', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await response.json();
                
                document.getElementById('resultCard').classList.remove('hidden');
                document.getElementById('riskScoreVal').innerText = data.risk_score;
                document.getElementById('fraudVal').innerText = data.fraud_flag ? "TRUE" : "FALSE";
                
                const badge = document.getElementById('statusBadge');
                badge.innerText = data.approval_status;
                badge.className = "text-xs px-3 py-1 rounded-full font-bold " + 
                    (data.approval_status.includes("APPROVED") ? "bg-emerald-900 text-emerald-300 border border-emerald-700" : "bg-rose-900 text-rose-300 border border-rose-700");

                const list = document.getElementById('auditTrailList');
                list.innerHTML = '';
                data.audit_trail.forEach(log => {
                    const li = document.createElement('li');
                    li.className = "text-slate-300 border-b border-slate-900 pb-1";
                    li.innerText = "-> " + log;
                    list.appendChild(li);
                });
            } catch (err) {
                alert("Error communicating with backend pipeline: " + err);
            } finally {
                btn.innerText = "Dispatch Agent Pipeline (MongoDB)";
                btn.disabled = false;
            }
        });
    </script>
</body>
</html>
    """

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)