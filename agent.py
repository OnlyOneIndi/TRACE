
from engine import run_research, ResearchVerificationError


def main():
    print("\n=== TRACE RESEARCH SYSTEM ===")

    question = input("\nWhat would you like to investigate?\n> ")

    try:
        report, saved_path = run_research(question)

        print("\n--- RESEARCH REPORT ---\n")
        print(report.model_dump_json(indent=2))

        print("\n[VERIFICATION PASSED]")
        print("Report saved to:", saved_path)

    except ResearchVerificationError as error:
        print("\n[VERIFICATION FAILED]")
        print(error)
        print("\nReport was not saved.")

    except Exception as error:
        print("\n[TRACE ERROR]")
        print(f"{type(error).__name__}: {error}")


if __name__ == "__main__":
    main()
