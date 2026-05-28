from unittest.mock import Mock, patch


@patch("app.sheets.build")
@patch("app.sheets.gspread.authorize")
@patch("app.sheets.Credentials.from_service_account_file")
def test_update_result_writes_transcript_and_analysis(
    mock_creds,
    mock_authorize,
    mock_build,
):
    worksheet = Mock()
    worksheet.id = 123
    worksheet.col_values.side_effect = [
        ["date", "27.05.2025"],
        ["phone", "0993523475"],
    ]
    workbook = Mock()
    workbook.sheet1 = worksheet
    gc = Mock()
    gc.open_by_key.return_value = workbook
    mock_authorize.return_value = gc
    mock_build.return_value = Mock()

    from app.sheets import GoogleSheetsClient

    analysis = {
        "result": "ok",
        "greeting": 1,
        "politeness": 1,
        "identified_need": 1,
        "car_body": 1,
        "car_year": 1,
        "mileage": 1,
        "diagnostic_offer": 1,
        "closing": 1,
        "farewell": 1,
        "top_work": "Greeting",
        "total_score": 9,
        "comment": "fine",
        "bad_call": False,
    }

    GoogleSheetsClient().update_result(
        "2025-05-27_16-15_0993523475_incoming.mp3",
        "hello transcript",
        analysis,
    )

    worksheet.update.assert_called_once_with(
        range_name="U2:V2",
        values=[
            [
                "hello transcript",
                (
                    '{\n'
                    '  "result": "ok",\n'
                    '  "greeting": 1,\n'
                    '  "politeness": 1,\n'
                    '  "identified_need": 1,\n'
                    '  "car_body": 1,\n'
                    '  "car_year": 1,\n'
                    '  "mileage": 1,\n'
                    '  "diagnostic_offer": 1,\n'
                    '  "closing": 1,\n'
                    '  "farewell": 1,\n'
                    '  "top_work": "Greeting",\n'
                    '  "total_score": 9,\n'
                    '  "comment": "fine",\n'
                    '  "bad_call": false\n'
                    "}"
                ),
            ]
        ],
    )


@patch("app.sheets.build")
@patch("app.sheets.gspread.authorize")
@patch("app.sheets.Credentials.from_service_account_file")
def test_paint_red_uses_real_sheet_id(
    mock_creds,
    mock_authorize,
    mock_build,
):
    worksheet = Mock()
    worksheet.id = 987654
    workbook = Mock()
    workbook.sheet1 = worksheet
    gc = Mock()
    gc.open_by_key.return_value = workbook
    mock_authorize.return_value = gc
    service = Mock()
    mock_build.return_value = service

    from app.config import GOOGLE_SHEET_ID
    from app.sheets import GoogleSheetsClient

    client = GoogleSheetsClient()
    client.paint_red(4)

    service.spreadsheets.return_value.batchUpdate.assert_called_once_with(
        spreadsheetId=GOOGLE_SHEET_ID,
        body={
            "requests": [
                {
                    "repeatCell": {
                        "range": {
                            "sheetId": 987654,
                            "startRowIndex": 3,
                            "endRowIndex": 4,
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "backgroundColor": {
                                    "red": 1,
                                    "green": 0.8,
                                    "blue": 0.8
                                }
                            }
                        },
                        "fields": "userEnteredFormat.backgroundColor"
                    }
                }
            ]
        }
    )


@patch("app.sheets.build")
@patch("app.sheets.gspread.authorize")
@patch("app.sheets.Credentials.from_service_account_file")
def test_update_result_marks_bad_calls_red(
    mock_creds,
    mock_authorize,
    mock_build,
):
    worksheet = Mock()
    worksheet.id = 456
    worksheet.col_values.side_effect = [
        ["date", "27.05.2025"],
        ["phone", "0993523475"],
    ]
    workbook = Mock()
    workbook.sheet1 = worksheet
    gc = Mock()
    gc.open_by_key.return_value = workbook
    mock_authorize.return_value = gc
    service = Mock()
    mock_build.return_value = service

    from app.sheets import GoogleSheetsClient

    client = GoogleSheetsClient()
    client.update_result(
        "2025-05-27_16-15_0993523475_incoming.mp3",
        "hello transcript",
        {
            "bad_call": True,
        },
    )

    service.spreadsheets.return_value.batchUpdate.assert_called_once()
    worksheet.update.assert_called_once_with(
        range_name="U2:V2",
        values=[["hello transcript", '{\n  "bad_call": true\n}']],
    )
