import json
from unittest.mock import Mock, patch

import requests


@patch("app.analyzer.requests.post")
@patch("app.analyzer.Path.write_text")
@patch("app.analyzer.Path.mkdir")
@patch("app.analyzer.Path.exists")
def test_analyze_adds_total_score(
    mock_exists,
    mock_mkdir,
    mock_write_text,
    mock_post,
):
    payload = {
        "greeting": 1,
        "politeness": 1,
        "identified_need": 1,
        "car_body": 1,
        "car_year": 1,
        "mileage": 1,
        "diagnostic_offer": 0,
        "closing": 1,
        "farewell": 1,
        "result": "ok",
    }
    response = Mock()
    response.json.return_value = {"response": json.dumps(payload)}
    response.raise_for_status = Mock()
    mock_post.return_value = response

    mock_exists.return_value = False

    from app.analyzer import CallAnalyzer

    result = CallAnalyzer().analyze("test transcript", "call.mp3")

    assert result["total_score"] == 8
    mock_post.assert_called_once()
    assert mock_post.call_args.args[0] == "http://localhost:11434/api/generate"
    response.raise_for_status.assert_called_once()


@patch("app.analyzer.requests.post")
@patch("app.analyzer.Path.write_text")
@patch("app.analyzer.Path.mkdir")
@patch("app.analyzer.Path.exists")
def test_analyze_retries_timeout(
    mock_exists,
    mock_mkdir,
    mock_write_text,
    mock_post,
):
    payload = {
        "greeting": 1,
        "politeness": 1,
        "identified_need": 1,
        "car_body": 1,
        "car_year": 1,
        "mileage": 1,
        "diagnostic_offer": 1,
        "closing": 1,
        "farewell": 1,
        "result": "ok",
    }
    response = Mock()
    response.json.return_value = {"response": json.dumps(payload)}
    response.raise_for_status = Mock()
    mock_post.side_effect = [
        requests.Timeout("timed out"),
        response,
    ]

    mock_exists.return_value = False

    from app.analyzer import CallAnalyzer

    result = CallAnalyzer().analyze("test transcript", "call.mp3")

    assert result["total_score"] == 9
    assert mock_post.call_count == 2
