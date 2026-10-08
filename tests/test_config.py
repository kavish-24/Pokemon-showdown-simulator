from src.config import load_config


def test_config_uses_environment(monkeypatch, tmp_path):
    monkeypatch.setenv("SHOWDOWN_WS_URL", "wss://example.ngrok-free.app/showdown/websocket")
    monkeypatch.setenv("SHOWDOWN_AUTH_URL", "https://example.ngrok-free.app")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    config = load_config()
    assert config.server[0].startswith("wss://")
    assert config.server[1] == "https://example.ngrok-free.app"
    assert config.data_dir == tmp_path
