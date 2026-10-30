"""Smoke an installed wheel from outside its source checkout (stdlib only)."""
import argparse
import importlib.metadata
import json
from pathlib import Path
import tempfile

import eaon_gov
from eaon_gov.orchestrator import GovOrchestrator


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-root", required=True, type=Path)
    args = parser.parse_args()
    installed_root = args.expected_root.resolve()
    module_path = Path(eaon_gov.__file__).resolve()
    source_root = Path(__file__).resolve().parents[1]
    if not module_path.is_relative_to(installed_root):
        raise RuntimeError(f"Expected installed package under {installed_root}, got {module_path}")
    if Path.cwd().resolve().is_relative_to(source_root):
        raise RuntimeError("Run this smoke check from outside the source checkout")
    with tempfile.TemporaryDirectory(prefix="eaon-gov-smoke-", dir=Path.cwd()) as temp:
        audit_path = Path(temp) / "audit.jsonl"
        result = GovOrchestrator(audit_path=str(audit_path)).run_scenario()
        expected_services = {"residence_registration", "tax_address", "vehicle_registration", "family_services"}
        if set(result["services"]) != expected_services or result["execution_status"] != "PARTIAL":
            raise RuntimeError("Packaged default scenario returned unexpected services or status")
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
        if audit["state_hash"] != result["state_hash"] or audit["trace_id"] != result["trace_id"]:
            raise RuntimeError("Installed default scenario did not persist matching audit state")
    print(json.dumps({
        "imported_from": str(module_path),
        "working_directory": str(Path.cwd().resolve()),
        "installed_version": importlib.metadata.version("eaon-gov"),
        "services": sorted(expected_services),
        "execution_status": result["execution_status"],
        "audit": "verified in temporary directory",
    }, indent=2))


if __name__ == "__main__":
    main()
