"""
AI Sage Financial Coach — CLI entry point for quick testing.

Usage:
    python hello.py

This runs a terminal chat loop against the coaching agent using
the demo customer profile. Useful for rapid iteration without
starting the full API or Streamlit UI.
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

# Verify environment
if not (os.getenv("OPENAI_API_KEY") or os.getenv("AZURE_OPENAI_API_KEY")):
    print("\n[ERROR] No API key found.")
    print("Copy .env.example to .env and add your OPENAI_API_KEY.\n")
    sys.exit(1)

from coaching_agent.agent import CoachingAgent
from data.mock_transactions import get_demo_customer


def main():
    print("\n" + "=" * 60)
    print("  AI Sage Financial Coach (MVP Demo)")
    print("=" * 60)
    print("  Type 'quit' to exit | 'reset' to start a new session")
    print("=" * 60 + "\n")

    profile = get_demo_customer()
    agent = CoachingAgent(profile)

    print(f"Session started for: {profile.name} ({profile.customer_id})")
    print("Building knowledge base...", end=" ", flush=True)

    # Warm up knowledge base
    from coaching_agent.tools.knowledge_base import get_knowledge_base
    get_knowledge_base()
    print("Done.\n")

    print("Coach: Hi Alex! I'm AI Sage, your financial coach. How can I help you today?\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nSession ended. Goodbye!")
            break

        if not user_input:
            continue
        if user_input.lower() == "quit":
            print("Goodbye!")
            break
        if user_input.lower() == "reset":
            agent = CoachingAgent(get_demo_customer())
            print("Coach: Session reset. How can I help you?\n")
            continue

        print("\nCoach: ", end="", flush=True)
        response = agent.chat(user_input)
        print(response + "\n")


if __name__ == "__main__":
    main()
