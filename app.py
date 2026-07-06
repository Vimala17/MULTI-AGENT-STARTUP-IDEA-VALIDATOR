import os
import json
import requests
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from bson import ObjectId

load_dotenv()

app = Flask(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")

client = MongoClient(MONGO_URI)
db = client["startupsense_db"]
history_collection = db["analyses"]

def json_serializable(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    raise TypeError(f"Type {type(obj)} not serializable")

def call_groq_agent(system_prompt, user_prompt):
    if not GROQ_API_KEY:
        return {"error": "API Key missing"}

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.3
    }

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=60
        )
        if response.status_code != 200:
            return {"error": f"API Error {response.status_code}"}
        res_json = response.json()
        content = res_json["choices"][0]["message"]["content"]
        return json.loads(content)
    except Exception as e:
        return {"error": str(e)}

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/analyze", methods=["POST"])
def analyze_idea():
    data = request.get_json(silent=True) or {}
    idea = data.get("idea", "").strip()

    if not idea:
        return jsonify({"error": "Idea text is required"}), 400

    judge_system = """
You are a **strict and critical VC analyst**. Do not give high scores easily. Be realistic and honest.

Return ONLY valid JSON in this exact format:

{
  "overall_score": number (40-88),
  "decision": "Strong Idea / Moderate Idea / Weak Idea",
  "elevator_pitch": "short powerful one line pitch",
  "investor_readiness_score": number (0-100),
  "risk_score": number (0-100),
  "innovation_score": number (0-100),
  "market_score": number (0-100),
  "business_score": number (0-100),
  "technology_score": number (0-100),
  "execution_score": number (0-100),
  "swot": {
    "strengths": ["point1", "point2"],
    "weaknesses": ["point1", "point2"],
    "opportunities": ["point1", "point2"],
    "threats": ["point1", "point2"]
  }
}
"""

    judge_res = call_groq_agent(judge_system, f"Give honest and critical analysis for this startup idea: {idea}")

    final_report = {
        "idea": idea,
        "judge_evaluation": {
            "overall_score": judge_res.get("overall_score", 55),
            "decision": judge_res.get("decision", "Moderate Idea"),
            "elevator_pitch": judge_res.get("elevator_pitch", "Needs significant improvement."),
            "investor_readiness_score": judge_res.get("investor_readiness_score", 50),
            "risk_score": judge_res.get("risk_score", 45),
            "innovation_score": judge_res.get("innovation_score", 60),
            "market_score": judge_res.get("market_score", 55),
            "business_score": judge_res.get("business_score", 50),
            "technology_score": judge_res.get("technology_score", 65),
            "execution_score": judge_res.get("execution_score", 45),
            "swot": judge_res.get("swot", {
                "strengths": ["Interesting concept"],
                "weaknesses": ["High execution risk"],
                "opportunities": ["Market potential"],
                "threats": ["Strong competition"]
            })
        }
    }

    try:
        doc = json.loads(json.dumps(final_report, default=json_serializable))
        result = history_collection.insert_one(doc)
        final_report["id"] = str(result.inserted_id)
    except Exception as e:
        print("DB Error:", e)

    return jsonify(final_report)

@app.route("/api/history", methods=["GET"])
def get_history():
    try:
        items = list(history_collection.find().sort("_id", -1).limit(5))
        for doc in items:
            doc["_id"] = str(doc["_id"])
        return jsonify(items)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(port=5000, debug=True)