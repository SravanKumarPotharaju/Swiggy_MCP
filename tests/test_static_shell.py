"""The served UI shell: no pre-filled personal data, one cache-buster version for local assets, and its favicon."""

import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from fastapi.testclient import TestClient

from app.main import app

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "static"

PERSONAL_PHONE = "9390787901"
TEXT_SUFFIXES = {".py", ".js", ".html", ".css", ".svg", ".json"}

FAVICON = STATIC / "favicon.svg"
TOKENS = STATIC / "css" / "rally-tokens.css"
HEX_COLOR = re.compile(r"#[0-9A-Fa-f]{6}\b")
RALLY_INK, RALLY_BLUE = "#101010", "#276EF1"


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


def hex_colors(path):
    return {color.upper() for color in HEX_COLOR.findall(path.read_text(encoding="utf-8"))}


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


def test_shell_links_the_svg_favicon_and_it_is_served():
    icons = [attrs for tag, attrs in shell_tags() if tag == "link" and attrs.get("rel") == "icon"]

    assert len(icons) == 1
    assert icons[0]["type"] == "image/svg+xml"
    assert icons[0]["href"].split("?")[0] == "/static/favicon.svg"

    res = TestClient(app).get(icons[0]["href"])
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("image/svg+xml")


def test_favicon_svg_is_drawn_in_rally_ink_and_blue_only():
    assert FAVICON.is_file()

    colors = hex_colors(FAVICON)
    assert colors == {RALLY_INK, RALLY_BLUE}
    assert colors <= hex_colors(TOKENS)


def test_favicon_ico_is_served_so_browsers_do_not_404():
    res = TestClient(app).get("/favicon.ico")

    assert res.status_code == 200
    assert res.headers["content-type"].startswith("image/svg+xml")
    assert res.content == FAVICON.read_bytes()
