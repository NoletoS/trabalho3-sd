from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, QRunnable, Qt, QThreadPool, QTimer, Signal, Slot
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .api import MediaApi


OPERATIONS = {
    "Converter para MP4": "convert_mp4",
    "Extrair áudio (MP3)": "extract_mp3",
    "Compactar vídeo": "compress_video",
}
OPERATION_LABELS = {value: label for label, value in OPERATIONS.items()}
STATUS_LABELS = {
    "pending": "Aguardando",
    "processing": "Processando",
    "completed": "Concluído",
    "failed": "Falhou",
}
STATUS_STYLES = {
    "pending": ("#efd06f", "#332a12", "#6f5a21"),
    "processing": ("#f5d86f", "#302b16", "#8a742c"),
    "completed": ("#67e0a8", "#103a2b", "#247052"),
    "failed": ("#ff7a8a", "#431923", "#842f41"),
}


STYLESHEET = """
QMainWindow, QWidget#centralWidget {
    background-color: #07110d;
    color: #eeeade;
    font-family: "Segoe UI";
    font-size: 13px;
}
QLabel { color: #e9e7dc; background: transparent; }
QLabel#brandMark {
    color: #07110d;
    background-color: #d4af37;
    border-radius: 11px;
    font-size: 18px;
    font-weight: 800;
}
QLabel#titleLabel { color: #fff8dc; font-size: 26px; font-weight: 700; }
QLabel#subtitleLabel { color: #82988f; font-size: 13px; }
QLabel#sectionTitle { color: #f7f1d7; font-size: 16px; font-weight: 650; }
QLabel#mutedLabel, QLabel#fieldLabel { color: #82988f; }
QLabel#fieldLabel { font-size: 12px; font-weight: 600; }
QLabel#statValue { color: #ffffff; font-size: 25px; font-weight: 700; }
QLabel#statCaption { color: #87998f; font-size: 12px; font-weight: 600; }
QLabel#countBadge {
    color: #e0cc88;
    background-color: #19271f;
    border: 1px solid #3e513b;
    border-radius: 10px;
    padding: 3px 9px;
    font-size: 11px;
}
QFrame#card, QFrame#statCard, QFrame#connectionCard {
    background-color: #0e1c17;
    border: 1px solid #223b31;
    border-radius: 15px;
}
QFrame#statAccentPurple { background-color: #d4af37; border-radius: 2px; }
QFrame#statAccentBlue { background-color: #9fbd61; border-radius: 2px; }
QFrame#statAccentGreen { background-color: #36c783; border-radius: 2px; }
QFrame#statAccentRed { background-color: #f2667a; border-radius: 2px; }
QLineEdit, QComboBox {
    color: #f0ede2;
    background-color: #091510;
    border: 1px solid #29463a;
    border-radius: 9px;
    padding: 10px 12px;
    selection-background-color: #2b7a58;
}
QLineEdit:focus, QComboBox:focus { border: 1px solid #d4af37; }
QLineEdit:read-only { color: #adb9b1; background-color: #0a1712; }
QComboBox::drop-down { border: none; width: 30px; }
QComboBox QAbstractItemView {
    color: #f0ede2;
    background-color: #12231c;
    border: 1px solid #315044;
    selection-background-color: #2b7a58;
    padding: 5px;
}
QPushButton {
    color: #d8ded8;
    background-color: #172a22;
    border: 1px solid #315044;
    border-radius: 9px;
    padding: 9px 15px;
    font-weight: 600;
}
QPushButton:hover { background-color: #203a30; border-color: #4e6b5d; }
QPushButton:pressed { background-color: #102019; }
QPushButton:disabled { color: #52635c; background-color: #101b17; border-color: #20332b; }
QPushButton#primaryButton {
    color: #07110d;
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #e0b84b, stop:1 #42c98d);
    border: none;
    padding: 11px 20px;
}
QPushButton#primaryButton:hover { background-color: #ebcb6b; }
QPushButton#successButton {
    color: #71e5b3;
    background-color: #102c25;
    border-color: #245a49;
}
QPushButton#successButton:hover { background-color: #153a30; }
QPushButton#compactButton { padding: 8px 12px; }
QTableWidget {
    color: #e5e8df;
    background-color: #0e1c17;
    alternate-background-color: #0b1813;
    border: none;
    outline: none;
    gridline-color: transparent;
    selection-background-color: #203c31;
    selection-color: #ffffff;
}
QTableWidget::item { border-bottom: 1px solid #1c332a; padding: 8px; }
QTableWidget::item:selected { background-color: #203c31; }
QHeaderView::section {
    color: #a69867;
    background-color: #0b1712;
    border: none;
    border-bottom: 1px solid #2a463a;
    padding: 11px 9px;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
}
QProgressBar {
    color: #eee9d7;
    background-color: #091510;
    border: 1px solid #2b463b;
    border-radius: 6px;
    text-align: center;
    font-size: 11px;
    font-weight: 600;
}
QProgressBar::chunk { background-color: #d4af37; border-radius: 5px; }
QScrollBar:vertical { background: #0b1712; width: 9px; margin: 0; }
QScrollBar::handle:vertical { background: #385649; border-radius: 4px; min-height: 24px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QStatusBar { color: #788e84; background-color: #07110d; border-top: 1px solid #1d352b; }
QToolTip { color: #f4efd8; background-color: #172820; border: 1px solid #496554; padding: 6px; }
"""


