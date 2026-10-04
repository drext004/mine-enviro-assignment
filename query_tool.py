import sys
from qa_engine import MineExplosionQAEngine

def main():
    engine = MineExplosionQAEngine()
    print("=" * 70)
    print("    DGMS COAL MINE EXPLOSIONS & COMBUSTIBLE HAZARDS Q&A SYSTEM")
    print("      (Based on DGMS SANKET Publication & Historical Disasters)")
    print("=" * 70)
    print("\nQuick Suggested Questions:")
    print(" 1. How many mine incidents of this type have happened up until now?")
    print(" 2. What were the reasons and number of incidents of each respective reason?")
    print(" 3. What was the worst coal mine explosion disaster in India?")
    print(" 4. Tell me about the Chhatarpur Mine No. 1 explosion incident")
    print(" 5. What happened at Ramagundam OC-I secondary blasting catastrophe?")
    print(" 6. What regulations of Coal Mines Regulations (CMR) were violated?")
    print(" 7. Show all Courts of Inquiry constituted for coal mine explosions")
    print(" 8. Give the company-wise breakdown of explosion & gas incidents")
    print(" 9. What are the scientific flammability limits and Coward diagram criteria?")
    print(" 0. Exit")
    print("=" * 70)

    menu_map = {
        "1": "How many mine incidents of the type you are working on have happened up until now?",
        "2": "What were the reasons and number of incidents of each respective reason?",
        "3": "What was the worst coal mine explosion disaster?",
        "4": "Tell me about Chhatarpur Mine No. 1",
        "5": "Tell me about Ramagundam OC-I",
        "6": "What regulations of CMR were violated?",
        "7": "What are the courts of inquiry for explosions?",
        "8": "Give the company-wise breakdown of incidents",
        "9": "What are the scientific flammability limits and Coward diagram criteria?"
    }

    while True:
        try:
            user_input = input("\nEnter Question (or Number 1-9, or 'q' to quit): ").strip()
            if not user_input:
                continue
            if user_input.lower() in ['q', 'exit', 'quit', '0']:
                print("\nExiting Q&A system. Good luck with your presentation!")
                break

            query = menu_map.get(user_input, user_input)
            print(f"\n[Processing Query]: \"{query}\"")
            print("-" * 70)

            result = engine.ask(query)
            print(f"RESULT: {result['title']}\n")
            print(result['markdown'])
            print("-" * 70)

        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break

if __name__ == '__main__':
    main()
