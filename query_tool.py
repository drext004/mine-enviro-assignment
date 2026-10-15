import sys
from qa_engine import MineExplosionQAEngine
from chat_agent import MineSafetyChatAgent

def main():
    engine = MineExplosionQAEngine()
    agent = MineSafetyChatAgent()

    print("=" * 75)
    print("    DGMS COAL MINE EXPLOSIONS & SAFETY CONVERSATIONAL INTELLIGENCE")
    print("      (Based on DGMS SANKET Publication & Historical Disasters)")
    print("=" * 75)
    print("\nOperational AI Agent Modes:")
    print(" W. 👷 Worker Transfer Safety Advisory (Enter target mine & worker role)")
    print(" R. 🛠️ Project Manager / Mining Engineer Revisit Plan (Enter mine name)")
    print(" A. ⚖️ DGMS Statutory Audit (CMR violations & Section 24 inquiries)")
    print(" S. 🔬 Explosion Dynamics & Coward Diagram Science")
    print("\nQuick Suggested Questions:")
    print(" 1. How many mine incidents of this type have happened up until now?")
    print(" 2. What were the reasons and number of incidents of each respective reason?")
    print(" 3. What was the worst coal mine explosion disaster in India?")
    print(" 4. Tell me about Chhatarpur Mine No. 1 explosion incident")
    print(" 5. What happened at Ramagundam OC-I secondary blasting catastrophe?")
    print(" 6. What regulations of Coal Mines Regulations (CMR) were violated?")
    print(" 7. Show all Courts of Inquiry constituted for coal mine explosions")
    print(" 8. Give the company-wise breakdown of explosion & gas incidents")
    print(" 9. What are the scientific flammability limits and Coward diagram criteria?")
    print(" 0. Exit")
    print("=" * 75)

    menu_map = {
        "1": ("How many mine incidents of the type you are working on have happened up until now?", "sql"),
        "2": ("What were the reasons and number of incidents of each respective reason?", "sql"),
        "3": ("What was the worst coal mine explosion disaster?", "sql"),
        "4": ("Tell me about Chhatarpur Mine No. 1", "sql"),
        "5": ("Tell me about Ramagundam OC-I", "sql"),
        "6": ("What regulations of CMR were violated?", "sql"),
        "7": ("What are the courts of inquiry for explosions?", "sql"),
        "8": ("Give the company-wise breakdown of incidents", "sql"),
        "9": ("What are the scientific flammability limits and Coward diagram criteria?", "science")
    }

    while True:
        try:
            user_input = input("\nEnter Choice (W, R, A, S, 1-9, or custom question, '0' to quit): ").strip()
            if not user_input:
                continue
            if user_input.lower() in ['q', 'exit', 'quit', '0']:
                print("\nExiting. Good luck with your presentation!")
                break

            ui_upper = user_input.upper()
            if ui_upper == 'W':
                target_mine = input("  Enter target mine name (e.g. Kurasia, Chhatarpur, Bagdewa, Dhori): ").strip()
                role = input("  Enter your job role (e.g. Driller, Loader, Shotfirer, Sirdar): ").strip() or "Miner"
                q = f"I am a {role} transferred to {target_mine}. What dangers am I exposed to and what are my pre-shift checks?"
                print(f"\n[Worker Transfer Agent Active]: Analyzing {target_mine} for {role}...")
                print("-" * 75)
                res = agent.chat(q, persona="worker")
                print(res["reply"])
                print("-" * 75)
                continue

            elif ui_upper == 'R':
                target_mine = input("  Enter colliery name for revisit plan (e.g. Bagdewa, Ramagundam, Dipka): ").strip()
                q = f"Formulate an operational revisit and re-entry safety plan for {target_mine}"
                print(f"\n[Project Manager Agent Active]: Formulating 5-phase plan for {target_mine}...")
                print("-" * 75)
                res = agent.chat(q, persona="manager")
                print(res["reply"])
                print("-" * 75)
                continue

            elif ui_upper == 'A':
                q = "Show all statutory CMR violations and Courts of Inquiry under Section 24"
                res = agent.chat(q, persona="auditor")
                print("-" * 75)
                print(res["reply"])
                print("-" * 75)
                continue

            elif ui_upper == 'S':
                q = "Explain explosion dynamics, methane flammability limits, and Coward diagram"
                res = agent.chat(q, persona="science")
                print("-" * 75)
                print(res["reply"])
                print("-" * 75)
                continue

            # Standard numbered lookup or free-text query
            if user_input in menu_map:
                query, engine_type = menu_map[user_input]
                result = engine.ask(query)
                print(f"\nRESULT: {result['title']}\n")
                print(result['markdown'])
            else:
                # Custom free-form question dispatched to Chat Agent
                print(f"\n[Autonomous Chat Agent Dispatch]: \"{user_input}\"")
                print("-" * 75)
                res = agent.chat(user_input, persona="auto")
                print(res["reply"])

            print("-" * 75)

        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break

if __name__ == '__main__':
    main()
