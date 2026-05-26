import gspread
from gspread.exceptions import APIError, SpreadsheetNotFound

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

from app.config import (
    GOOGLE_CREDS_FILE,
    GOOGLE_SHEET_ID
)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets"
]


class GoogleSheetsClient:
    def __init__(self):
        if not GOOGLE_SHEET_ID:
            raise ValueError("GOOGLE_SHEET_ID is not configured")

        creds = Credentials.from_service_account_file(
            GOOGLE_CREDS_FILE,
            scopes=SCOPES
        )

        gc = gspread.authorize(creds)

        try:
            self.sheet = gc.open_by_key(
                GOOGLE_SHEET_ID
            ).sheet1
        except SpreadsheetNotFound as exc:
            raise RuntimeError(
                "Google Sheet was not found. Verify GOOGLE_SHEET_ID and "
                "share the sheet with the service account."
            ) from exc
        except APIError as exc:
            raise RuntimeError(
                "Configured GOOGLE_SHEET_ID is not a native Google Sheet or "
                "the account cannot access it."
            ) from exc

        self.service = build(
            "sheets",
            "v4",
            credentials=creds
        )

    def append_result(
        self,
        filename,
        analysis
    ):
        row = [
            filename,
            analysis.get("result", ""),
            "",
            "",
            "",
            analysis.get("greeting", 0),
            analysis.get("car_body", 0),
            analysis.get("car_year", 0),
            analysis.get("mileage", 0),
            analysis.get("diagnostic_offer", 0),
            analysis.get("identified_need", 0),
            "",
            analysis.get("farewell", 0),
            analysis.get("top_work", ""),
            "",
            "",
            analysis.get("result", ""),
            analysis.get("total_score", 0),
            "",
            analysis.get("comment", "")
        ]

        self.sheet.append_row(row)

        last_row = len(self.sheet.get_all_values())

        if analysis.get("bad_call"):
            self.paint_red(last_row)

    def paint_red(self, row_index):
        requests = [
            {
                "repeatCell": {
                    "range": {
                        "sheetId": 0,
                        "startRowIndex": row_index - 1,
                        "endRowIndex": row_index,
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

        self.service.spreadsheets().batchUpdate(
            spreadsheetId=GOOGLE_SHEET_ID,
            body={"requests": requests}
        ).execute()
