from __future__ import annotations

import json
import shutil
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator
from uuid import uuid4

from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from .config import Settings
from .database import Base, build_database
from .models import MediaJob
from .processor import (
    OPERATION_PARAMS,
    FFmpegProcessor,
    ProcessingError,
    calculate_sha256,
)
from .schemas import HealthResponse, JobResponse, JobStatus, MetaResponse, Operation
from .web import HTML_PAGE


ALLOWED_EXTENSIONS = {
    ".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac", ".wma",
    ".mp4", ".mkv", ".avi", ".mov", ".webm", ".mpg", ".mpeg",
}


def _job_response(job: MediaJob) -> JobResponse:
    result = JobResponse.model_validate(job)
    result.meta_url = f"/api/jobs/{job.id}/meta"
    
    if job.input_path and Path(job.input_path).is_file():
        result.original_audio_url = f"/api/jobs/{job.id}/original/audio"
    if job.original_waveform_path and Path(job.original_waveform_path).is_file():
        result.original_waveform_url = f"/api/jobs/{job.id}/original/waveform"
        
    if job.status == JobStatus.completed.value:
        result.download_url = f"/api/jobs/{job.id}/download"
        if job.output_path and Path(job.output_path).is_file():
            result.processed_audio_url = f"/api/jobs/{job.id}/processed/audio"
        if job.output_waveform_path and Path(job.output_waveform_path).is_file():
            result.processed_waveform_url = f"/api/jobs/{job.id}/processed/waveform"
            
    return result


