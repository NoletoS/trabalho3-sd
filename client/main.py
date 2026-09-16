from __future__ import annotations

import os
import sys

from PySide6.QtWidgets import QApplication

from app.api import MediaApi
from app.main_window import MainWindow


def main() -> int:
    application = QApplication(sys.argv)
    application.setApplicationName("Processador Distribuído de Mídia")
    api = MediaApi(os.getenv("MEDIA_SERVER_URL", "http://127.0.0.1:8000"))
    window = MainWindow(api)
    window.show()
    return application.exec()


if __name__ == "__main__":
    raise SystemExit(main())
