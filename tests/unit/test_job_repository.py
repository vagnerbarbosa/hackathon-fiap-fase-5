"""Tests for JobRepository."""

import pytest
from uuid import uuid4

from src.infrastructure.repositories.job_repository import JobRepository
from src.models.job import Job, JobStatus


class TestJobRepository:
    """Test JobRepository operations."""

    async def test_create_job(self, db_session):
        """Should create a new job in the database."""
        repo = JobRepository(db_session)
        job = await repo.create(input_image_path="/tmp/test.png")

        assert job.id is not None
        assert job.status == JobStatus.PENDING.value
        assert job.input_image_path == "/tmp/test.png"
        assert job.created_at is not None
        assert job.updated_at is not None

    async def test_create_job_returns_job_object(self, db_session):
        """Should return Job object with all fields."""
        repo = JobRepository(db_session)
        job = await repo.create(input_image_path="/tmp/diagram.png")

        assert isinstance(job, Job)
        assert job.output_report_path is None
        assert job.error_message is None

    async def test_list_recent_jobs_empty(self, db_session):
        """Should return empty list when no jobs."""
        repo = JobRepository(db_session)
        recent = await repo.list_recent(limit=10)

        assert recent == []

    async def test_list_recent_jobs(self, db_session):
        """Should return recently created jobs."""
        repo = JobRepository(db_session)

        # Create jobs
        job1 = await repo.create(input_image_path="/tmp/1.png")
        job2 = await repo.create(input_image_path="/tmp/2.png")

        # List should return them
        recent = await repo.list_recent(limit=10)

        assert len(recent) == 2
        # Most recent first
        paths = [j.input_image_path for j in recent]
        assert "/tmp/2.png" in paths
        assert "/tmp/1.png" in paths

    async def test_list_recent_respects_limit(self, db_session):
        """Should respect the limit parameter."""
        repo = JobRepository(db_session)

        # Create 5 jobs
        for i in range(5):
            await repo.create(input_image_path=f"/tmp/{i}.png")

        # Request only 2
        recent = await repo.list_recent(limit=2)

        assert len(recent) == 2

    async def test_update_status_changes_status(self, db_session):
        """Should update job status."""
        repo = JobRepository(db_session)
        job = await repo.create(input_image_path="/tmp/test.png")

        # Update to processing
        updated = await repo.update_status(
            job_id=job.id,
            status=JobStatus.PROCESSING,
        )

        assert updated is not None
        assert updated.status == JobStatus.PROCESSING.value

    async def test_update_status_to_completed(self, db_session):
        """Should update job status to completed with report."""
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
        """Should update job status to failed with error."""
        repo = JobRepository(db_session)
        job = await repo.create(input_image_path="/tmp/test.png")

        updated = await repo.update_status(
            job_id=job.id,
            status=JobStatus.FAILED,
            error_message="Model not found",
        )

        assert updated.status == JobStatus.FAILED.value
        assert updated.error_message == "Model not found"
