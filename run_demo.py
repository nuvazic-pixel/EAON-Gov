import json
from eaon_gov.orchestrator import GovOrchestrator

def main():
    orchestrator = GovOrchestrator()
    final_state = orchestrator.run_scenario("scenarios/relocation.json")
    print(json.dumps(final_state, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
