"""
main.py
-------
Entry point for the Sun Life health monitoring agent demo.

Run with:
    python main.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from data.mock_data import MARCUS, MARCUS_EXTENDED, SARAH, BASELINE
from data.simulator import generate_demo_sequence, describe_snapshot
from scoring.scorer import score
from agent.loop import run_agent


def run_demo_sequence():
    """Steps through Marcus's 7-day decline and shows risk escalating."""
    print("\n" + "=" * 60)
    print("DEMO: Watching Marcus's pattern emerge over 7 days")
    print("=" * 60)

    for snap in generate_demo_sequence(MARCUS):
        day = int(snap.user_id.split("_day")[1])
        result = score(snap)
        declining = ", ".join(s.name for s in result.declining_signals) or "none"
        print(f"\n{describe_snapshot(MARCUS, day)}")
        print(f"  Risk tier : {result.risk_tier.upper()}")
        print(f"  Declining : {declining}")
        print(f"  Days concern: {result.days_of_concern}")


def run_agent_demo(patient_name="marcus", province="ON", use_extended=False):
    """Runs the full agent loop and prints Claude's explanation."""
    patients = {
        "marcus":   MARCUS,
        "extended": MARCUS_EXTENDED,
        "sarah":    SARAH,
        "baseline": BASELINE,
    }

    payload = patients.get(patient_name.lower(), MARCUS)
    if use_extended:
        payload = MARCUS_EXTENDED

    print("\n" + "=" * 60)
    print(f"AGENT RUN: {payload.user_id}  |  Province: {province}")
    print("=" * 60)

    try:
        result = run_agent(payload, province=province, month=3)
        print(f"\nRisk tier : {result['risk_tier'].upper()}")
        print(f"Severity  : {result['severity']:.2f} / 1.00")
        print(f"Urgent    : {result['urgent']}")
        print(f"Days      : {result['days_concern']}")
        print("\n--- Agent Explanation ---\n")
        print(result["explanation"])
    except Exception as e:
        print(f"\nAgent call failed: {e}")
        print("\nFalling back to dry_run (no Claude call)...")
        result = run_agent(payload, province=province, month=3, dry_run=True)
        print(f"\nRisk tier : {result['risk_tier'].upper()}")
        print(f"Severity  : {result['severity']:.2f} / 1.00")
        print(f"Days      : {result['days_concern']}")
        print("\n[Add API credits at console.anthropic.com to see the full explanation]")


if __name__ == "__main__":
    # Step 1: show the pattern emerging over 7 days
    run_demo_sequence()

    # Step 2: run the full agent on Marcus extended (all 8 signals)
    run_agent_demo(province="ON", use_extended=True)
