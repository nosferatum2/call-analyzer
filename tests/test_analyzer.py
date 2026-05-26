import json
from unittest.mock import Mock, patch


@patch("app.analyzer.requests.post")
def test_analyze_adds_total_score(mock_post):
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

    from app.analyzer import CallAnalyzer

    result = CallAnalyzer().analyze("test transcript")

    assert result["total_score"] == 8
    response.raise_for_status.assert_called_once()
