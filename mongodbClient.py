import os
from pymongo import MongoClient

# Local MongoDB connection string (or your MongoDB Atlas URI)
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")

client = MongoClient(MONGO_URI)
db = client["agent_orchestration_db"]
applications_collection = db["loan_applications"]

def save_application_to_mongo(final_state: dict):
    """Persists or updates a completed workflow state as a rich JSON document in MongoDB."""
    app_id = final_state.get("applicant_id")
    
    # Use upsert=True so it inserts if new, or updates if the applicant_id already exists
    applications_collection.update_one(
        {"applicant_id": app_id},
        {"$set": final_state},
        upsert=True
    )
    print(f"[MongoDB] Successfully persisted application ID {app_id} to collection.")