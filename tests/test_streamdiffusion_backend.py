import projection_mapping.streamdiffusion_backend as backend


def test_xformers_request_falls_back_when_module_missing(monkeypatch):
    monkeypatch.setattr(backend, "_module_available", lambda name: False)
    assert backend.resolve_acceleration("xformers") == "none"


def test_auto_uses_native_when_xformers_missing(monkeypatch):
    monkeypatch.setattr(backend, "_module_available", lambda name: False)
    assert backend.resolve_acceleration("auto") == "none"


def test_auto_prefers_xformers_when_available(monkeypatch):
    monkeypatch.setattr(backend, "_module_available", lambda name: name == "xformers")
    assert backend.resolve_acceleration("auto") == "xformers"
