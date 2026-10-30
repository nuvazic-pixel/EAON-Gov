import json
from eaon_gov.orchestrator import GovOrchestrator


def main():
    print(json.dumps(GovOrchestrator().run_scenario(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
