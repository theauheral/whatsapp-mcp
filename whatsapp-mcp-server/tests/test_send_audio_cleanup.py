"""send_audio_message converts non-.ogg input to a temp file that must be
removed after the bridge call, on both success and failure paths."""

import os

import pytest

import whatsapp


class _Resp:
    def __init__(self, status_code=200, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload or {"success": True, "message": "ok"}
        self.text = text

    def json(self):
        return self._payload


@pytest.mark.parametrize("status_code", [200, 500])
def test_send_audio_removes_converted_temp_file(tmp_path, monkeypatch, status_code):
    src = tmp_path / "voice.mp3"
    src.write_bytes(b"not really mp3")
    converted = tmp_path / "converted.ogg"

    def fake_convert(path):
        converted.write_bytes(b"ogg")
        return str(converted)

    monkeypatch.setattr(whatsapp.audio, "convert_to_opus_ogg_temp", fake_convert)
    monkeypatch.setattr(whatsapp.requests, "post", lambda *a, **k: _Resp(status_code=status_code))

    whatsapp.send_audio_message("12025551234", str(src))

    assert not os.path.exists(converted)
    assert src.exists()  # the caller's original file is never touched


def test_send_audio_leaves_native_ogg_in_place(tmp_path, monkeypatch):
    src = tmp_path / "voice.ogg"
    src.write_bytes(b"ogg")
    monkeypatch.setattr(whatsapp.audio, "convert_to_opus_ogg_temp", lambda p: pytest.fail("must not convert .ogg"))
    monkeypatch.setattr(whatsapp.requests, "post", lambda *a, **k: _Resp())

    ok, _ = whatsapp.send_audio_message("12025551234", str(src))

    assert ok is True
    assert src.exists()
