"""The served UI shell: no pre-filled personal data and one cache-buster version for local assets."""

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "static"

PERSONAL_PHONE = "9390787901"
TEXT_SUFFIXES = {".py", ".js", ".html", ".css", ".svg", ".json"}


class TagCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))


def shell_tags():
    collector = TagCollector()
    collector.feed((STATIC / "index.html").read_text(encoding="utf-8"))
    return collector.tags


def local_asset_refs():
    """href/src of the stylesheets, icons and scripts the shell loads from /static."""
    refs = []
    for tag, attrs in shell_tags():
        if tag == "script":
            ref = attrs.get("src", "")
        elif tag == "link" and attrs.get("rel") in ("stylesheet", "icon"):
            ref = attrs.get("href", "")
        else:
            continue
        if ref.startswith("/static/"):
            refs.append(ref)
    return refs


def test_swiggy_phone_input_is_not_prefilled():
    inputs = [attrs for tag, attrs in shell_tags() if tag == "input" and attrs.get("id") == "swiggy-phone-input"]

    assert len(inputs) == 1
    assert "value" not in inputs[0]
    assert inputs[0]["placeholder"]


def test_served_code_hardcodes_no_personal_phone_number():
    hits = sorted(
        str(path.relative_to(ROOT))
        for folder in ("app", "static")
        for path in (ROOT / folder).rglob("*")
        if path.is_file()
        and path.suffix in TEXT_SUFFIXES
        and PERSONAL_PHONE in path.read_text(encoding="utf-8", errors="ignore")
    )

    assert hits == []


def test_local_assets_share_one_cache_buster_version():
    refs = local_asset_refs()
    versions = {parse_qs(urlparse(ref).query).get("v", [None])[0] for ref in refs}

    assert refs
    assert len(versions) == 1, f"mixed or missing ?v= across {refs}"
    assert None not in versions
