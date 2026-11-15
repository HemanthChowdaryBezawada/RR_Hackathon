from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_no_previous_placeholder_literals():
    """Prevent reintroducing fixed values from the pre-pressure_core pipeline."""
    forbidden = ("alpha_g=100", "0.10 *", "super-over rows | 6", "D/L or revised | 19")
    files = list((ROOT / "src").rglob("*.py")) + list((ROOT / "outputs").rglob("*"))
    for path in files:
        if path.is_file() and path.suffix in {".py", ".md", ".csv", ".txt"}:
            text = path.read_text(encoding="utf-8", errors="ignore")
            assert not any(token in text for token in forbidden), f"placeholder literal in {path}"
