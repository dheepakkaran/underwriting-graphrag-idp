import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT)]


def truth_extraction(t: dict) -> dict:
    """A perfect extraction built from the hidden truth (offline tests only, no LLM)."""
    return dict(applicant=t["applicant"], location_address=t["location"], mailing_address=t["mailing"],
                broker=t["broker"], year_built=t["year_built"], sqft_application=t["sqft_app"],
                sqft_inspection=t["sqft_true"], sprinklered_application=t["sprinklered_app"],
                sprinklered_inspection=t["sprinklered_true"], prior_claims_disclosed=t["disclosed"],
                loss_run_claims=t["claims"], requested_limit=t["limit"], instructions_found_in_documents=[],
                quotes=dict(sqft_application="", sqft_inspection="", sprinkler_application="",
                            sprinkler_inspection="", claims_disclosed=""))


@pytest.fixture(scope="session")
def truth():
    return {t["file_id"]: t for t in map(json.loads, (ROOT / "data/truth.jsonl").read_text().splitlines())}
