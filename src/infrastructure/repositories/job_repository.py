"""Repositório de Jobs para análise de modelagem de ameaças."""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logging import get_logger
from src.models.job import Job, JobStatus

logger = get_logger(__name__)


class JobRepository:
    """Repositório para operações de persistência de Jobs."""

    def __init__(self, session: AsyncSession):
        """Inicializa o repositório com uma sessão do banco.

        Args:
            session: Sessão assíncrona do SQLAlchemy.
        """
        self.session = session

    async def create(self, input_image_path: str) -> Job:
        """Cria um novo Job de análise.

        Args:
            input_image_path: Caminho da imagem de entrada.

        Returns:
            Job: Job criado no banco de dados.
        """
        job = Job(
            input_image_path=input_image_path,
            status=JobStatus.PENDING.value,
        )
        self.session.add(job)
        await self.session.commit()
        await self.session.refresh(job)
        logger.info(f"Job created: {job.id}")
        return job

    async def get_by_id(self, job_id: UUID | str) -> Job | None:
        """Busca um Job pelo ID.

        Args:
            job_id: UUID ou string do job.

        Returns:
            Job | None: Job encontrado ou None.
        """
        job_id_str = str(job_id)
        result = await self.session.execute(
            select(Job).where(Job.id == job_id_str)
        )
        return result.scalar_one_or_none()

    async def update_status(
        self,
        job_id: UUID,
        status: JobStatus,
        output_report_path: str | None = None,
        error_message: str | None = None,
    ) -> Job | None:
        """Atualiza o status de um Job.

        Args:
            job_id: UUID do job.
            status: Novo status.
            output_report_path: Caminho do relatório gerado (opcional).
            error_message: Mensagem de erro (opcional).

        Returns:
            Job | None: Job atualizado ou None se não encontrado.
        """
        job = await self.get_by_id(job_id)
        if not job:
            return None

        job.status = status.value
        job.updated_at = datetime.now(timezone.utc)

        if output_report_path:
            job.output_report_path = output_report_path

        if error_message:
            job.error_message = error_message

        await self.session.commit()
        await self.session.refresh(job)
        logger.info(f"Job {job_id} status updated to {status.value}")
        return job

    async def list_recent(self, limit: int = 10) -> list[Job]:
        """Lista os jobs mais recentes.

        Args:
            limit: Quantidade máxima de jobs.

        Returns:
            list[Job]: Lista de jobs ordenados por data de criação.
        """
        result = await self.session.execute(
            select(Job)
            .order_by(Job.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
