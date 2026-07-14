"""Testes para JobRepository."""

import pytest
from uuid import uuid4

from src.infrastructure.repositories.job_repository import JobRepository
from src.models.job import Job, JobStatus


class TestJobRepository:
    """Testes para operações do JobRepository."""

    async def test_create_job(self, db_session):
        """Deve criar um novo job no banco de dados."""
        repo = JobRepository(db_session)
        job = await repo.create(input_image_path="/tmp/test.png")

        assert job.id is not None
        assert job.status == JobStatus.PENDING.value
        assert job.input_image_path == "/tmp/test.png"
        assert job.created_at is not None
        assert job.updated_at is not None

    async def test_create_job_returns_job_object(self, db_session):
        """Deve retornar objeto Job com todos os campos."""
        repo = JobRepository(db_session)
        job = await repo.create(input_image_path="/tmp/diagram.png")

        assert isinstance(job, Job)
        assert job.output_report_path is None
        assert job.error_message is None

    async def test_list_recent_jobs_empty(self, db_session):
        """Deve retornar lista vazia quando não há jobs."""
        repo = JobRepository(db_session)
        recent = await repo.list_recent(limit=10)

        assert recent == []

    async def test_list_recent_jobs(self, db_session):
        """Deve retornar jobs criados recentemente."""
        repo = JobRepository(db_session)

        # Cria jobs
        job1 = await repo.create(input_image_path="/tmp/1.png")
        job2 = await repo.create(input_image_path="/tmp/2.png")

        # Lista deve retorná-los
        recent = await repo.list_recent(limit=10)

        assert len(recent) == 2
        # Mais recentes primeiro
        paths = [j.input_image_path for j in recent]
        assert "/tmp/2.png" in paths
        assert "/tmp/1.png" in paths

    async def test_list_recent_respects_limit(self, db_session):
        """Deve respeitar o parâmetro de limite."""
        repo = JobRepository(db_session)

        # Cria 5 jobs
        for i in range(5):
            await repo.create(input_image_path=f"/tmp/{i}.png")

        # Solicita apenas 2
        recent = await repo.list_recent(limit=2)

        assert len(recent) == 2

    async def test_update_status_changes_status(self, db_session):
        """Deve atualizar o status do job."""
        repo = JobRepository(db_session)
        job = await repo.create(input_image_path="/tmp/test.png")

        # Atualiza para processing
        updated = await repo.update_status(
            job_id=job.id,
            status=JobStatus.PROCESSING,
        )

        assert updated is not None
        assert updated.status == JobStatus.PROCESSING.value

    async def test_update_status_to_completed(self, db_session):
        """Deve atualizar o status do job para completed com relatório."""
        repo = JobRepository(db_session)
        job = await repo.create(input_image_path="/tmp/test.png")

        updated = await repo.update_status(
            job_id=job.id,
            status=JobStatus.COMPLETED,
            output_report_path="reports/123.md",
        )

        assert updated.status == JobStatus.COMPLETED.value
        assert updated.output_report_path == "reports/123.md"

    async def test_update_status_to_failed(self, db_session):
        """Deve atualizar o status do job para failed com erro."""
        repo = JobRepository(db_session)
        job = await repo.create(input_image_path="/tmp/test.png")

        updated = await repo.update_status(
            job_id=job.id,
            status=JobStatus.FAILED,
            error_message="Model not found",
        )

        assert updated.status == JobStatus.FAILED.value
        assert updated.error_message == "Model not found"
