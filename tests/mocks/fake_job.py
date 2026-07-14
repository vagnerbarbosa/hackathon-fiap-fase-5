"""Mock Job for Spec 006 testing."""

from datetime import datetime, timezone
from uuid import uuid4

from src.domain.models import Job, JobStatus

fake_job = Job(
    id=uuid4(),
    status=JobStatus.COMPLETED,
    input_image_path="/uploads/diagrama.png",
    output_report_path="/reports/job-123/report.md",
    created_at=datetime.now(timezone.utc),
    updated_at=datetime.now(timezone.utc),
)

if __name__ == "__main__":
    print(f"Created mock job: {fake_job.id}")
    print(f"  Status: {fake_job.status.value}")
    print(f"  Input: {fake_job.input_image_path}")
    print(f"  Output: {fake_job.output_report_path}")
