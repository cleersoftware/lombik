from application import themes


def test_available_themes():
    theme_list = themes.available_themes()
    ids = {t["id"] for t in theme_list}
    assert "coral" in ids
    for theme in theme_list:
        assert "brand" in theme["light"]
        assert "brand" in theme["dark"]


def test_theme_css_shape():
    css = themes.theme_css()
    assert ":root" in css
    assert ".dark" in css
    assert "--brand" in css
    assert "--canvas" in css


def test_save_and_load_theme(monkeypatch, tmp_path):
    monkeypatch.setattr(themes, "THEME_FILE", tmp_path / "theme.json")

    assert themes.save_theme("ocean") is True
    assert themes.active_theme_id() == "ocean"

    # Unknown themes are rejected and the previous selection is kept.
    assert themes.save_theme("does-not-exist") is False
    assert themes.active_theme_id() == "ocean"
