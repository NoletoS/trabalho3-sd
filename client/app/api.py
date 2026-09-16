from __future__ import annotations

from pathlib import Path
from typing import Any

import requests


class ApiError(RuntimeError):
    pass


class MediaApi:
    def __init__(self, base_url: str = "http://127.0.0.1:8000") -> None:
        self.base_url = base_url.rstrip("/")

    def _check(self, response: requests.Response) -> requests.Response:
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            try:
                message = response.json().get("detail", response.text)
            except ValueError:
                message = response.text
            raise ApiError(str(message) or "Falha na comunicação com o servidor.") from exc
        return response

    def health(self) -> dict[str, Any]:
        response = requests.get(f"{self.base_url}/api/health", timeout=5)
        return self._check(response).json()

    def list_jobs(self) -> list[dict[str, Any]]:
        response = requests.get(f"{self.base_url}/api/jobs", timeout=10)
        return self._check(response).json()

    def create_job(self, file_path: str, operation: str) -> dict[str, Any]:
        path = Path(file_path)
        with path.open("rb") as stream:
            response = requests.post(
                f"{self.base_url}/api/jobs",
                data={"operation": operation},
                files={"media": (path.name, stream, "application/octet-stream")},
                timeout=(10, 600),
            )
        return self._check(response).json()

    def download(self, job_id: str, destination: str) -> str:
        response = requests.get(
            f"{self.base_url}/api/jobs/{job_id}/download",
            stream=True,
            timeout=(10, 600),
        )
        self._check(response)
        path = Path(destination)
        with path.open("wb") as target:
            for chunk in response.iter_content(1024 * 1024):
                if chunk:
                    target.write(chunk)
        return str(path)
