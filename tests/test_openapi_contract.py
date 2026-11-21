"""OpenAPI contract tests (docs/openapi.yaml vs. the running app).

Keeps the published document honest without a live server: the documented
paths/methods must match the app's route table, and the repairs response
shape must match the ``Repair``/``RepairDetail`` schemas.
"""

import re
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SPEC_PATH = PROJECT_ROOT / "docs" / "openapi.yaml"

HTTP_METHODS = {"get", "put", "post", "delete", "patch"}


def _spec() -> dict:
    return yaml.safe_load(SPEC_PATH.read_text(encoding="utf-8"))


def _normalize(path: str) -> str:
    """Collapse path parameters to ``{}`` (names/converters differ by tool)."""
    path = re.sub(r"<(?:[^:>]+:)?[^>]+>", "{}", path)
    return re.sub(r"\{[^}]+\}", "{}", path)


def test_documented_paths_match_app_routes(app):
    spec = _spec()
    documented = {
        (_normalize(path), method.lower())
        for path, item in spec["paths"].items()
        for method in item
        if method in HTTP_METHODS
    }

    actual = set()
    for rule in app.url_map.iter_rules():
        if not str(rule).startswith("/api/v1"):
            continue
        for method in rule.methods - {"HEAD", "OPTIONS"}:
            actual.add((_normalize(str(rule)), method.lower()))

    assert documented == actual, (
        f"undocumented: {sorted(actual - documented)}; "
        f"documented but absent: {sorted(documented - actual)}"
    )


def test_repair_response_shape_matches_schemas(client, db):
    spec = _spec()["components"]["schemas"]
    repair_props = set(spec["Repair"]["properties"])
    detail_props = repair_props | set(spec["RepairDetail"]["allOf"][1]["properties"])

    created = client.post("/api/v1/repairs", json={"customer": 1, "vehicle": 1})
    assert created.status_code == 201
    assert set(created.get_json()) == detail_props

    listing = client.get("/api/v1/repairs").get_json()
    assert set(listing[0]) == repair_props

    detail = client.get(f"/api/v1/repairs/{listing[0]['id']}").get_json()
    assert set(detail) == detail_props


def test_export_content_type_matches_document(client, db):
    xlsx = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    documented = set(
        _spec()["paths"]["/api/v1/repairs/export"]["get"]["responses"]["200"]["content"]
    )
    assert documented == {xlsx}

    response = client.get("/api/v1/repairs/export")
    assert response.status_code == 200
    assert response.headers["Content-Type"].split(";")[0].strip() in documented
