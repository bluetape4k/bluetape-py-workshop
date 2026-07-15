import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_runnable_module_emits_contextual_log_and_deterministic_json() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "examples.order_intake"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == {
        "order_id": "order-1001",
        "partner_id": "partner-acme",
        "quantity": 2,
        "request_id": "request-1001",
        "sku": "SKU-BLUE-42",
        "status": "accepted",
    }
    assert "order_intake.accepted" in completed.stderr
    assert "request_id=request-1001" in completed.stderr
    assert "partner_id=partner-acme" in completed.stderr
    assert "order_id=order-1001" in completed.stderr
