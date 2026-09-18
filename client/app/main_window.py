from __future__ import annotations

import json
import os
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

client_dir = str(Path(__file__).resolve().parent.parent)
if client_dir not in sys.path:
    sys.path.insert(0, client_dir)

from PySide6.QtCore import QObject, QRunnable, Qt, QThreadPool, QTimer, QUrl, Signal, Slot
from PySide6.QtGui import QColor, QIcon, QImage, QPixmap
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
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
    QSlider,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.api import MediaApi


OPERATIONS = {
    "🔊 Normalização de Volume (EBU R128 loudnorm)": "normalize_volume",
    "🎧 Converter para MP3 (190 kbps)": "convert_mp3",
    "🎼 Converter para WAV (PCM 16-bit)": "convert_wav",
    "🎙️ Extrair áudio (MP3)": "extract_mp3",
    "🎸 Realce de Graves (Bass Boost)": "bass_boost",
    "⚡ Acelerar Áudio (1.25x)": "speed_up",
    "🐢 Desacelerar Áudio (0.85x)": "slow_down",
    "🎬 Converter Vídeo para MP4": "convert_mp4",
    "📦 Compactar vídeo": "compress_video",
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
    font-family: "Segoe UI", "Inter", sans-serif;
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
QLabel#titleLabel { color: #fff8dc; font-size: 24px; font-weight: 700; }
QLabel#subtitleLabel { color: #82988f; font-size: 13px; }
QLabel#sectionTitle { color: #f7f1d7; font-size: 15px; font-weight: 650; }
QLabel#mutedLabel, QLabel#fieldLabel { color: #82988f; }
QLabel#fieldLabel { font-size: 12px; font-weight: 600; }
QLabel#statValue { color: #ffffff; font-size: 24px; font-weight: 700; }
QLabel#statCaption { color: #87998f; font-size: 12px; font-weight: 600; }
QLabel#countBadge {
    color: #e0cc88;
    background-color: #19271f;
    border: 1px solid #3e513b;
    border-radius: 10px;
    padding: 3px 9px;
    font-size: 11px;
}
QFrame#card, QFrame#statCard, QFrame#playerCard {
    background-color: #0e1c17;
    border: 1px solid #223b31;
    border-radius: 14px;
}
QFrame#statAccentGreen { background-color: #36c783; border-radius: 2px; }
QFrame#statAccentGold { background-color: #d4af37; border-radius: 2px; }
QFrame#statAccentBlue { background-color: #38bdf8; border-radius: 2px; }
QFrame#statAccentRed { background-color: #f2667a; border-radius: 2px; }
QLineEdit, QComboBox {
    color: #f0ede2;
    background-color: #091510;
    border: 1px solid #29463a;
    border-radius: 8px;
    padding: 9px 12px;
    selection-background-color: #2b7a58;
}
QLineEdit:focus, QComboBox:focus { border: 1px solid #d4af37; }
QLineEdit:read-only { color: #adb9b1; background-color: #0a1712; }
QPushButton {
    color: #d8ded8;
    background-color: #172a22;
    border: 1px solid #315044;
    border-radius: 8px;
    padding: 9px 14px;
    font-weight: 600;
}
QPushButton:hover { background-color: #203a30; border-color: #4e6b5d; }
QPushButton:pressed { background-color: #102019; }
QPushButton:disabled { color: #52635c; background-color: #101b17; border-color: #20332b; }
QPushButton#primaryButton {
    color: #07110d;
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #e0b84b, stop:1 #42c98d);
    border: none;
    padding: 10px 18px;
    font-weight: 700;
}
QPushButton#primaryButton:hover { background-color: #ebcb6b; }
QPushButton#playButton {
    color: #05100c;
    background-color: #36c783;
    border: none;
    padding: 8px 14px;
    font-weight: 700;
}
QPushButton#playButton:hover { background-color: #4ade80; }
QPushButton#dangerButton {
    color: #fca5a5;
    background-color: #2a1518;
    border: 1px solid #5c272e;
}
QPushButton#dangerButton:hover { background-color: #3a1a1f; }
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
    padding: 10px 8px;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
}
QSlider::groove:horizontal {
    border: none;
    height: 6px;
    background: #15261f;
    border-radius: 3px;
}
QSlider::sub-page:horizontal {
    background: #36c783;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #f0ede2;
    border: 1px solid #245a49;
    width: 14px;
    margin-top: -4px;
    margin-bottom: -4px;
    border-radius: 7px;
}
"""


class WorkerSignals(QObject):
    finished = Signal(object)
    error = Signal(str)


class Worker(QRunnable):
    def __init__(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @Slot()
    def run(self) -> None:
        try:
            result = self.fn(*self.args, **self.kwargs)
            self.signals.finished.emit(result)
        except Exception as exc:
            self.signals.error.emit(str(exc))


class MetaDialog(QDialog):
    def __init__(self, meta_data: dict[str, Any], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Metadados: meta.json ({meta_data.get('id', '')})")
        self.resize(650, 480)
        self.setStyleSheet(STYLESHEET)

        layout = QVBoxLayout(self)
        title = QLabel(f"📄 Arquivo meta.json — Job {meta_data.get('id', '')}")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setStyleSheet(
            "background-color: #08120d; color: #a7f3d0; font-family: 'JetBrains Mono', 'Courier New'; font-size: 12px; border: 1px solid #203c31; border-radius: 8px; padding: 12px;"
        )
        text_edit.setPlainText(json.dumps(meta_data, indent=2, ensure_ascii=False))
        layout.addWidget(text_edit)

        btn_close = QPushButton("Fechar")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignmentFlag.AlignRight)


class MainWindow(QMainWindow):
    def __init__(self, api: MediaApi) -> None:
        super().__init__()
        self.api = api
        self.thread_pool = QThreadPool()
        self.selected_job: dict[str, Any] | None = None
        self.showing_trash = False
        self.cached_jobs: list[dict[str, Any]] = []

        # Configurar Player de Áudio
        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(0.8)

        self.player.positionChanged.connect(self.on_player_position_changed)
        self.player.durationChanged.connect(self.on_player_duration_changed)
        self.player.playbackStateChanged.connect(self.on_playback_state_changed)
        self.player.errorOccurred.connect(self.on_player_error)

        self.setup_ui()
        self.setStyleSheet(STYLESHEET)

        # Polling periódico de status
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_data)
        self.timer.start(3000)

        self.refresh_data()

    def setup_ui(self) -> None:
        self.setWindowTitle("Processador Distribuído de Áudio e Mídia (PySide6)")
        self.resize(1180, 840)

        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()
        brand_icon = QLabel(" ♬ ")
        brand_icon.setObjectName("brandMark")
        brand_icon.setFixedSize(38, 38)
        brand_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(brand_icon)

        title_col = QVBoxLayout()
        title = QLabel("Processador Distribuído de Áudio")
        title.setObjectName("titleLabel")
        subtitle = QLabel("Cliente Desktop PySide6 • HTTP + FFmpeg + PostgreSQL • Subpastas UUID")
        subtitle.setObjectName("subtitleLabel")
        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        header_layout.addLayout(title_col)

        header_layout.addStretch()

        # Configuração de Conexão com a API (Permite alterar IP para outro PC)
        conn_frame = QFrame()
        conn_frame.setObjectName("card")
        conn_layout = QHBoxLayout(conn_frame)
        conn_layout.setContentsMargins(10, 6, 10, 6)
        conn_layout.setSpacing(8)

        lbl_api = QLabel("API:")
        lbl_api.setObjectName("fieldLabel")
        conn_layout.addWidget(lbl_api)

        self.api_url_input = QLineEdit(self.api.base_url)
        self.api_url_input.setPlaceholderText("http://IP:8000")
        self.api_url_input.setFixedWidth(230)
        self.api_url_input.returnPressed.connect(self.change_api_url)
        conn_layout.addWidget(self.api_url_input)

        btn_connect = QPushButton("Conectar")
        btn_connect.clicked.connect(self.change_api_url)
        conn_layout.addWidget(btn_connect)

        self.health_badge = QLabel("●")
        self.health_badge.setStyleSheet("color: #36c783; font-size: 18px; padding: 0 4px;")
        self.health_badge.setToolTip("Conectando...")
        conn_layout.addWidget(self.health_badge)

        header_layout.addWidget(conn_frame)

        main_layout.addLayout(header_layout)

        # Splitter com Envio (esquerda) e Lista + Player (direita)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # --- PAINEL ESQUERDO: ENVIO ---
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 10, 0)
        left_layout.setSpacing(14)

        # Card de Upload
        upload_card = QFrame()
        upload_card.setObjectName("card")
        up_layout = QVBoxLayout(upload_card)
        up_layout.setContentsMargins(16, 16, 16, 16)
        up_layout.setSpacing(12)

        up_title = QLabel("Novo Processamento de Áudio")
        up_title.setObjectName("sectionTitle")
        up_layout.addWidget(up_title)

        up_layout.addWidget(QLabel("ARQUIVO DE ÁUDIO / MÍDIA:"))
        file_row = QHBoxLayout()
        self.file_input = QLineEdit()
        self.file_input.setPlaceholderText("Selecione um arquivo...")
        self.file_input.setReadOnly(True)
        btn_browse = QPushButton("Procurar...")
        btn_browse.clicked.connect(self.browse_file)
        file_row.addWidget(self.file_input)
        file_row.addWidget(btn_browse)
        up_layout.addLayout(file_row)

        up_layout.addWidget(QLabel("OPERAÇÃO FFmpeg:"))
        self.op_combo = QComboBox()
        for label, val in OPERATIONS.items():
            self.op_combo.addItem(label, val)
        up_layout.addWidget(self.op_combo)

        self.btn_send = QPushButton("⚡ Enviar para o Servidor")
        self.btn_send.setObjectName("primaryButton")
        self.btn_send.clicked.connect(self.submit_job)
        up_layout.addWidget(self.btn_send)

        left_layout.addWidget(upload_card)

        # Card de Especificação de Armazenamento
        spec_card = QFrame()
        spec_card.setObjectName("card")
        spec_layout = QVBoxLayout(spec_card)
        spec_layout.setContentsMargins(14, 14, 14, 14)
        spec_layout.setSpacing(8)

        spec_title = QLabel("Regras de Armazenamento")
        spec_title.setObjectName("sectionTitle")
        spec_layout.addWidget(spec_title)

        spec_desc = QLabel(
            "• <b>UUID Único:</b> Subpasta <code>storage/&lt;uuid&gt;/</code><br>"
            "• <b>Áudio Original:</b> <code>original/audio.&lt;ext&gt;</code><br>"
            "• <b>Áudio Processado:</b> <code>processed/audio.&lt;ext&gt;</code><br>"
            "• <b>Waveform:</b> <code>waveform.png</code> gerada auto.<br>"
            "• <b>Metadados:</b> <code>meta.json</code> com SHA-256.<br>"
            "• <b>Lixeira:</b> <code>storage/trash/&lt;uuid&gt;/</code>"
        )
        spec_desc.setTextFormat(Qt.TextFormat.RichText)
        spec_desc.setStyleSheet("font-size: 11px; color: #82988f; line-height: 1.5;")
        spec_layout.addWidget(spec_desc)

        left_layout.addWidget(spec_card)
        left_layout.addStretch()

        splitter.addWidget(left_widget)

        # --- PAINEL DIREITO: TABELA, PLAYER E WAVEFORM ---
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(10, 0, 0, 0)
        right_layout.setSpacing(14)

        # Barra superior da lista (Abas Ativos / Lixeira)
        top_list_bar = QHBoxLayout()
        self.lbl_list_title = QLabel("Processamentos Ativos")
        self.lbl_list_title.setObjectName("sectionTitle")
        top_list_bar.addWidget(self.lbl_list_title)
        top_list_bar.addStretch()

        self.btn_toggle_trash = QPushButton("🗑️ Ver Lixeira")
        self.btn_toggle_trash.clicked.connect(self.toggle_trash_view)
        top_list_bar.addWidget(self.btn_toggle_trash)

        btn_refresh = QPushButton("🔄 Atualizar")
        btn_refresh.clicked.connect(self.refresh_data)
        top_list_bar.addWidget(btn_refresh)

        right_layout.addLayout(top_list_bar)

        # Tabela de Jobs
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Arquivo Original", "Operação", "Status", "Tamanho", "UUID"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.itemSelectionChanged.connect(self.on_table_selection_changed)
        right_layout.addWidget(self.table)

        # --- PLAYER E WAVEFORM CARD ---
        self.player_card = QFrame()
        self.player_card.setObjectName("playerCard")
        p_layout = QVBoxLayout(self.player_card)
        p_layout.setContentsMargins(16, 16, 16, 16)
        p_layout.setSpacing(10)

        p_title_row = QHBoxLayout()
        self.lbl_player_track = QLabel("Nenhum áudio selecionado")
        self.lbl_player_track.setObjectName("sectionTitle")
        p_title_row.addWidget(self.lbl_player_track)
        p_title_row.addStretch()

        self.btn_view_meta = QPushButton("📄 Ver meta.json")
        self.btn_view_meta.setEnabled(False)
        self.btn_view_meta.clicked.connect(self.open_meta_dialog)
        p_title_row.addWidget(self.btn_view_meta)

        self.btn_action_trash = QPushButton("🗑️ Mover p/ Lixeira")
        self.btn_action_trash.setObjectName("dangerButton")
        self.btn_action_trash.setEnabled(False)
        self.btn_action_trash.clicked.connect(self.action_trash_or_restore)
        p_title_row.addWidget(self.btn_action_trash)

        self.btn_download = QPushButton("⬇️ Baixar Resultado")
        self.btn_download.setEnabled(False)
        self.btn_download.clicked.connect(self.download_selected)
        p_title_row.addWidget(self.btn_download)

        p_layout.addLayout(p_title_row)

        # Waveform Display
        self.lbl_waveform = QLabel("A forma de onda (waveform.png) aparecerá aqui")
        self.lbl_waveform.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_waveform.setStyleSheet(
            "background-color: #08120d; border: 1px solid #1c332a; border-radius: 8px; min-height: 80px; max-height: 120px; color: #52635c;"
        )
        p_layout.addWidget(self.lbl_waveform)

        # Controles de Reprodução
        controls_row = QHBoxLayout()

        self.btn_play_original = QPushButton("▶ Tocar Original")
        self.btn_play_original.setEnabled(False)
        self.btn_play_original.clicked.connect(lambda: self.play_current(is_original=True))
        controls_row.addWidget(self.btn_play_original)

        self.btn_play_processed = QPushButton("▶ Tocar Processado")
        self.btn_play_processed.setObjectName("playButton")
        self.btn_play_processed.setEnabled(False)
        self.btn_play_processed.clicked.connect(lambda: self.play_current(is_original=False))
        controls_row.addWidget(self.btn_play_processed)

        self.btn_pause = QPushButton("⏸ Pausar")
        self.btn_pause.setEnabled(False)
        self.btn_pause.clicked.connect(self.player.pause)
        controls_row.addWidget(self.btn_pause)

        self.btn_stop = QPushButton("⏹ Parar")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.player.stop)
        controls_row.addWidget(self.btn_stop)

        controls_row.addSpacing(14)
        controls_row.addWidget(QLabel("Vol:"))
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(80)
        self.volume_slider.setFixedWidth(80)
        self.volume_slider.valueChanged.connect(lambda v: self.audio_output.setVolume(v / 100.0))
        controls_row.addWidget(self.volume_slider)

        p_layout.addLayout(controls_row)

        # Barra de Progresso do Áudio
        time_row = QHBoxLayout()
        self.audio_time_lbl = QLabel("00:00 / 00:00")
        self.audio_time_lbl.setStyleSheet("font-family: 'JetBrains Mono'; font-size: 11px; color: #82988f;")
        self.audio_slider = QSlider(Qt.Orientation.Horizontal)
        self.audio_slider.setRange(0, 1000)
        self.audio_slider.sliderMoved.connect(self.set_player_position)

        time_row.addWidget(self.audio_slider)
        time_row.addWidget(self.audio_time_lbl)
        p_layout.addLayout(time_row)

        right_layout.addWidget(self.player_card)

        splitter.addWidget(right_widget)
        splitter.setSizes([380, 800])
        main_layout.addWidget(splitter)

    # --- LÓGICA E EVENTOS ---

    def browse_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar Arquivo de Áudio / Mídia",
            "",
            "Áudio e Vídeo (*.mp3 *.wav *.ogg *.flac *.m4a *.mp4 *.mkv *.avi *.mov *.webm);;Todos (*.*)",
        )
        if path:
            self.file_input.setText(path)

    def submit_job(self) -> None:
        file_path = self.file_input.text().strip()
        if not file_path:
            QMessageBox.warning(self, "Aviso", "Selecione um arquivo primeiro.")
            return

        operation = self.op_combo.currentData()
        self.btn_send.setEnabled(False)
        self.btn_send.setText("Enviando...")

        def _task():
            return self.api.create_job(file_path, operation)

        worker = Worker(_task)
        worker.signals.finished.connect(self.on_job_created)
        worker.signals.error.connect(self.on_job_error)
        self.thread_pool.start(worker)

    def on_job_created(self, job: dict[str, Any]) -> None:
        self.btn_send.setEnabled(True)
        self.btn_send.setText("⚡ Enviar para o Servidor")
        self.file_input.clear()
        if self.showing_trash:
            self.toggle_trash_view()
        else:
            self.refresh_data()

    def on_job_error(self, err: str) -> None:
        self.btn_send.setEnabled(True)
        self.btn_send.setText("⚡ Enviar para o Servidor")
        QMessageBox.critical(self, "Erro", f"Falha ao enviar arquivo:\n{err}")

    def toggle_trash_view(self) -> None:
        self.showing_trash = not self.showing_trash
        if self.showing_trash:
            self.lbl_list_title.setText("Lixeira (trash/)")
            self.btn_toggle_trash.setText("📂 Ver Ativos")
        else:
            self.lbl_list_title.setText("Processamentos Ativos")
            self.btn_toggle_trash.setText("🗑️ Ver Lixeira")
        self.refresh_data()

    def refresh_data(self) -> None:
        # Atualizar Health
        def _health_task():
            return self.api.health()

        h_worker = Worker(_health_task)
        h_worker.signals.finished.connect(self.on_health_ok)
        h_worker.signals.error.connect(self.on_health_fail)
        self.thread_pool.start(h_worker)

        # Atualizar Lista de Jobs
        def _jobs_task():
            return self.api.list_trash() if self.showing_trash else self.api.list_jobs()

        j_worker = Worker(_jobs_task)
        j_worker.signals.finished.connect(self.on_jobs_loaded)
        self.thread_pool.start(j_worker)

    def change_api_url(self) -> None:
        new_url = self.api_url_input.text().strip()
        if not new_url:
            new_url = "http://127.0.0.1:8000"
            self.api_url_input.setText(new_url)
        if not (new_url.startswith("http://") or new_url.startswith("https://")):
            new_url = f"http://{new_url}"
            self.api_url_input.setText(new_url)

        self.api.set_base_url(new_url)
        self.health_badge.setText("●")
        self.health_badge.setStyleSheet("color: #f59e0b; font-size: 18px; padding: 0 4px;")
        self.health_badge.setToolTip("Conectando...")
        self.refresh_data()

    def on_health_ok(self, data: dict[str, Any]) -> None:
        status = data.get("status", "ok")
        if status == "ok":
            self.health_badge.setText("●")
            self.health_badge.setStyleSheet("color: #36c783; font-size: 18px; padding: 0 4px;")
            self.health_badge.setToolTip("Conectado à API")
        else:
            self.health_badge.setText("●")
            self.health_badge.setStyleSheet("color: #f59e0b; font-size: 18px; padding: 0 4px;")
            self.health_badge.setToolTip(f"Online (status: {status})")

    def on_health_fail(self, _err: str) -> None:
        self.health_badge.setText("●")
        self.health_badge.setStyleSheet("color: #ef4444; font-size: 18px; padding: 0 4px;")
        self.health_badge.setToolTip("Desconectado do Servidor")

    def on_jobs_loaded(self, jobs: list[dict[str, Any]]) -> None:
        self.cached_jobs = jobs
        selected_uuid = self.selected_job.get("id") if self.selected_job else None

        self.table.setRowCount(len(jobs))
        selected_row = -1

        for row, job in enumerate(jobs):
            if job.get("id") == selected_uuid:
                selected_row = row

            name_item = QTableWidgetItem(job.get("original_name", ""))
            op_label = OPERATION_LABELS.get(job.get("operation"), job.get("operation", ""))
            op_item = QTableWidgetItem(op_label)

            st_val = job.get("status", "")
            st_text = STATUS_LABELS.get(st_val, st_val)
            st_item = QTableWidgetItem(st_text)
            colors = STATUS_STYLES.get(st_val, ("#eee", "#222", "#444"))
            st_item.setForeground(QColor(colors[0]))

            size_kb = (job.get("file_size", 0) or 0) / 1024
            size_item = QTableWidgetItem(f"{size_kb:.1f} KB")

            uuid_item = QTableWidgetItem(job.get("id", ""))

            self.table.setItem(row, 0, name_item)
            self.table.setItem(row, 1, op_item)
            self.table.setItem(row, 2, st_item)
            self.table.setItem(row, 3, size_item)
            self.table.setItem(row, 4, uuid_item)

        if selected_row >= 0:
            self.selected_job = jobs[selected_row]
            self.table.selectRow(selected_row)
            self.update_player_controls()
        elif self.table.rowCount() > 0 and not self.selected_job:
            self.selected_job = jobs[0]
            self.table.selectRow(0)
            self.update_player_controls()
            self.load_waveform_preview()

    def on_table_selection_changed(self) -> None:
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            self.selected_job = None
            self.update_player_controls()
            return

        row = selected_rows[0].row()
        if row < len(self.cached_jobs):
            self.selected_job = self.cached_jobs[row]
            self.update_player_controls()
            self.load_waveform_preview()

    def update_player_controls(self) -> None:
        if not self.selected_job:
            self.lbl_player_track.setText("Nenhum áudio selecionado")
            self.btn_play_original.setEnabled(False)
            self.btn_play_processed.setEnabled(False)
            self.btn_view_meta.setEnabled(False)
            self.btn_action_trash.setEnabled(False)
            self.btn_download.setEnabled(False)
            self.lbl_waveform.setText("A forma de onda (waveform.png) aparecerá aqui")
            self.lbl_waveform.setPixmap(QPixmap())
            return

        job = self.selected_job
        self.lbl_player_track.setText(f"♬ {job.get('original_name')} (UUID: {job.get('id')[:8]}...)")
        self.btn_view_meta.setEnabled(True)

        if self.showing_trash:
            self.btn_action_trash.setText("♻️ Restaurar da Lixeira")
            self.btn_action_trash.setObjectName("successButton")
            self.btn_action_trash.setStyleSheet("color: #67e0a8; background-color: #103a2b;")
        else:
            self.btn_action_trash.setText("🗑️ Mover p/ Lixeira")
            self.btn_action_trash.setObjectName("dangerButton")
            self.btn_action_trash.setStyleSheet("color: #fca5a5; background-color: #2a1518;")
        self.btn_action_trash.setEnabled(True)

        has_orig = bool(job.get("original_audio_url"))
        has_proc = bool(job.get("processed_audio_url")) and job.get("status") == "completed"

        self.btn_play_original.setEnabled(has_orig)
        self.btn_play_processed.setEnabled(has_proc)
        self.btn_download.setEnabled(has_proc)

    def load_waveform_preview(self) -> None:
        if not self.selected_job:
            return
        job = self.selected_job
        wave_url = job.get("processed_waveform_url") or job.get("original_waveform_url")
        if not wave_url:
            self.lbl_waveform.setText("Forma de onda ainda não disponível.")
            self.lbl_waveform.setPixmap(QPixmap())
            return

        full_url = f"{self.api.base_url}{wave_url}"

        def _fetch_img():
            import requests
            resp = requests.get(full_url, timeout=5)
            if resp.ok:
                return resp.content
            return None

        def _on_img_loaded(img_bytes: bytes | None):
            if img_bytes:
                img = QImage.fromData(img_bytes)
                pixmap = QPixmap.fromImage(img)
                scaled = pixmap.scaledToWidth(self.lbl_waveform.width() - 20, Qt.TransformationMode.SmoothTransformation)
                self.lbl_waveform.setPixmap(scaled)
            else:
                self.lbl_waveform.setText("Forma de onda não carregada.")

        worker = Worker(_fetch_img)
        worker.signals.finished.connect(_on_img_loaded)
        self.thread_pool.start(worker)

    def play_current(self, is_original: bool) -> None:
        if not self.selected_job:
            return
        job = self.selected_job
        path_url = job.get("original_audio_url") if is_original else job.get("processed_audio_url")
        if not path_url:
            return

        full_url = f"{self.api.base_url}{path_url}"
        tag = "Original" if is_original else f"Processado ({job.get('operation')})"
        self.lbl_player_track.setText(f"▶ Carregando [{tag}]: {job.get('original_name')}...")

        self.player.stop()
        self.player.setSource(QUrl(full_url))
        self.player.play()
        self.btn_pause.setEnabled(True)
        self.btn_stop.setEnabled(True)

    def on_playback_state_changed(self, state: QMediaPlayer.PlaybackState) -> None:
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.btn_pause.setEnabled(True)
            self.btn_stop.setEnabled(True)
            self.btn_pause.setText("⏸ Pausar")
            current_text = self.lbl_player_track.text()
            if "Carregando" in current_text:
                self.lbl_player_track.setText(current_text.replace("Carregando", "Tocando"))
        elif state == QMediaPlayer.PlaybackState.PausedState:
            self.btn_pause.setText("▶ Continuar")
        elif state == QMediaPlayer.PlaybackState.StoppedState:
            self.btn_pause.setEnabled(False)
            self.btn_stop.setEnabled(False)
            self.btn_pause.setText("⏸ Pausar")
            self.audio_slider.setValue(0)

    def on_player_error(self, error: QMediaPlayer.Error, error_string: str) -> None:
        self.lbl_player_track.setText(f"⚠️ Erro ao reproduzir áudio: {error_string}")
        self.btn_pause.setEnabled(False)
        self.btn_stop.setEnabled(False)

    def on_player_position_changed(self, position: int) -> None:
        duration = self.player.duration()
        if duration > 0:
            self.audio_slider.setValue(int(position * 1000 / duration))
            pos_str = f"{position // 60000:02d}:{(position % 60000) // 1000:02d}"
            dur_str = f"{duration // 60000:02d}:{(duration % 60000) // 1000:02d}"
            self.audio_time_lbl.setText(f"{pos_str} / {dur_str}")

    def on_player_duration_changed(self, duration: int) -> None:
        if duration > 0:
            dur_str = f"{duration // 60000:02d}:{(duration % 60000) // 1000:02d}"
            self.audio_time_lbl.setText(f"00:00 / {dur_str}")

    def set_player_position(self, value: int) -> None:
        duration = self.player.duration()
        if duration > 0:
            target = int(value * duration / 1000)
            self.player.setPosition(target)

    def open_meta_dialog(self) -> None:
        if not self.selected_job:
            return
        job_id = self.selected_job["id"]

        def _fetch_meta():
            return self.api.get_meta(job_id)

        def _on_meta_loaded(meta_data: dict[str, Any]):
            dialog = MetaDialog(meta_data, self)
            dialog.exec()

        worker = Worker(_fetch_meta)
        worker.signals.finished.connect(_on_meta_loaded)
        worker.signals.error.connect(lambda err: QMessageBox.warning(self, "Aviso", f"Erro ao buscar meta.json:\n{err}"))
        self.thread_pool.start(worker)

    def action_trash_or_restore(self) -> None:
        if not self.selected_job:
            return
        job_id = self.selected_job["id"]

        if self.showing_trash:
            # Restaurar
            def _restore():
                return self.api.restore_trash(job_id)

            worker = Worker(_restore)
            worker.signals.finished.connect(lambda _: self.refresh_data())
            worker.signals.error.connect(lambda err: QMessageBox.critical(self, "Erro", f"Falha ao restaurar:\n{err}"))
            self.thread_pool.start(worker)
        else:
            # Mover para Lixeira
            if QMessageBox.question(
                self, "Mover para Lixeira", "Deseja mover este processamento para a pasta trash/?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            ) != QMessageBox.StandardButton.Yes:
                return

            def _trash():
                self.api.delete_job(job_id)

            worker = Worker(_trash)
            worker.signals.finished.connect(lambda _: self.refresh_data())
            worker.signals.error.connect(lambda err: QMessageBox.critical(self, "Erro", f"Falha ao mover para lixeira:\n{err}"))
            self.thread_pool.start(worker)

    def download_selected(self) -> None:
        if not self.selected_job:
            return
        job = self.selected_job
        default_name = f"{Path(job.get('original_name', 'audio')).stem}_{job.get('operation')}.mp3"
        dest, _ = QFileDialog.getSaveFileName(self, "Salvar Arquivo Processado", default_name)
        if not dest:
            return

        def _dl():
            return self.api.download(job["id"], dest)

        worker = Worker(_dl)
        worker.signals.finished.connect(lambda p: QMessageBox.information(self, "Download Concluído", f"Arquivo salvo em:\n{p}"))
        worker.signals.error.connect(lambda err: QMessageBox.critical(self, "Erro", f"Falha no download:\n{err}"))
        self.thread_pool.start(worker)
