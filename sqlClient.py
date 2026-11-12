import json
from sqlalchemy import create_engine, Column, String, Float, Integer, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Replace with your actual MySQL credentials (e.g., root password, host, port, db name)
# Format: mysql+pymysql://username:password@host:port/database_name

import os
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://root:DARKhaunter3492@localhost:3306/agent_orchestration_db"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class LoanApplicationModel(Base):
    __tablename__ = "loan_applications"

    applicant_id = Column(String(50), primary_key=True, index=True)
    applicant_name = Column(String(100), nullable=False)
    income = Column(Float, nullable=False)
    requested_amount = Column(Float, nullable=False)
    credit_score = Column(Integer, nullable=False)
    risk_score = Column(Float, nullable=True)
    fraud_flag = Column(Integer, default=0) # 0 for False, 1 for True
    approval_status = Column(String(50), nullable=False)
    audit_trail_json = Column(Text, nullable=True) # Stored as JSON string
    created_at = Column(DateTime, default=datetime.utcnow)

def init_mysql_db():
    """Creates the MySQL tables if they do not already exist."""
    Base.metadata.create_all(bind=engine)
    print("[MySQL] Database tables initialized successfully.")

def save_application_to_mysql(final_state: dict):
    """Persists a completed workflow state into MySQL."""
    db = SessionLocal()
    try:
        app_id = final_state.get("applicant_id")
        
        # Check if record already exists, update or insert
        existing_record = db.query(LoanApplicationModel).filter(LoanApplicationModel.applicant_id == app_id).first()
        
        audit_json = json.dumps(final_state.get("audit_trail", []))
        is_fraud = 1 if final_state.get("fraud_flag") else 0

        if existing_record:
            existing_record.risk_score = final_state.get("risk_score")
            existing_record.fraud_flag = is_fraud
            existing_record.approval_status = final_state.get("approval_status")
            existing_record.audit_trail_json = audit_json
        else:
            new_record = LoanApplicationModel(
                applicant_id=app_id,
                applicant_name=final_state.get("applicant_name"),
                income=final_state.get("income"),
                requested_amount=final_state.get("requested_amount"),
                credit_score=final_state.get("credit_score"),
                risk_score=final_state.get("risk_score"),
                fraud_flag=is_fraud,
                approval_status=final_state.get("approval_status"),
                audit_trail_json=audit_json
            )
            db.add(new_record)
            
        db.commit()
        print(f"[MySQL] Successfully persisted application ID {app_id} to database.")
    except Exception as e:
        db.rollback()
        print(f"[MySQL Error] Failed to save application: {e}")
    finally:
        db.close()