"""
app.py
------
Person D's Flask web server for the Sun Life health monitoring dashboard.

Serves:
  GET /                                    → UI dashboard (ui/index.html)
  GET /api/patients                        → list of available patient keys
  GET /api/provinces                       → list of Canadian province codes
  GET /api/score?patient=&province=&month= → scored health payload (JSON)
  GET /api/sequence?patient=               → 7-day demo escalation sequence
  GET /api/agent?patient=&province=        → Claude agent explanation

Run with:
    pip install flask
    python app.py
"""

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, jsonify, request, send_from_directory
from dotenv import load_dotenv

from data.mock_data import MARCUS, MARCUS_EXTENDED, SARAH, BASELINE
from data.simulator import generate_demo_sequence, get_payload_at_day
from scoring.scorer import score, score_with_severity
from scoring.thresholds import PROVINCE_811_GUIDANCE
from agent.context import build_canadian_context
from agent.loop import run_agent, URGENT_SIGNALS

load_dotenv()

app = Flask(__name__, static_folder="ui", static_url_path="/ui")

PATIENTS = {
    "marcus":          MARCUS,
    "marcus_extended": MARCUS_EXTENDED,
    "sarah":           SARAH,
    "baseline":        BASELINE,
}

PATIENT_LABELS = {
    "marcus":          "Marcus (4 signals)",
    "marcus_extended": "Marcus Extended (8 signals)",
    "sarah":           "Sarah (low risk)",
    "baseline":        "Baseline (healthy)",
}


# ---------------------------------------------------------------------------
# Static
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return send_from_directory("ui", "index.html")


# ---------------------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------------------

@app.route("/api/patients")
def list_patients():
    return jsonify([
        {"key": k, "label": PATIENT_LABELS[k]} for k in PATIENTS
    ])


@app.route("/api/provinces")
def list_provinces():
    return jsonify(sorted(PROVINCE_811_GUIDANCE.keys()))


# ---------------------------------------------------------------------------
# Score endpoint
# ---------------------------------------------------------------------------

@app.route("/api/score")
def get_score():
    patient_name = request.args.get("patient", "marcus_extended")
    province     = request.args.get("province", "ON")
    month        = int(request.args.get("month", 3))
    day          = request.args.get("day")  # optional: view data as of day N

    payload = PATIENTS.get(patient_name, MARCUS_EXTENDED)

    if day is not None:
        try:
            payload = get_payload_at_day(payload, int(day))
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

    result, severity = score_with_severity(payload)

    canadian_ctx = build_canadian_context(province, month)

    declining_names = {s.name for s in result.declining_signals}

    signals_data = []
    for name, sig in result.all_signals.items():
        raw_values = (
            payload.signals[name].values
            if name in payload.signals else []
        )
        signals_data.append({
            "name":                    name,
            "today":                   round(sig.today, 4),
            "baseline":                round(sig.baseline, 4),
            "trend":                   round(sig.trend, 4),
            "consecutive_decline_days": sig.consecutive_decline_days,
            "unit":                    sig.unit,
            "declining":               name in declining_names,
            "urgent":                  name in URGENT_SIGNALS and name in declining_names,
            "raw_values":              [round(v, 4) for v in raw_values],
        })

    return jsonify({
        "user_id":     result.user_id,
        "risk_tier":   result.risk_tier,
        "severity":    round(severity, 3),
        "days_concern": result.days_of_concern,
        "urgent":      any(s.name in URGENT_SIGNALS for s in result.declining_signals),
        "signals":     signals_data,
        "canadian_context": {
            "province":       canadian_ctx.province,
            "month":          canadian_ctx.month,
            "vitamin_d_risk": canadian_ctx.vitamin_d_risk,
            "call_811":       canadian_ctx.call_811,
        },
    })


# ---------------------------------------------------------------------------
# Sequence endpoint (demo animation)
# ---------------------------------------------------------------------------

@app.route("/api/sequence")
def get_sequence():
    patient_name = request.args.get("patient", "marcus")
    payload = PATIENTS.get(patient_name, MARCUS)

    sequence = []
    for snap in generate_demo_sequence(payload, days=[1, 2, 3, 4, 5, 6, 7]):
        day = int(snap.user_id.split("_day")[1])
        result, severity = score_with_severity(snap)
        declining_names = [s.name for s in result.declining_signals]

        # Per-signal data at this day for sparkline animation
        signals_at_day = []
        for name, sig in result.all_signals.items():
            raw_values = (
                snap.signals[name].values
                if name in snap.signals else []
            )
            signals_at_day.append({
                "name":      name,
                "today":     round(sig.today, 4),
                "baseline":  round(sig.baseline, 4),
                "trend":     round(sig.trend, 4),
                "declining": name in declining_names,
                "raw_values": [round(v, 4) for v in raw_values],
            })

        sequence.append({
            "day":         day,
            "risk_tier":   result.risk_tier,
            "severity":    round(severity, 3),
            "days_concern": result.days_of_concern,
            "declining":   declining_names,
            "signals":     signals_at_day,
        })

    return jsonify(sequence)


# ---------------------------------------------------------------------------
# Agent endpoint
# ---------------------------------------------------------------------------

@app.route("/api/agent")
def get_agent():
    patient_name = request.args.get("patient", "marcus_extended")
    province     = request.args.get("province", "ON")
    month        = int(request.args.get("month", 3))

    payload = PATIENTS.get(patient_name, MARCUS_EXTENDED)

    try:
        result = run_agent(payload, province=province, month=month)
        result["error"] = None
    except Exception as e:
        result = run_agent(payload, province=province, month=month, dry_run=True)
        result["error"] = str(e)
        result["explanation"] = (
            "[Claude API unavailable — add credits at console.anthropic.com "
            "to see the full AI explanation]\n\n"
            "--- Prompt that would have been sent ---\n\n"
            + result.get("prompt", "")
        )

    return jsonify(result)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("\n Sun Life Health Monitor — Person D Dashboard")
    print(" Open http://localhost:5000 in your browser\n")
    app.run(debug=True, port=5000)
