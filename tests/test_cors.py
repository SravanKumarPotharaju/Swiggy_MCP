"""CORS policy: only allow-listed origins may make credentialed cross-origin requests."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import Settings
from app.main import app

REPO_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:3000",
]
# Origins a "reflect any origin" bug would wrongly trust: an arbitrary site, the opaque
# "null" origin (sandboxed iframes, file://), and look-alikes of an allowed origin.
UNTRUSTED_ORIGINS = [
    "https://evil.example",
    "null",
    "http://localhost:3000.evil.example",
    "http://localhost:3001",
]
RENDER_URL = "https://smartflow-abc.onrender.com"


@pytest.fixture(scope="module")
def client():
    # Not entered as a context manager, so the lifespan (MongoDB/Redis connect) never starts.
    return TestClient(app)


@pytest.fixture
def cors_env(monkeypatch):
    """monkeypatch with the CORS-related variables cleared, so Settings reads only what a test sets."""
    monkeypatch.delenv("CORS_ALLOWED_ORIGINS", raising=False)
    monkeypatch.delenv("RENDER_EXTERNAL_URL", raising=False)
    return monkeypatch


def preflight(client, origin, method="POST", request_headers="content-type"):
    return client.options(
        "/api/v1/cart",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": method,
            "Access-Control-Request-Headers": request_headers,
        },
    )


# --- the running app: who gets Access-Control-Allow-Origin -------------------------------


@pytest.mark.parametrize("origin", DEFAULT_ORIGINS)
def test_default_origin_preflight_is_allowed_with_credentials(client, origin):
    response = preflight(client, origin)

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin
    assert response.headers["access-control-allow-credentials"] == "true"


@pytest.mark.parametrize("origin", DEFAULT_ORIGINS)
def test_default_origin_simple_request_echoes_origin(client, origin):
    response = client.get("/health", headers={"Origin": origin})

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin
    assert response.headers["access-control-allow-credentials"] == "true"


def test_allowed_origin_can_read_the_request_id_and_timing_headers(client):
    response = client.get("/health", headers={"Origin": "http://localhost:3000"})

    exposed = response.headers["access-control-expose-headers"]
    assert "X-Request-ID" in exposed
    assert "X-Process-Time" in exposed


@pytest.mark.parametrize("origin", UNTRUSTED_ORIGINS)
def test_untrusted_origin_preflight_gets_no_allow_origin(client, origin):
    response = preflight(client, origin)

    assert "access-control-allow-origin" not in response.headers


@pytest.mark.parametrize("origin", UNTRUSTED_ORIGINS)
def test_untrusted_origin_simple_request_gets_no_allow_origin(client, origin):
    response = client.get("/health", headers={"Origin": origin})

    assert "access-control-allow-origin" not in response.headers


# --- the running app: methods and headers are an allow-list, not a wildcard --------------


@pytest.mark.parametrize("method", ["GET", "POST", "PUT", "PATCH", "DELETE"])
def test_preflight_allows_the_methods_the_api_uses(client, method):
    response = preflight(client, "http://localhost:3000", method=method)

    assert response.status_code == 200


def test_preflight_allows_the_headers_clients_send(client):
    response = preflight(
        client, "http://localhost:3000", request_headers="content-type, authorization, x-request-id"
    )

    assert response.status_code == 200


def test_preflight_rejects_a_method_the_api_does_not_use(client):
    response = preflight(client, "http://localhost:3000", method="HEAD")

    assert response.status_code == 400


def test_preflight_rejects_a_header_the_app_does_not_use(client):
    response = preflight(client, "http://localhost:3000", request_headers="x-evil-header")

    assert response.status_code == 400


# --- same-origin flow keeps working -------------------------------------------------------


def test_same_origin_ui_flow_still_works(client):
    # The UI is served from "/" and calls the API on the same host. Browsers attach an Origin
    # header to same-origin POSTs; that origin is not in the allow-list yet must be served.
    page = client.get("/")
    api = client.get("/health", headers={"Origin": "http://testserver"})

    assert page.status_code == 200
    assert api.status_code == 200
    assert api.json()["status"] == "ok"


# --- settings: parsing CORS_ALLOWED_ORIGINS and merging RENDER_EXTERNAL_URL ---------------


def test_comma_separated_origins_are_parsed_and_normalized(cors_env):
    cors_env.setenv("CORS_ALLOWED_ORIGINS", " https://a.example , https://b.example/ ,")

    origins = Settings(_env_file=None).CORS_ALLOWED_ORIGINS

    assert origins == ["https://a.example", "https://b.example"]


def test_origins_are_read_from_a_dotenv_file(cors_env, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("CORS_ALLOWED_ORIGINS=https://a.example,https://b.example\n")

    origins = Settings(_env_file=env_file).CORS_ALLOWED_ORIGINS

    assert origins == ["https://a.example", "https://b.example"]


def test_render_external_url_is_added_to_the_default_origins(cors_env):
    cors_env.setenv("RENDER_EXTERNAL_URL", RENDER_URL + "/")

    origins = Settings(_env_file=None).CORS_ALLOWED_ORIGINS

    assert RENDER_URL in origins
    assert "http://localhost:3000" in origins


def test_render_external_url_is_added_to_explicit_origins(cors_env):
    cors_env.setenv("CORS_ALLOWED_ORIGINS", "https://a.example")
    cors_env.setenv("RENDER_EXTERNAL_URL", RENDER_URL)

    origins = Settings(_env_file=None).CORS_ALLOWED_ORIGINS

    assert origins == ["https://a.example", RENDER_URL]


def test_render_external_url_is_not_added_twice(cors_env):
    cors_env.setenv("CORS_ALLOWED_ORIGINS", f"https://a.example,{RENDER_URL}/")
    cors_env.setenv("RENDER_EXTERNAL_URL", RENDER_URL)

    origins = Settings(_env_file=None).CORS_ALLOWED_ORIGINS

    assert origins == ["https://a.example", RENDER_URL]


@pytest.mark.parametrize("blank", ["", "   "])
def test_blank_render_external_url_adds_no_origin(cors_env, blank):
    cors_env.setenv("CORS_ALLOWED_ORIGINS", "https://a.example")
    cors_env.setenv("RENDER_EXTERNAL_URL", blank)

    origins = Settings(_env_file=None).CORS_ALLOWED_ORIGINS

    assert origins == ["https://a.example"]


@pytest.mark.parametrize("value", ["*", "https://a.example,*"])
def test_wildcard_origin_is_rejected_because_credentials_are_enabled(cors_env, value):
    cors_env.setenv("CORS_ALLOWED_ORIGINS", value)

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


# --- end to end: RENDER_EXTERNAL_URL reaches the running app ------------------------------

_PROBE = """
import json, sys
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
allow_origin = {}
for origin in sys.argv[1:]:
    response = client.options(
        "/api/v1/cart",
        headers={"Origin": origin, "Access-Control-Request-Method": "POST"},
    )
    allow_origin[origin] = response.headers.get("access-control-allow-origin")
print(json.dumps(allow_origin))
"""


def test_render_external_url_origin_is_allowed_by_the_running_app(tmp_path):
    # The allow-list is fixed when app.main is imported, so run the real app in a fresh
    # interpreter with a controlled environment (empty cwd: no .env file is picked up).
    env = {k: v for k, v in os.environ.items() if k not in ("CORS_ALLOWED_ORIGINS", "RENDER_EXTERNAL_URL")}
    env["RENDER_EXTERNAL_URL"] = RENDER_URL
    env["PYTHONPATH"] = os.pathsep.join(p for p in (str(REPO_ROOT), os.environ.get("PYTHONPATH")) if p)

    probe = subprocess.run(
        [sys.executable, "-c", _PROBE, RENDER_URL, "https://evil.example"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )

    assert probe.returncode == 0, probe.stderr
    assert json.loads(probe.stdout.splitlines()[-1]) == {
        RENDER_URL: RENDER_URL,
        "https://evil.example": None,
    }