def _save_meta_json(
    meta_path: Path,
    job_id: str,
    original_name: str,
    operation: str,
    status_val: str,
    created_at: datetime,
    completed_at: datetime | None,
    original_checksum: str | None,
    processed_checksum: str | None,
    original_size: int,
    processed_size: int | None,
    parameters: dict[str, Any],
    media_info: dict[str, Any],
) -> None:
    meta_data = {
        "id": job_id,
        "original_name": original_name,
        "operation": operation,
        "status": status_val,
        "created_at": created_at.isoformat() if created_at else None,
        "completed_at": completed_at.isoformat() if completed_at else None,
        "original_checksum_sha256": original_checksum,
        "processed_checksum_sha256": processed_checksum,
        "original_size_bytes": original_size,
        "processed_size_bytes": processed_size,
        "parameters": parameters,
        "media_info": media_info,
    }
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    with meta_path.open("w", encoding="utf-8") as f:
        json.dump(meta_data, f, indent=2, ensure_ascii=False)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    engine, session_factory = build_database(settings.database_url)
    processor = FFmpegProcessor(settings.ffmpeg_path, settings.ffprobe_path)

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        settings.storage_root.mkdir(parents=True, exist_ok=True)
        settings.trash_dir.mkdir(parents=True, exist_ok=True)
        Base.metadata.create_all(engine)
        yield
        engine.dispose()

    application = FastAPI(
        title="Processador Distribuído de Áudio e Mídia",
        version="2.0.0",
        description="API HTTP para envio, processamento e gestão de áudio distribuído com FFmpeg e PostgreSQL.",
        lifespan=lifespan,
    )
    application.state.settings = settings
    application.state.session_factory = session_factory
    application.state.processor = processor
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    def get_db(request: Request) -> Iterator[Session]:
        with request.app.state.session_factory() as database:
            yield database

    def process_job(job_id: str) -> None:
        with session_factory() as database:
            job = database.get(MediaJob, job_id)
            if job is None:
                return

            job.status = JobStatus.processing.value
            job.progress = 20
            job.started_at = datetime.now(timezone.utc)
            database.commit()

            input_p = Path(job.input_path)
            output_p = Path(job.output_path)
            meta_p = Path(job.meta_json_path)
            orig_waveform_p = Path(job.original_waveform_path)
            proc_waveform_p = Path(job.output_waveform_path)

            # 1. Gerar waveform do áudio original caso ainda não gerada
            if not orig_waveform_p.is_file():
                processor.generate_waveform(input_p, orig_waveform_p)

            # 2. Executar o processamento FFmpeg
            try:
                op = Operation(job.operation)
                processor.run(op, input_p, output_p)
                job.progress = 75
                database.commit()

                # 3. Checksum e Waveform do processado
                processed_checksum = calculate_sha256(output_p)
                processor.generate_waveform(output_p, proc_waveform_p)
                media_info = processor.get_media_info(output_p)

                job.status = JobStatus.completed.value
                job.progress = 100
                job.completed_at = datetime.now(timezone.utc)
                job.processed_checksum = processed_checksum
                job.error_message = None

                # 4. Atualizar meta.json
                _save_meta_json(
                    meta_path=meta_p,
                    job_id=job.id,
                    original_name=job.original_name,
                    operation=job.operation,
                    status_val=job.status,
                    created_at=job.created_at,
                    completed_at=job.completed_at,
                    original_checksum=job.original_checksum,
                    processed_checksum=processed_checksum,
                    original_size=job.file_size,
                    processed_size=output_p.stat().st_size if output_p.is_file() else None,
                    parameters=OPERATION_PARAMS.get(op, {}),
                    media_info=media_info,
                )

            except (ProcessingError, OSError, ValueError) as exc:
                job.status = JobStatus.failed.value
                job.progress = 0
                job.completed_at = datetime.now(timezone.utc)
                job.error_message = str(exc)[:2000]

                _save_meta_json(
                    meta_path=meta_p,
                    job_id=job.id,
                    original_name=job.original_name,
                    operation=job.operation,
                    status_val=job.status,
                    created_at=job.created_at,
                    completed_at=job.completed_at,
                    original_checksum=job.original_checksum,
                    processed_checksum=None,
                    original_size=job.file_size,
                    processed_size=None,
                    parameters=OPERATION_PARAMS.get(Operation(job.operation), {}),
                    media_info={"error": str(exc)},
                )

            database.commit()

    @application.get("/", response_class=HTMLResponse, tags=["web"])
    def index_page() -> str:
        return HTML_PAGE

    @application.get("/api/health", response_model=HealthResponse, tags=["sistema"])
    def health(database: Session = Depends(get_db)) -> HealthResponse:
        try:
            database.execute(text("SELECT 1"))
            db_status = "ok"
        except Exception:
            db_status = "indisponível"
        ffmpeg_status = "ok" if processor.is_available() else "não encontrado"
        overall = "ok" if db_status == "ok" and ffmpeg_status == "ok" else "degradado"
        return HealthResponse(status=overall, database=db_status, ffmpeg=ffmpeg_status)

    @application.post(
        "/api/jobs",
        response_model=JobResponse,
        status_code=status.HTTP_202_ACCEPTED,
        tags=["processamento"],
    )
    def create_job(
        background_tasks: BackgroundTasks,
        media: UploadFile = File(...),
        operation: Operation = Form(...),
        database: Session = Depends(get_db),
    ) -> JobResponse:
        original_name = Path(media.filename or "audio").name
        extension = Path(original_name).suffix.lower()
        if not extension:
            extension = ".mp3"
        if extension not in ALLOWED_EXTENSIONS:
            allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
            raise HTTPException(415, f"Formato não aceito. Extensões permitidas: {allowed}")

        job_id = str(uuid4())
        job_dir = settings.job_dir(job_id)
        original_dir = job_dir / "original"
        processed_dir = job_dir / "processed"
        original_dir.mkdir(parents=True, exist_ok=True)
        processed_dir.mkdir(parents=True, exist_ok=True)

        # Regra: o nome do arquivo armazenado é sempre audio.{ext}, organizado em subpastas
        input_path = original_dir / f"audio{extension}"
        out_ext = processor.get_output_suffix(operation, extension)
        output_path = processed_dir / f"audio{out_ext}"

        original_waveform = original_dir / "waveform.png"
        output_waveform = processed_dir / "waveform.png"
        meta_json_path = job_dir / "meta.json"

        max_bytes = settings.max_upload_mb * 1024 * 1024
        total = 0
        try:
            with input_path.open("wb") as target:
                while chunk := media.file.read(1024 * 1024):
                    total += len(chunk)
                    if total > max_bytes:
                        raise HTTPException(
                            413, f"O arquivo excede o limite de {settings.max_upload_mb} MB."
                        )
                    target.write(chunk)
        except Exception:
            shutil.rmtree(job_dir, ignore_errors=True)
            raise
        finally:
            media.file.close()

        # Calcular SHA-256 do arquivo original recebido
        original_checksum = calculate_sha256(input_path)
        processor.generate_waveform(input_path, original_waveform)
        media_info = processor.get_media_info(input_path)

        # Gravar meta.json inicial
        _save_meta_json(
            meta_path=meta_json_path,
            job_id=job_id,
            original_name=original_name,
            operation=operation.value,
            status_val=JobStatus.pending.value,
            created_at=datetime.now(timezone.utc),
            completed_at=None,
            original_checksum=original_checksum,
            processed_checksum=None,
            original_size=total,
            processed_size=None,
            parameters=OPERATION_PARAMS.get(operation, {}),
            media_info=media_info,
        )

        job = MediaJob(
            id=job_id,
            original_name=original_name[:255],
            operation=operation.value,
            status=JobStatus.pending.value,
            progress=0,
            input_path=str(input_path),
            output_path=str(output_path),
            original_waveform_path=str(original_waveform),
            output_waveform_path=str(output_waveform),
            meta_json_path=str(meta_json_path),
            original_checksum=original_checksum,
            processed_checksum=None,
            is_trashed=False,
            file_size=total,
        )

        try:
            database.add(job)
            database.commit()
            database.refresh(job)
        except Exception:
            database.rollback()
            shutil.rmtree(job_dir, ignore_errors=True)
            raise

        background_tasks.add_task(process_job, job.id)
        return _job_response(job)

    @application.get("/api/jobs", response_model=list[JobResponse], tags=["processamento"])
    def list_jobs(database: Session = Depends(get_db)) -> list[JobResponse]:
        jobs = database.scalars(
            select(MediaJob)
            .where(MediaJob.is_trashed.is_(False))
            .order_by(MediaJob.created_at.desc())
            .limit(100)
        ).all()
        return [_job_response(job) for job in jobs]

    @application.get("/api/trash", response_model=list[JobResponse], tags=["lixeira"])
    def list_trash(database: Session = Depends(get_db)) -> list[JobResponse]:
        jobs = database.scalars(
            select(MediaJob)
            .where(MediaJob.is_trashed.is_(True))
            .order_by(MediaJob.trashed_at.desc())
            .limit(100)
        ).all()
        return [_job_response(job) for job in jobs]

    @application.post("/api/trash/{job_id}/restore", response_model=JobResponse, tags=["lixeira"])
    def restore_trash(job_id: str, database: Session = Depends(get_db)) -> JobResponse:
        job = database.get(MediaJob, job_id)
        if job is None:
            raise HTTPException(404, "Processamento não encontrado.")
        if not job.is_trashed:
            return _job_response(job)

        active_dir = settings.job_dir(job_id)
        trash_dir = settings.job_trash_dir(job_id)

        if trash_dir.exists():
            if active_dir.exists():
                shutil.rmtree(active_dir, ignore_errors=True)
            shutil.move(str(trash_dir), str(active_dir))

            # Atualizar paths para pasta ativa
            job.input_path = str(active_dir / "original" / Path(job.input_path).name)
            job.output_path = str(active_dir / "processed" / Path(job.output_path).name)
            job.original_waveform_path = str(active_dir / "original" / "waveform.png")
            job.output_waveform_path = str(active_dir / "processed" / "waveform.png")
            job.meta_json_path = str(active_dir / "meta.json")

        job.is_trashed = False
        job.trashed_at = None
        database.commit()
        return _job_response(job)

    @application.get(
        "/api/jobs/{job_id}", response_model=JobResponse, tags=["processamento"]
    )
    def get_job(job_id: str, database: Session = Depends(get_db)) -> JobResponse:
        job = database.get(MediaJob, job_id)
        if job is None:
            raise HTTPException(404, "Processamento não encontrado.")
        return _job_response(job)

    @application.get("/api/jobs/{job_id}/meta", response_model=MetaResponse, tags=["processamento"])
    def get_job_meta(job_id: str, database: Session = Depends(get_db)) -> Any:
        job = database.get(MediaJob, job_id)
        if job is None:
            raise HTTPException(404, "Processamento não encontrado.")
        meta_path = Path(job.meta_json_path) if job.meta_json_path else settings.job_dir(job_id) / "meta.json"
        if not meta_path.is_file():
            raise HTTPException(404, "Arquivo meta.json não encontrado no servidor.")
        with meta_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    @application.get("/api/jobs/{job_id}/original/audio", tags=["streaming"])
    def get_original_audio(job_id: str, database: Session = Depends(get_db)) -> FileResponse:
        job = database.get(MediaJob, job_id)
        if job is None or not job.input_path or not Path(job.input_path).is_file():
            raise HTTPException(404, "Áudio original não encontrado.")
        path = Path(job.input_path)
        media_type = "audio/mpeg" if path.suffix == ".mp3" else ("audio/wav" if path.suffix == ".wav" else None)
        return FileResponse(path, media_type=media_type)

    @application.get("/api/jobs/{job_id}/original/waveform", tags=["streaming"])
    def get_original_waveform(job_id: str, database: Session = Depends(get_db)) -> FileResponse:
        job = database.get(MediaJob, job_id)
        if job is None or not job.original_waveform_path or not Path(job.original_waveform_path).is_file():
            raise HTTPException(404, "Forma de onda original não encontrada.")
        return FileResponse(Path(job.original_waveform_path), media_type="image/png")

    @application.get("/api/jobs/{job_id}/processed/audio", tags=["streaming"])
    def get_processed_audio(job_id: str, database: Session = Depends(get_db)) -> FileResponse:
        job = database.get(MediaJob, job_id)
        if job is None or job.status != JobStatus.completed.value or not job.output_path or not Path(job.output_path).is_file():
            raise HTTPException(404, "Áudio processado não disponível.")
        path = Path(job.output_path)
        media_type = "audio/mpeg" if path.suffix == ".mp3" else ("audio/wav" if path.suffix == ".wav" else None)
        return FileResponse(path, media_type=media_type)

    @application.get("/api/jobs/{job_id}/processed/waveform", tags=["streaming"])
    def get_processed_waveform(job_id: str, database: Session = Depends(get_db)) -> FileResponse:
        job = database.get(MediaJob, job_id)
        if job is None or not job.output_waveform_path or not Path(job.output_waveform_path).is_file():
            raise HTTPException(404, "Forma de onda processada não encontrada.")
        return FileResponse(Path(job.output_waveform_path), media_type="image/png")

    @application.get("/api/jobs/{job_id}/download", tags=["processamento"])
    def download_result(job_id: str, database: Session = Depends(get_db)) -> FileResponse:
        job = database.get(MediaJob, job_id)
        if job is None:
            raise HTTPException(404, "Processamento não encontrado.")
        if job.status != JobStatus.completed.value:
            raise HTTPException(409, "O resultado ainda não está disponível.")
        output_path = Path(job.output_path)
        if not output_path.is_file():
            raise HTTPException(410, "O arquivo processado não está mais no servidor.")
        download_name = f"{Path(job.original_name).stem}_{job.operation}{output_path.suffix}"
        return FileResponse(output_path, filename=download_name)

    @application.delete(
        "/api/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["processamento"]
    )
    def delete_job(job_id: str, database: Session = Depends(get_db)) -> None:
        """Move o diretório do UUID para storage/trash/<uuid>."""
        job = database.get(MediaJob, job_id)
        if job is None:
            raise HTTPException(404, "Processamento não encontrado.")
        if job.status == JobStatus.processing.value:
            raise HTTPException(409, "Não é possível remover um processamento em execução.")

        active_dir = settings.job_dir(job_id)
        trash_dir = settings.job_trash_dir(job_id)

        if active_dir.exists():
            if trash_dir.exists():
                shutil.rmtree(trash_dir, ignore_errors=True)
            settings.trash_dir.mkdir(parents=True, exist_ok=True)
            shutil.move(str(active_dir), str(trash_dir))

            # Atualizar paths para a pasta trash
            job.input_path = str(trash_dir / "original" / Path(job.input_path).name)
            job.output_path = str(trash_dir / "processed" / Path(job.output_path).name)
            job.original_waveform_path = str(trash_dir / "original" / "waveform.png")
            job.output_waveform_path = str(trash_dir / "processed" / "waveform.png")
            job.meta_json_path = str(trash_dir / "meta.json")

        job.is_trashed = True
        job.trashed_at = datetime.now(timezone.utc)
        database.commit()

    return application


app = create_app()
