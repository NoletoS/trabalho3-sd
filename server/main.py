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


import socket


def get_local_ip() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"


def main() -> None:
    import uvicorn

    host = os.getenv("SERVER_HOST", "0.0.0.0")
    port = int(os.getenv("SERVER_PORT", "8000"))
    local_ip = get_local_ip()

    print("\n" + "=" * 62)
    print("🚀 Servidor Processador Distribuído de Áudio Iniciado!")
    print("=" * 62)
    print(f"📡 Acesso Local (neste PC):")
    print(f"   http://127.0.0.1:{port}")
    print(f"   http://localhost:{port}\n")
    print(f"🌐 Conexão de Outro PC (Use este IP no Cliente Desktop):")
    print(f"   http://{local_ip}:{port}\n")
    print(f"📖 Documentação Swagger da API:")
    print(f"   http://{local_ip}:{port}/docs")
    print("=" * 62 + "\n")

    uvicorn.run(
        app,
        host=host,
        port=port,
    )


if __name__ == "__main__":
    main()


__all__ = ["app", "main"]
