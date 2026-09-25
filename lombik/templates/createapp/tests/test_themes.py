from application import themes


def _palette(prefix):
    return {
        token: f"#{prefix}{i:06x}"[:7]
        for i, token in enumerate(themes.TOKENS)
    }


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


def test_create_and_delete_custom_theme(monkeypatch, tmp_path):
    monkeypatch.setattr(themes, "THEME_FILE", tmp_path / "theme.json")

    light = _palette("a")
    dark = _palette("b")

    ok, error = themes.create_theme("My Brand", light, dark)
    assert ok is True and error is None
    assert themes.active_theme_id() == "my-brand"
    assert themes.is_custom("my-brand") is True

    assert themes.delete_theme("my-brand") is True
    assert themes.is_custom("my-brand") is False
    assert themes.active_theme_id() == themes.DEFAULT_THEME
