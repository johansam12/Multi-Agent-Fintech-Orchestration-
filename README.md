# 🚀 FinTech Multi-Agent Risk & Compliance Hub

A production-grade, full-stack **Multi-Agent Orchestration System** designed for automated loan risk evaluation and compliance checking. Built with **Python, LangGraph, Redis, MongoDB, FastAPI, and Tailwind CSS**.

---

## 🛠️ Architecture & Tech Stack

This system moves away from linear prompt chains, implementing a state-machine multi-agent graph where specialized agents collaborate, make decisions, and record audit trails:

* **Core Language:** Python
* **Agent Orchestration:** **LangGraph** (manages cyclical decision nodes, compliance routing, and agent coordination).
* **Caching & State Broker:** **Redis** (handles real-time session tracking and active scratchpads).
* **Document Database:** **MongoDB** (permanently archives rich JSON application states and audit histories).
* **Backend API & Web Server:** **FastAPI**
* **Frontend Interface:** **Tailwind CSS** (embedded interactive web dashboard)

---

## 🤖 The Multi-Agent Workflow
1. **Compliance & Fraud Guard Agent:** Scans applicant metrics for fraud flags, AML risks, and baseline criteria.
2. **Credit Analysis Agent:** Evaluates credit scores and income-to-loan ratios to compute dynamic risk scores.
3. **Decision Synthesis Agent (Supervisor):** Weighs intermediate outputs and reaches a final decision (*Approved*, *Rejected*, or *Pending Review*).

---

## ⚙️ Quick Start & Installation

### 1. Prerequisites
Ensure you have the following running locally:
* **Python 3.10+**
* **Redis Server** (running on port `6379`)
* **MongoDB Server** (running on port `27017`)

### 2. Clone the Repository
```bash
git clone [https://github.com/johansam12/Multi-Agent-Fintech-Orchestration-.git](https://github.com/johansam12/Multi-Agent-Fintech-Orchestration-.git)
cd Multi-Agent-Fintech-Orchestration-

### 3. Install Dependencies
```bash
pip install fastapi uvicorn langgraph redis pymongo pydantic
```

### 4. Run the Application
Start the FastAPI server:
```bash
python server.py
```

### 5. Access the Web Dashboard
Open your browser and navigate to:
👉 **`http://127.0.0.1:8000`**

---

## 📂 Project Structure

* `server.py` — FastAPI backend endpoints, LangGraph graph definition, and Tailwind UI.
* `mongo_client.py` — MongoDB connector and document persistence functions.
* `redis_client.py` — Redis state management and session caching module.