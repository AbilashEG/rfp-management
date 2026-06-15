"""
Local test runner — runs the full RFP agent lifecycle end-to-end.
Usage: python -m agent.agent_runner
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.rfp_agent import rfp_agent

TEST_PROMPT = """
We need 500 units of ABS wheel speed sensors for our new vehicle platform.
The component category in our database is: sensors
Specs: High-precision ABS wheel speed sensor, IP67 rated,
operating temp -40C to 125C, connector type AMP Superseal.
Deadline: 2026-09-30.
Please find suppliers in the 'sensors' category, generate and send the RFP,
collect proposals, score them, and give me your top 2 recommendation.
"""

if __name__ == "__main__":
    print("=" * 60)
    print("SUPPLIER RFP MANAGEMENT AGENT — TEST RUN")
    print("=" * 60)
    response = rfp_agent(TEST_PROMPT)
    print("\nFINAL AGENT RESPONSE:")
    print(response)
