"""Ponto de entrada do servidor FastAPI.

Aceita tanto ``python main.py`` quanto ``uvicorn main:app``.
"""

import os
import sys
from pathlib import Path

server_dir = str(Path(__file__).resolve().parent)
if server_dir not in sys.path:
    sys.path.insert(0, server_dir)

try:
    from app.main import app
except ModuleNotFoundError as exc:
    missing = exc.name or "desconhecida"
    raise SystemExit(
        f"Dependência Python ausente: {missing}.\n"
        "Execute o servidor pelo ambiente virtual do projeto:\n"
        r"  .\venv\Scripts\python.exe main.py"
        "\nOu ative o ambiente antes de executar:\n"
        r"  .\venv\Scripts\Activate.ps1"
    ) from exc


def main() -> None:
    import uvicorn

    uvicorn.run(
        app,
        host=os.getenv("SERVER_HOST", "127.0.0.1"),
        port=int(os.getenv("SERVER_PORT", "8000")),
    )


if __name__ == "__main__":
    main()


__all__ = ["app", "main"]