class WorkerSignals(QObject):
    success = Signal(object)
    error = Signal(str)


class Worker(QRunnable):
    def __init__(self, function: Callable[[], Any]) -> None:
        super().__init__()
        self.function = function
        self.signals = WorkerSignals()

    @Slot()
    def run(self) -> None:
        try:
            self.signals.success.emit(self.function())
        except Exception as exc:
            self.signals.error.emit(str(exc))


class MainWindow(QMainWindow):
    def __init__(self, api: MediaApi) -> None:
        super().__init__()
        self.api = api
        self.jobs: list[dict[str, Any]] = []
        self.pool = QThreadPool.globalInstance()
        self.setWindowTitle("MediaFlow — Processador Distribuído")
        self.setMinimumSize(980, 680)
        self.resize(1180, 780)
        self.setStyleSheet(STYLESHEET)
        self._build_ui()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_jobs)
        self.timer.start(3000)
        self.check_health()
        self.refresh_jobs()

    @staticmethod
    def _button(text: str, object_name: str = "") -> QPushButton:
        button = QPushButton(text)
        if object_name:
            button.setObjectName(object_name)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        return button

    @staticmethod
    def _field_label(text: str) -> QLabel:
        label = QLabel(text.upper())
        label.setObjectName("fieldLabel")
        return label

    @staticmethod
    def _stat_card(caption: str, accent_name: str) -> tuple[QFrame, QLabel]:
        card = QFrame()
        card.setObjectName("statCard")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(13)
        accent = QFrame()
        accent.setObjectName(accent_name)
        accent.setFixedSize(4, 42)
        layout.addWidget(accent)
        text = QVBoxLayout()
        text.setSpacing(0)
        value = QLabel("0")
        value.setObjectName("statValue")
        label = QLabel(caption)
        label.setObjectName("statCaption")
        text.addWidget(value)
        text.addWidget(label)
        layout.addLayout(text)
        layout.addStretch()
        return card, value

    def _build_ui(self) -> None:
        central = QWidget()
        central.setObjectName("centralWidget")
        root = QVBoxLayout(central)
        root.setContentsMargins(28, 24, 28, 20)
        root.setSpacing(17)

        header = QHBoxLayout()
        header.setSpacing(14)
        brand = QLabel("MF")
        brand.setObjectName("brandMark")
        brand.setAlignment(Qt.AlignmentFlag.AlignCenter)
        brand.setFixedSize(46, 46)
        header.addWidget(brand)
        heading = QVBoxLayout()
        heading.setSpacing(1)
        title = QLabel("MediaFlow")
        title.setObjectName("titleLabel")
        subtitle = QLabel("Processamento distribuído de áudio e vídeo")
        subtitle.setObjectName("subtitleLabel")
        heading.addWidget(title)
        heading.addWidget(subtitle)
        header.addLayout(heading)
        header.addStretch()

        connection = QFrame()
        connection.setObjectName("connectionCard")
        connection_layout = QHBoxLayout(connection)
        connection_layout.setContentsMargins(12, 7, 12, 7)
        connection_layout.setSpacing(8)
        self.connection_dot = QLabel("●")
        self.connection_dot.setStyleSheet("color: #f6c76b; font-size: 14px;")
        self.connection_status = QLabel("Verificando servidor")
        connection_layout.addWidget(self.connection_dot)
        connection_layout.addWidget(self.connection_status)
        header.addWidget(connection)
        root.addLayout(header)

        stats = QGridLayout()
        stats.setHorizontalSpacing(12)
        stat_specs = [
            ("Total de tarefas", "statAccentPurple", "stat_total"),
            ("Em processamento", "statAccentBlue", "stat_processing"),
            ("Concluídos", "statAccentGreen", "stat_completed"),
            ("Com falha", "statAccentRed", "stat_failed"),
        ]
        for column, (caption, accent, attribute) in enumerate(stat_specs):
            card, value = self._stat_card(caption, accent)
            setattr(self, attribute, value)
            stats.addWidget(card, 0, column)
            stats.setColumnStretch(column, 1)
        root.addLayout(stats)

        upload_card = QFrame()
        upload_card.setObjectName("card")
        upload = QVBoxLayout(upload_card)
        upload.setContentsMargins(20, 17, 20, 19)
        upload.setSpacing(11)
        upload_header = QHBoxLayout()
        upload_title = QLabel("Novo processamento")
        upload_title.setObjectName("sectionTitle")
        upload_hint = QLabel("Selecione a mídia e o formato de saída")
        upload_hint.setObjectName("mutedLabel")
        upload_header.addWidget(upload_title)
        upload_header.addSpacing(8)
        upload_header.addWidget(upload_hint)
        upload_header.addStretch()
        upload.addLayout(upload_header)

        fields = QGridLayout()
        fields.setHorizontalSpacing(12)
        fields.setVerticalSpacing(7)
        fields.addWidget(self._field_label("Arquivo de mídia"), 0, 0)
        fields.addWidget(self._field_label("Operação"), 0, 2)
        self.file_path = QLineEdit()
        self.file_path.setReadOnly(True)
        self.file_path.setPlaceholderText("Nenhum arquivo selecionado")
        fields.addWidget(self.file_path, 1, 0)
        choose_button = self._button("Escolher arquivo", "compactButton")
        choose_button.clicked.connect(self.choose_file)
        fields.addWidget(choose_button, 1, 1)
        self.operation = QComboBox()
        self.operation.addItems(OPERATIONS.keys())
        fields.addWidget(self.operation, 1, 2)
        self.send_button = self._button("Iniciar processamento", "primaryButton")
        self.send_button.clicked.connect(self.submit_job)
        fields.addWidget(self.send_button, 1, 3)
        fields.setColumnStretch(0, 4)
        fields.setColumnStretch(2, 2)
        upload.addLayout(fields)
        root.addWidget(upload_card)

        server_card = QFrame()
        server_card.setObjectName("card")
        server_layout = QHBoxLayout(server_card)
        server_layout.setContentsMargins(16, 11, 16, 11)
        server_layout.setSpacing(10)
        server_label = QLabel("API")
        server_label.setObjectName("fieldLabel")
        self.server_url = QLineEdit(self.api.base_url)
        self.server_url.editingFinished.connect(self._update_server_url)
        local_button = self._button("Usar servidor local", "compactButton")
        local_button.clicked.connect(self._use_local_server)
        server_layout.addWidget(server_label)
        server_layout.addWidget(self.server_url, 1)
        server_layout.addWidget(local_button)
        root.addWidget(server_card)

        jobs_card = QFrame()
        jobs_card.setObjectName("card")
        jobs_layout = QVBoxLayout(jobs_card)
        jobs_layout.setContentsMargins(1, 15, 1, 1)
        jobs_layout.setSpacing(10)
        table_header = QHBoxLayout()
        table_header.setContentsMargins(18, 0, 18, 0)
        table_title = QLabel("Processamentos recentes")
        table_title.setObjectName("sectionTitle")
        self.count_badge = QLabel("0 itens")
        self.count_badge.setObjectName("countBadge")
        refresh_button = self._button("Atualizar", "compactButton")
        refresh_button.clicked.connect(self.refresh_jobs)
        self.download_button = self._button("Baixar resultado", "successButton")
        self.download_button.clicked.connect(self.download_selected)
        table_header.addWidget(table_title)
        table_header.addWidget(self.count_badge)
        table_header.addStretch()
        table_header.addWidget(refresh_button)
        table_header.addWidget(self.download_button)
        jobs_layout.addLayout(table_header)

        self.empty_state = QLabel("Nenhum processamento ainda. Envie sua primeira mídia acima.")
        self.empty_state.setObjectName("mutedLabel")
        self.empty_state.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_state.setMinimumHeight(52)
        jobs_layout.addWidget(self.empty_state)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["Arquivo", "Operação", "Estado", "Progresso", "Tamanho", "Detalhe"]
        )
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(56)
        header_view = self.table.horizontalHeader()
        header_view.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header_view.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header_view.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header_view.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(2, 126)
        self.table.setColumnWidth(3, 145)
        jobs_layout.addWidget(self.table, 1)
        root.addWidget(jobs_card, 1)

        self.setCentralWidget(central)
        self.statusBar().showMessage("Pronto para processar")

    def _run(
        self,
        function: Callable[[], Any],
        success: Callable[[Any], None],
        error: Callable[[str], None] | None = None,
    ) -> None:
        worker = Worker(function)
        worker.signals.success.connect(success)
        worker.signals.error.connect(error or self._show_error)
        self.pool.start(worker)

    def _update_server_url(self) -> None:
        self.api.base_url = self.server_url.text().strip().rstrip("/")
        self.check_health()
        self.refresh_jobs()

    def _use_local_server(self) -> None:
        self.server_url.setText("http://127.0.0.1:8000")
        self._update_server_url()

    def choose_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar mídia",
            "",
            "Mídia (*.mp4 *.mkv *.avi *.mov *.webm *.mpeg *.mpg *.mp3 *.wav *.flac *.m4a *.ogg)",
        )
        if path:
            self.file_path.setText(path)
            self.statusBar().showMessage(f"Arquivo selecionado: {Path(path).name}", 4000)

    def check_health(self) -> None:
        self._run(self.api.health, self._health_ok, self._health_error)

    def _health_ok(self, health: dict[str, Any]) -> None:
        healthy = health["status"] == "ok"
        self.connection_status.setText("Servidor online" if healthy else "Servidor degradado")
        self.connection_dot.setStyleSheet(
            f"color: {'#55d99f' if healthy else '#f6c76b'}; font-size: 14px;"
        )
        self.connection_status.setStyleSheet(
            f"color: {'#9ce8c7' if healthy else '#f6c76b'}; font-weight: 600;"
        )
        self.connection_status.setToolTip(
            f"Banco: {health['database']} | FFmpeg: {health['ffmpeg']}"
        )

    def _health_error(self, message: str) -> None:
        self.connection_status.setText("Servidor desconectado")
        self.connection_dot.setStyleSheet("color: #ff6f82; font-size: 14px;")
        self.connection_status.setStyleSheet("color: #ff8d9d; font-weight: 600;")
        self.connection_status.setToolTip(message)
        self.statusBar().showMessage(
            "Servidor indisponível. Use http://127.0.0.1:8000 neste computador.",
            7000,
        )

    def submit_job(self) -> None:
        path = self.file_path.text()
        if not path:
            QMessageBox.information(self, "Arquivo", "Escolha um arquivo de mídia.")
            return
        operation = OPERATIONS[self.operation.currentText()]
        self.send_button.setEnabled(False)
        self.send_button.setText("Enviando…")
        self.statusBar().showMessage("Enviando arquivo para o servidor…")
        self._run(
            lambda: self.api.create_job(path, operation),
            self._job_submitted,
            self._submit_error,
        )

    def _job_submitted(self, _job: dict[str, Any]) -> None:
        self.send_button.setEnabled(True)
        self.send_button.setText("Iniciar processamento")
        self.file_path.clear()
        self.statusBar().showMessage("Arquivo recebido. Processamento iniciado.", 5000)
        self.refresh_jobs()

    def _submit_error(self, message: str) -> None:
        self.send_button.setEnabled(True)
        self.send_button.setText("Iniciar processamento")
        self._show_error(message)

    def refresh_jobs(self) -> None:
        self._run(self.api.list_jobs, self._render_jobs, self._health_error)

    def _render_jobs(self, jobs: list[dict[str, Any]]) -> None:
        self.jobs = jobs
        total = len(jobs)
        self.stat_total.setText(str(total))
        self.stat_processing.setText(
            str(sum(job["status"] in {"pending", "processing"} for job in jobs))
        )
        self.stat_completed.setText(str(sum(job["status"] == "completed" for job in jobs)))
        self.stat_failed.setText(str(sum(job["status"] == "failed" for job in jobs)))
        self.count_badge.setText(f"{total} {'item' if total == 1 else 'itens'}")
        self.empty_state.setVisible(total == 0)
        self.table.setVisible(total > 0)
        self.table.setRowCount(total)

        for row, job in enumerate(jobs):
            file_item = QTableWidgetItem(job["original_name"])
            file_item.setData(Qt.ItemDataRole.UserRole, job["id"])
            file_item.setToolTip(job["original_name"])
            operation_item = QTableWidgetItem(
                OPERATION_LABELS.get(job["operation"], job["operation"])
            )
            size_item = QTableWidgetItem(self._format_size(job["file_size"]))
            size_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            detail_text = job.get("error_message") or {
                "pending": "Na fila do servidor",
                "processing": "Processando com FFmpeg",
                "completed": "Disponível para download",
                "failed": "Falha no processamento",
            }.get(job["status"], "")
            detail_item = QTableWidgetItem(detail_text)
            detail_item.setToolTip(detail_text)
            if job["status"] == "failed":
                detail_item.setForeground(QColor("#ff8d9d"))
            elif job["status"] == "completed":
                detail_item.setForeground(QColor("#74d9ae"))

            for column, item in (
                (0, file_item),
                (1, operation_item),
                (4, size_item),
                (5, detail_item),
            ):
                item.setTextAlignment(
                    (Qt.AlignmentFlag.AlignLeft if column in {0, 5} else Qt.AlignmentFlag.AlignCenter)
                    | Qt.AlignmentFlag.AlignVCenter
                )
                self.table.setItem(row, column, item)

            foreground, background, border = STATUS_STYLES.get(
                job["status"], ("#cbd5e6", "#1b2539", "#34435d")
            )
            status_label = QLabel(STATUS_LABELS.get(job["status"], job["status"]))
            status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            status_label.setStyleSheet(
                f"color:{foreground}; background-color:{background}; border:1px solid {border};"
                "border-radius:9px; padding:5px 8px; font-size:11px; font-weight:700;"
            )
            status_container = QWidget()
            status_layout = QHBoxLayout(status_container)
            status_layout.setContentsMargins(9, 10, 9, 10)
            status_layout.addWidget(status_label)
            self.table.setCellWidget(row, 2, status_container)

            progress = QProgressBar()
            progress.setRange(0, 100)
            progress.setValue(int(job["progress"]))
            progress.setFixedHeight(20)
            if job["status"] == "failed":
                progress.setStyleSheet("QProgressBar::chunk { background-color: #e35970; }")
            elif job["status"] == "completed":
                progress.setStyleSheet("QProgressBar::chunk { background-color: #45c990; }")
            progress_container = QWidget()
            progress_layout = QHBoxLayout(progress_container)
            progress_layout.setContentsMargins(9, 16, 9, 16)
            progress_layout.addWidget(progress)
            self.table.setCellWidget(row, 3, progress_container)

    def download_selected(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Resultado", "Selecione um processamento.")
            return
        job = self.jobs[row]
        if job["status"] != "completed":
            QMessageBox.information(self, "Resultado", "O processamento ainda não foi concluído.")
            return
        extension = ".mp3" if job["operation"] == "extract_mp3" else ".mp4"
        suggested = f"{Path(job['original_name']).stem}_processado{extension}"
        destination, _ = QFileDialog.getSaveFileName(self, "Salvar resultado", suggested)
        if not destination:
            return
        self.statusBar().showMessage("Baixando resultado…")
        self._run(
            lambda: self.api.download(job["id"], destination),
            lambda path: self.statusBar().showMessage(f"Resultado salvo em {path}", 8000),
        )

    def _show_error(self, message: str) -> None:
        self.statusBar().showMessage(message, 7000)
        QMessageBox.critical(self, "Erro", message)

    @staticmethod
    def _format_size(size: int) -> str:
        value = float(size)
        for unit in ("B", "KB", "MB", "GB"):
            if value < 1024 or unit == "GB":
                return f"{value:.1f} {unit}"
            value /= 1024
        return f"{value:.1f} GB"
