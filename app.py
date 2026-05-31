"""
MediExplain — Flask Web Application
"""
from dotenv import load_dotenv
load_dotenv()          # ← add this line — loads your .env file

import os
from flask import Flask, render_template, request, jsonify, session
import uuid

from agent import run_agent

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "mediexplain-dev-secret-2024")

MODELS = ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"]

@app.route("/")
def index():
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())[:8]
    return render_template("index.html", models=MODELS)

@app.route("/explain", methods=["POST"])
def explain():
    data = request.get_json()
    query      = data.get("query", "").strip()
    sex        = data.get("sex", "both")
    model      = data.get("model", "gpt-3.5-turbo")
    session_id = session.get("session_id", "demo")

    if not query:
        return jsonify({"success": False, "message": "Please enter your lab results."})

    if not os.environ.get("GROQ_API_KEY"):
        return jsonify({
            "success": False,
            "message": "OpenAI API key not set. Please add OPENAI_API_KEY to your .env file."
        })

    result = run_agent(query, sex=sex, model=model, session_id=session_id)
    return jsonify(result)

@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "MediExplain"})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
