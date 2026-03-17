from infra_guide.preferences import PreferencesStore


def test_preferences_store_persists_theme_and_history(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    store = PreferencesStore()
    store.set_theme("forest")
    store.record_execution("plan", ["-out=tfplan"], "tofu plan -out=tfplan", "/tmp/app", 0)

    reloaded = PreferencesStore()

    assert reloaded.get_theme_name() == "forest"
    history = reloaded.get_history(limit=1)
    assert len(history) == 1
    assert history[0]["command_name"] == "plan"
    assert history[0]["args"] == ["-out=tfplan"]


def test_toggle_favorite_round_trip(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    store = PreferencesStore()
    enabled = store.toggle_favorite("plan", ["-out=tfplan"], "tofu plan -out=tfplan")
    disabled = store.toggle_favorite("plan", ["-out=tfplan"], "tofu plan -out=tfplan")

    assert enabled is True
    assert disabled is False
    assert store.get_favorites() == []
