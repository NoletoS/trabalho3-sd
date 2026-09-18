from __future__ import annotations

import json
from pathlib import Path


def create_job(client, name="audio.wav", operation="normalize_volume"):
    return client.post(
        "/api/jobs",
        data={"operation": operation},
        files={"media": (name, b"sample-audio-data", "application/octet-stream")},
    )


def test_health_reports_dependencies(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok", "ffmpeg": "ok"}


def test_upload_creates_uuid_structure_and_meta_json(client):
    created = create_job(client, name="musica.wav", operation="normalize_volume")
    assert created.status_code == 202
    job_id = created.json()["id"]

    detail = client.get(f"/api/jobs/{job_id}")
    assert detail.status_code == 200
    data = detail.json()
    assert data["status"] == "completed"
    assert data["progress"] == 100
    assert data["original_checksum"] is not None
    assert data["processed_checksum"] is not None
    assert data["original_audio_url"] == f"/api/jobs/{job_id}/original/audio"
    assert data["processed_audio_url"] == f"/api/jobs/{job_id}/processed/audio"

    # Verificar endpoint meta.json
    meta_resp = client.get(f"/api/jobs/{job_id}/meta")
    assert meta_resp.status_code == 200
    meta = meta_resp.json()
    assert meta["id"] == job_id
    assert meta["original_name"] == "musica.wav"
    assert meta["operation"] == "normalize_volume"
    assert meta["original_checksum_sha256"] is not None
    assert meta["processed_checksum_sha256"] is not None
    assert "parameters" in meta

    # Verificar streaming do áudio original e processado
    orig_audio = client.get(f"/api/jobs/{job_id}/original/audio")
    assert orig_audio.status_code == 200
    assert orig_audio.content == b"sample-audio-data"

    proc_audio = client.get(f"/api/jobs/{job_id}/processed/audio")
    assert proc_audio.status_code == 200
    assert proc_audio.content == b"processed-audio-media"


def test_trash_move_and_restore(client):
    job_id = create_job(client).json()["id"]

    # Verificar que está nos ativos
    assert any(j["id"] == job_id for j in client.get("/api/jobs").json())
    assert not any(j["id"] == job_id for j in client.get("/api/trash").json())

    # Mover para Lixeira
    del_resp = client.delete(f"/api/jobs/{job_id}")
    assert del_resp.status_code == 204

    # Não deve mais aparecer em /api/jobs, mas deve aparecer em /api/trash
    assert not any(j["id"] == job_id for j in client.get("/api/jobs").json())
    assert any(j["id"] == job_id for j in client.get("/api/trash").json())

    # Restaurar da Lixeira
    rest_resp = client.post(f"/api/trash/{job_id}/restore")
    assert rest_resp.status_code == 200
    assert rest_resp.json()["is_trashed"] is False

    # Deve voltar a aparecer nos ativos
    assert any(j["id"] == job_id for j in client.get("/api/jobs").json())
    assert not any(j["id"] == job_id for j in client.get("/api/trash").json())


def test_rejects_unsupported_extension(client):
    response = create_job(client, name="documento.pdf")
    assert response.status_code == 415


def test_rejects_unknown_operation(client):
    response = create_job(client, operation="operacao_invalida")
    assert response.status_code == 422


def test_web_interface_served_at_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Processador Distribuído de Áudio" in response.text
