import json
from pathlib import Path

_BASE_DIR = Path(__file__).resolve().parent
_ABI_DIR = _BASE_DIR / "abis"


def _load_json_file(filename: str) -> dict:
    file_path = _ABI_DIR / filename

    if not file_path.exists():
        raise FileNotFoundError(f"ABI file not found: {file_path}")

    with file_path.open("r", encoding="utf-8") as f:
        return json.load(f)

@staticmethod
def factory_abi() -> dict:
    return _load_json_file("factory.json")


@staticmethod
def wallet_abi() -> dict:
    return _load_json_file("wallet.json")
