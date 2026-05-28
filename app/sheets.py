import json
import re
from datetime import datetime
from pathlib import Path

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
            self.sheet_id = self.sheet.id
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

    def update_result(
        self,
        filename,
        transcript,
        analysis
    ):
        row_index = self._find_row_index(filename)

        if analysis.get("bad_call"):
            self.paint_red(row_index)

        self.sheet.update(
            range_name=f"U{row_index}:V{row_index}",
            values=[[
                transcript,
                json.dumps(
                    analysis,
                    ensure_ascii=False,
                    indent=2
                )
            ]]
        )

    def _find_row_index(self, filename: str) -> int:
        call_date, phone = self._parse_filename(filename)
        normalized_phone = self._normalize_phone(phone)

        date_values = self.sheet.col_values(1)
        phone_values = self.sheet.col_values(3)

        max_rows = max(len(date_values), len(phone_values))
        same_date_rows = []
        same_phone_rows = []

        for index in range(2, max_rows + 1):
            row_date = (
                date_values[index - 1].strip()
                if index - 1 < len(date_values) else ""
            )
            row_phone = (
                phone_values[index - 1].strip()
                if index - 1 < len(phone_values) else ""
            )
            normalized_row_phone = self._normalize_phone(row_phone)

            if row_date == call_date:
                same_date_rows.append(
                    {
                        "row": index,
                        "date": row_date,
                        "phone": row_phone,
                    }
                )

            if normalized_row_phone == normalized_phone:
                same_phone_rows.append(
                    {
                        "row": index,
                        "date": row_date,
                        "phone": row_phone,
                    }
                )

            if (
                row_date == call_date and
                normalized_row_phone == normalized_phone
            ):
                return index

        raise RuntimeError(
            "Row not found for "
            f"date {call_date} and phone {phone} from file {filename}. "
            f"Rows with same date: {same_date_rows[:5]}. "
            f"Rows with same phone: {same_phone_rows[:5]}."
        )

    @staticmethod
    def _parse_filename(filename: str) -> tuple[str, str]:
        stem = Path(filename).stem
        match = re.match(
            r"(?P<date>\d{4}-\d{2}-\d{2})_\d{2}-\d{2}_(?P<phone>\d+)",
            stem
        )

        if not match:
            raise RuntimeError(
                f"Cannot parse date and phone from filename: {filename}"
            )

        formatted_date = datetime.strptime(
            match.group("date"),
            "%Y-%m-%d"
        ).strftime("%d.%m.%Y")

        return formatted_date, match.group("phone")

    @staticmethod
    def _normalize_phone(phone: str) -> str:
        digits = re.sub(r"\D", "", phone)
        return digits[-10:]

    def paint_red(self, row_index):
        requests = [
            {
                "repeatCell": {
                    "range": {
                        "sheetId": self.sheet_id,
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
