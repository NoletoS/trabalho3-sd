from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator
from uuid import uuid4

from fastapi import BackgroundTasks, Depends, FastAPI, File, Form, HTTPException, Request, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from .config import Settings
from .database import Base, build_database
from .models import MediaJob
from .processor import FFmpegProcessor, OUTPUT_SUFFIXES, ProcessingError
from .schemas import HealthResponse, JobResponse, JobStatus, Operation


ALLOWED_EXTENSIONS = {
    ".mp4", ".mkv", ".avi", ".mov", ".webm", ".mpeg", ".mpg",
    ".mp3", ".wav", ".flac", ".m4a", ".ogg",
}


def _job_response(job: MediaJob) -> JobResponse:
    result = JobResponse.model_validate(job)
    if job.status == JobStatus.completed.value:
        result.download_url = f"/api/jobs/{job.id}/download"
    return result


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    engine, session_factory = build_database(settings.database_url)
    processor = FFmpegProcessor(settings.ffmpeg_path)

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        settings.input_dir.mkdir(parents=True, exist_ok=True)
        settings.output_dir.mkdir(parents=True, exist_ok=True)
        Base.metadata.create_all(engine)
        yield
        engine.dispose()

    application = FastAPI(
        title="Processador Distribuído de Mídia",
        version="1.0.0",
        description="API HTTP para envio e processamento assíncrono de mídia com FFmpeg.",
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
            job.progress = 10
            job.started_at = datetime.now(timezone.utc)
            database.commit()
            try:
                processor.run(
                    Operation(job.operation), Path(job.input_path), Path(job.output_path)
                )
                job.status = JobStatus.completed.value
                job.progress = 100
                job.completed_at = datetime.now(timezone.utc)
                job.error_message = None
            except (ProcessingError, OSError, ValueError) as exc:
                job.status = JobStatus.failed.value
                job.progress = 0
                job.completed_at = datetime.now(timezone.utc)
                job.error_message = str(exc)[:2000]
            database.commit()

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
        original_name = Path(media.filename or "arquivo").name
        extension = Path(original_name).suffix.lower()
        if extension not in ALLOWED_EXTENSIONS:
            allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
            raise HTTPException(415, f"Formato não aceito. Extensões permitidas: {allowed}")

        job_id = str(uuid4())
        input_path = settings.input_dir / f"{job_id}{extension}"
        output_path = settings.output_dir / f"{job_id}{OUTPUT_SUFFIXES[operation]}"
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
            input_path.unlink(missing_ok=True)
            raise
        finally:
            media.file.close()

        job = MediaJob(
            id=job_id,
            original_name=original_name[:255],
            operation=operation.value,
            status=JobStatus.pending.value,
            progress=0,
            input_path=str(input_path),
            output_path=str(output_path),
            file_size=total,
        )
        try:
            database.add(job)
            database.commit()
            database.refresh(job)
        except Exception:
            database.rollback()
            input_path.unlink(missing_ok=True)
            raise
        background_tasks.add_task(process_job, job.id)
        return _job_response(job)

    @application.get("/api/jobs", response_model=list[JobResponse], tags=["processamento"])
    def list_jobs(database: Session = Depends(get_db)) -> list[JobResponse]:
        jobs = database.scalars(
            select(MediaJob).order_by(MediaJob.created_at.desc()).limit(100)
        ).all()
        return [_job_response(job) for job in jobs]

    @application.get(
        "/api/jobs/{job_id}", response_model=JobResponse, tags=["processamento"]
    )
    def get_job(job_id: str, database: Session = Depends(get_db)) -> JobResponse:
        job = database.get(MediaJob, job_id)
        if job is None:
            raise HTTPException(404, "Processamento não encontrado.")
        return _job_response(job)

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
        download_name = f"{Path(job.original_name).stem}_processado{output_path.suffix}"
        return FileResponse(output_path, filename=download_name)

    @application.delete(
        "/api/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["processamento"]
    )
    def delete_job(job_id: str, database: Session = Depends(get_db)) -> None:
        job = database.get(MediaJob, job_id)
        if job is None:
            raise HTTPException(404, "Processamento não encontrado.")
        if job.status == JobStatus.processing.value:
            raise HTTPException(409, "Não é possível remover um processamento em execução.")
        Path(job.input_path).unlink(missing_ok=True)
        Path(job.output_path).unlink(missing_ok=True)
        database.delete(job)
        database.commit()

    return application


app = create_app()
