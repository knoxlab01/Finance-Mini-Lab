"""Read-only frozen specification, verified before any research calculation."""
import hashlib
import json
from pathlib import Path
from types import MappingProxyType

SPEC_VERSION = "1.1-frozen"
SPEC_SHA256 = "bea9d81702d4afe70a2d65d3fd1beb33c410eeefa0298cc2e5fe5d06e521e0b7"
SPEC_PATH = Path(__file__).resolve().parents[3] / "docs" / "evolance_v1_1_frozen_spec.json"


def _freeze(value):
    if isinstance(value, dict):
        return MappingProxyType({k: _freeze(v) for k, v in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(v) for v in value)
    return value


def load_spec(path=SPEC_PATH):
    content = path.read_bytes()
    if hashlib.sha256(content).hexdigest() != SPEC_SHA256:
        raise ValueError("Frozen specification hash mismatch; do not retune from results")
    value = json.loads(content)
    if value["version"] != SPEC_VERSION:
        raise ValueError("Wrong specification version")
    return _freeze(value)


SPEC = load_spec()
CORE = ("Growth Strength", "Downside Stability", "Diversification Quality", "Return Efficiency")
