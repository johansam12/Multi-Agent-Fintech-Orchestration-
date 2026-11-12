import asyncio
from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
from redisClient import RedisStateManager
from sqlClient import init_mysql_db, save_application_to_mysql

# Initialize Redis & MySQL
redis_manager = RedisStateManager(host='localhost', port=6379)
init_mysql_db() # Ensures tables exist on startup

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
    print(f"[Credit Agent] Analyzing credit for {state['applicant_name']}...")
    score = state['credit_score']
    ratio = state['requested_amount'] / (state['income'] * 0.5)
    
    risk_score = 0.85 if score < 600 or ratio > 2.0 else (0.45 if score < 700 else 0.15)
    trail = state['audit_trail'] + [f"Credit Agent evaluated risk score: {risk_score}"]
    return {"risk_score": risk_score, "audit_trail": trail}

def compliance_fraud_agent(state: LoanApplicationState) -> Dict[str, Any]:
    print(f"[Compliance Agent] Running AML and fraud checks for ID: {state['applicant_id']}...")
    is_fraudulent = state['income'] < 10000 or state['credit_score'] < 400
    trail = state['audit_trail'] + [f"Compliance Agent check result - Fraud Flag: {is_fraudulent}"]
    return {"fraud_flag": is_fraudulent, "audit_trail": trail}

def decision_synthesis_agent(state: LoanApplicationState) -> Dict[str, Any]:
    print(f"[Supervisor/Synthesis] Making final call...")
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

# Build LangGraph workflow
workflow = StateGraph(LoanApplicationState)
workflow.add_node("check_compliance", compliance_fraud_agent)
workflow.add_node("analyze_credit", credit_analysis_agent)
workflow.add_node("synthesize", decision_synthesis_agent)
workflow.set_entry_point("check_compliance")
workflow.add_conditional_edges("check_compliance", route_after_compliance, {"synthesize": "synthesize", "analyze_credit": "analyze_credit"})
workflow.add_edge("analyze_credit", "synthesize")
workflow.add_edge("synthesize", END)
app_graph = workflow.compile()

async def process_full_pipeline(payload: Dict[str, Any]):
    app_id = payload.get("id")
    initial_state = {
        "applicant_id": app_id,
        "applicant_name": payload.get("name"),
        "income": payload.get("income"),
        "requested_amount": payload.get("amount"),
        "credit_score": payload.get("credit_score"),
        "fraud_flag": False,
        "risk_score": 0.0,
        "approval_status": "PROCESSING",
        "audit_trail": ["Application received into orchestration pipeline."]
    }
    
    # 1. Save initial state to Redis cache
    redis_manager.save_session_state(app_id, initial_state)
    
    # 2. Run LangGraph Multi-Agent Workflow
    final_state = await app_graph.ainvoke(initial_state)
    
    # 3. Update Redis cache with final state
    redis_manager.save_session_state(app_id, final_state)
    for log in final_state["audit_trail"]:
        redis_manager.append_audit_scratchpad(app_id, log)
        
    # 4. Permanently commit record to MySQL
    save_application_to_mysql(final_state)
    
    return final_state

if __name__ == "__main__":
    sample_payload = {
        "id": "COO-0002",
        "name": "Test Sam",
        "income": 95000.0,
        "amount": 20000.0,
        "credit_score": 760
    }
    
    result = asyncio.run(process_full_pipeline(sample_payload))
    print("\n--- Full Architecture Run Complete (Python + LangGraph + Redis + MySQL) ---")
    print(f"Final Status: {result['approval_status']}")