from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import requests


class TelegramError(RuntimeError):
    pass


class TelegramBotAPI:
    def __init__(self, token: str, session: requests.Session | None = None) -> None:
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.file_base_url = f"https://api.telegram.org/file/bot{token}"
        self.session = session or requests.Session()

    def _request(self, method: str, payload: dict[str, Any] | None = None, files: dict[str, Any] | None = None) -> Any:
        response = self.session.post(f"{self.base_url}/{method}", data=payload, files=files, timeout=120)
        response.raise_for_status()
        data = response.json()
        if not data.get("ok"):
            raise TelegramError(data.get("description", f"Telegram API error in {method}"))
        return data["result"]

    def get_me(self) -> dict[str, Any]:
        return self._request("getMe")

    def get_sticker_set(self, name: str) -> dict[str, Any]:
        return self._request("getStickerSet", {"name": name})

    def get_file(self, file_id: str) -> dict[str, Any]:
        return self._request("getFile", {"file_id": file_id})

    def download_file(self, file_path: str, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        response = self.session.get(f"{self.file_base_url}/{file_path}", timeout=120)
        response.raise_for_status()
        destination.write_bytes(response.content)

    def create_new_sticker_set(
        self,
        user_id: int,
        name: str,
        title: str,
        sticker_path: Path,
        emoji_list: list[str],
    ) -> Any:
        sticker_payload = json.dumps(
            [
                {
                    "sticker": "attach://sticker_0",
                    "format": "video",
                    "emoji_list": emoji_list,
                }
            ]
        )
        with sticker_path.open("rb") as fh:
            return self._request(
                "createNewStickerSet",
                payload={
                    "user_id": str(user_id),
                    "name": name,
                    "title": title,
                    "stickers": sticker_payload,
                    "sticker_type": "regular",
                },
                files={"sticker_0": (sticker_path.name, fh, "video/webm")},
            )

    def add_sticker_to_set(self, user_id: int, name: str, sticker_path: Path, emoji_list: list[str]) -> Any:
        sticker_payload = json.dumps(
            {
                "sticker": "attach://sticker",
                "format": "video",
                "emoji_list": emoji_list,
            }
        )
        with sticker_path.open("rb") as fh:
            return self._request(
                "addStickerToSet",
                payload={
                    "user_id": str(user_id),
                    "name": name,
                    "sticker": sticker_payload,
                },
                files={"sticker": (sticker_path.name, fh, "video/webm")},
            )

