from __future__ import annotations


def create_job(client, name="sample.wav", operation="extract_mp3"):
    return client.post(
        "/api/jobs",
        data={"operation": operation},
        files={"media": (name, b"fake-media", "application/octet-stream")},
    )


def test_health_reports_dependencies(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok", "ffmpeg": "ok"}


def test_upload_process_list_and_download(client):
    created = create_job(client)
    assert created.status_code == 202
    job_id = created.json()["id"]

    detail = client.get(f"/api/jobs/{job_id}")
    assert detail.status_code == 200
    assert detail.json()["status"] == "completed"
    assert detail.json()["progress"] == 100
    assert detail.json()["download_url"] == f"/api/jobs/{job_id}/download"

    listing = client.get("/api/jobs")
    assert [job["id"] for job in listing.json()] == [job_id]

    download = client.get(f"/api/jobs/{job_id}/download")
    assert download.status_code == 200
    assert download.content == b"processed-media"
    assert "sample_processado.mp3" in download.headers["content-disposition"]


def test_rejects_unsupported_extension(client):
    response = create_job(client, name="malware.exe")
    assert response.status_code == 415
    assert client.get("/api/jobs").json() == []


def test_rejects_unknown_operation(client):
    response = create_job(client, operation="unknown")
    assert response.status_code == 422


def test_delete_removes_completed_job(client):
    job_id = create_job(client).json()["id"]
    response = client.delete(f"/api/jobs/{job_id}")
    assert response.status_code == 204
    assert client.get(f"/api/jobs/{job_id}").status_code == 404


def test_processing_failure_is_persisted(client):
    def fail(*_args):
        raise OSError("falha simulada")

    client.app.state.processor.run = fail
    job_id = create_job(client).json()["id"]
    detail = client.get(f"/api/jobs/{job_id}").json()
    assert detail["status"] == "failed"
    assert detail["error_message"] == "falha simulada"
    assert client.get(f"/api/jobs/{job_id}/download").status_code == 409
