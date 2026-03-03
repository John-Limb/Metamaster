"""Tests for the /health/logs endpoint helper."""

import json


def test_tail_log_returns_empty_for_missing_file():
    from app.api.v1.health.endpoints import _tail_log

    result = _tail_log("nonexistent_file_xyz.log", 10)
    assert result == []


def test_tail_log_returns_last_n_lines(tmp_path):
    from app.api.v1.health.endpoints import _tail_log

    log_file = tmp_path / "test.log"
    entries = [
        json.dumps({"timestamp": f"2026-03-01T00:00:0{i}", "level": "INFO", "message": f"msg {i}"})
        for i in range(15)
    ]
    log_file.write_text("\n".join(entries), encoding="utf-8")
    result = _tail_log(str(log_file), 10)
    assert len(result) == 10
    assert result[-1]["message"] == "msg 14"
    assert result[0]["message"] == "msg 5"


def test_tail_log_returns_all_lines_when_fewer_than_n(tmp_path):
    from app.api.v1.health.endpoints import _tail_log

    log_file = tmp_path / "test.log"
    entries = [
        json.dumps({"timestamp": "2026-03-01T00:00:00", "level": "INFO", "message": "only line"})
    ]
    log_file.write_text("\n".join(entries), encoding="utf-8")
    result = _tail_log(str(log_file), 10)
    assert len(result) == 1
    assert result[0]["message"] == "only line"


def test_tail_log_skips_invalid_json_gracefully(tmp_path):
    from app.api.v1.health.endpoints import _tail_log

    log_file = tmp_path / "test.log"
    log_file.write_text(
        '{"timestamp": "t", "level": "INFO", "message": "ok"}\nnot json at all\n',
        encoding="utf-8",
    )
    result = _tail_log(str(log_file), 10)
    assert len(result) == 2
    assert result[0]["message"] == "ok"
    assert result[1]["level"] == "RAW"
    assert "not json at all" in result[1]["message"]


def test_tail_log_skips_blank_lines(tmp_path):
    from app.api.v1.health.endpoints import _tail_log

    log_file = tmp_path / "test.log"
    log_file.write_text(
        '{"timestamp": "t", "level": "INFO", "message": "line1"}\n\n\n',
        encoding="utf-8",
    )
    result = _tail_log(str(log_file), 10)
    assert len(result) == 1
