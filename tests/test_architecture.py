"""Structural contracts for the web-first application."""

from pathlib import Path

from bobbee import create_app

ROOT = Path(__file__).resolve().parent.parent


def test_factory_builds_independent_apps(tmp_path):
    first = create_app({"TESTING": True, "DATA_PATH": str(tmp_path / "one.json")})
    second = create_app({"TESTING": True, "DATA_PATH": str(tmp_path / "two.json")})
    assert first is not second
    assert first.extensions["bobbee.services"] is not second.extensions["bobbee.services"]
    assert {rule.rule for rule in first.url_map.iter_rules()} == {
        rule.rule for rule in second.url_map.iter_rules()
    }


def test_templates_compile_and_assets_are_packaged(app):
    templates = app.jinja_env.list_templates()
    assert "index.html" in templates
    assert "mocks/salesloft.html" in templates
    for template in templates:
        app.jinja_env.get_template(template)
    assert Path(app.static_folder, "css/design-system.css").is_file()
    assert Path(app.static_folder, "css/dashboard.css").is_file()
    assert Path(app.static_folder, "js/workflows.js").is_file()


def test_legacy_architecture_is_removed():
    removed = (
        "Account_Segmentation", "Account_Tiering", "Call_Planning",
        "ISC_Scraper_App", "IBM_Scraper_App", "shared_auth",
        "bobbee/runtime.py", "bobbee/routes",
    )
    assert all(not (ROOT / path).exists() for path in removed)
    launcher = (ROOT / "wsgi.py").read_text()
    assert "from bobbee import create_app" in launcher
    assert len(launcher.splitlines()) < 20


def test_http_layer_does_not_import_legacy_runtime():
    for path in (ROOT / "bobbee/api").glob("*.py"):
        source = path.read_text()
        assert "run_pipeline" not in source
        assert "subprocess" not in source
        assert "openpyxl" not in source
