from datetime import datetime, timedelta, timezone
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


def in_hours(hours: int) -> int:
    """Convert hours to a unix timestamp in the future."""
    return int((datetime.now(timezone.utc) + timedelta(hours=hours)).timestamp())

def in_days(days: int) -> int:
    """Convert days to a unix timestamp in the future."""
    return int((datetime.now(timezone.utc) + timedelta(days=days)).timestamp())

def at_datetime(dt: datetime) -> int:
    """Convert a datetime to a unix timestamp."""
    if dt.tzinfo is None:
        # Assume naive datetimes are in UTC
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp())