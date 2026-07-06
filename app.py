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
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=60)
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

    # 1. Market Research Agent
    market_system = '''You are a Market Research expert. Return ONLY this JSON format with no markdown:
{"market_size": "estimated market size", "demand": "market demand level", "opportunity": "key opportunity", "target_market": "target customer segment", "growth_potential": "growth outlook", "key_insights": ["insight1", "insight2"]}'''
    market_res = call_groq_agent(
        market_system,
        f"Analyze market demand for this startup idea: {idea}"
    )

    # 2. Competitor Agent
    comp_system = '''You are a Competitor Analysis expert. Return ONLY this JSON format with no markdown:
{"main_competitors": "main competitors", "competition_level": "high/medium/low", "competitive_advantage": "key advantage", "differentiation": "how to differentiate", "market_gaps": "unmet needs", "threats": ["threat1", "threat2"]}'''
    comp_res = call_groq_agent(
        comp_system,
        f"Analyze competition for this idea: {idea}"
    )

    # 3. Risk & Revenue Agent
    risk_system = '''You are a Risk & Revenue VC expert. Return ONLY this JSON format with no markdown:
{"revenue_potential": "revenue model and potential", "main_risks": "primary risks", "risk_level": "high/medium/low", "mitigation": "mitigation strategies", "funding_needs": "funding requirements", "break_even_timeline": "timeline", "roi_projection": "ROI outlook"}'''
    risk_res = call_groq_agent(
        risk_system,
        f"Analyze risks and revenue potential for this idea: {idea}"
    )

    # 4. Judge Agent (Final Decision)
    judge_system = """
You are the final VC Judge. Return ONLY this JSON with all scores (0-100):
{
  "overall_score": number (50-88),
  "decision": "Strong Idea / Moderate Idea / Weak Idea",
  "elevator_pitch": "short powerful pitch",
  "investor_readiness_score": number,
  "innovation_score": number,
  "market_score": number,
  "business_score": number,
  "technology_score": number,
  "risk_score": number,
  "swot": {
    "strengths": ["..."],
    "weaknesses": ["..."],
    "opportunities": ["..."],
    "threats": ["..."]
  }
}
"""
    judge_res = call_groq_agent(judge_system, f"Idea: {idea}\nMarket: {json.dumps(market_res)}\nCompetitors: {json.dumps(comp_res)}\nRisk: {json.dumps(risk_res)}")

    final_report = {
        "idea": idea,
        "market_research": market_res,
        "competitor_analysis": comp_res,
        "risk_revenue": risk_res,
        "judge_evaluation": judge_res
    }

    try:
        doc = json.loads(json.dumps(final_report, default=str))
        result = history_collection.insert_one(doc)
        final_report["id"] = str(result.inserted_id)
    except Exception as e:
        print("DB Error:", e)

    return jsonify(final_report)

@app.route("/api/history", methods=["GET"])
def get_history():
    items = list(history_collection.find().sort("_id", -1).limit(10))
    for r in items:
        r["_id"] = str(r["_id"])
    return jsonify(items)

if __name__ == "__main__":
    app.run(port=5000, debug=True)