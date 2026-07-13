"""Countermeasure lookup and STRIDE fallback rules."""

from src.core.vulnerability_db import VulnerabilityMapping
from src.domain.models import Countermeasure


DEFAULT_COUNTERMEASURES: dict[str, tuple[Countermeasure, ...]] = {
    "S": (
        Countermeasure(
            title="Exigir autenticacao forte",
            description=(
                "Aplicar MFA, tokens assinados e expiracao curta para reduzir "
                "spoofing de identidade."
            ),
            owasp_ref="OWASP Authentication Cheat Sheet",
        ),
        Countermeasure(
            title="Validar identidade entre servicos",
            description=(
                "Usar mTLS ou credenciais por servico quando a origem da chamada "
                "precisar ser autenticada."
            ),
            owasp_ref="OWASP Transport Layer Security Cheat Sheet",
        ),
    ),
    "T": (
        Countermeasure(
            title="Proteger integridade dos dados",
            description=(
                "Usar TLS 1.3, HMAC ou assinatura digital para detectar "
                "alteracoes de mensagens."
            ),
            owasp_ref="OWASP Cryptographic Storage Cheat Sheet",
        ),
        Countermeasure(
            title="Validar entradas e estado",
            description=(
                "Rejeitar payloads inesperados e validar autorizacao antes de "
                "alterar dados sensiveis."
            ),
            owasp_ref="OWASP Input Validation Cheat Sheet",
        ),
    ),
    "R": (
        Countermeasure(
            title="Centralizar auditoria",
            description=(
                "Registrar acoes sensiveis com usuario, origem, resultado e "
                "timestamp confiavel."
            ),
            owasp_ref="OWASP Logging Cheat Sheet",
        ),
        Countermeasure(
            title="Proteger logs contra alteracao",
            description="Enviar logs para armazenamento imutavel ou com controle de integridade.",
            owasp_ref="OWASP Logging Cheat Sheet",
        ),
    ),
    "I": (
        Countermeasure(
            title="Criptografar dados sensiveis",
            description="Usar criptografia em transito e em repouso para dados confidenciais.",
            owasp_ref="OWASP Cryptographic Storage Cheat Sheet",
        ),
        Countermeasure(
            title="Minimizar exposicao de dados",
            description=(
                "Aplicar mascaramento, tokenizacao e principio de menor exposicao "
                "nas respostas e logs."
            ),
            owasp_ref="OWASP Data Protection Cheat Sheet",
        ),
    ),
    "D": (
        Countermeasure(
            title="Aplicar controle de consumo",
            description=(
                "Usar rate limiting, timeouts, limites de payload e quotas por "
                "usuario ou origem."
            ),
            owasp_ref="OWASP Denial of Service Cheat Sheet",
        ),
        Countermeasure(
            title="Isolar falhas de dependencias",
            description=(
                "Aplicar circuit breaker, retries com backoff e degradacao "
                "controlada."
            ),
            owasp_ref="NIST SP 800-160",
        ),
    ),
    "E": (
        Countermeasure(
            title="Aplicar least privilege",
            description=(
                "Conceder apenas permissoes necessarias e revisar escopos de "
                "usuarios, tokens e servicos."
            ),
            owasp_ref="OWASP Authorization Cheat Sheet",
        ),
        Countermeasure(
            title="Isolar execucao sensivel",
            description=(
                "Usar RBAC, sandboxing e separacao de papeis para conter "
                "escalacao de privilegios."
            ),
            owasp_ref="OWASP Authorization Cheat Sheet",
        ),
    ),
}


class CountermeasureLookup:
    """Resolve specific or generic countermeasures for a threat."""

    def for_mapping_or_category(
        self,
        mapping: VulnerabilityMapping | None,
        stride_category: str,
    ) -> list[Countermeasure]:
        """Return mapping countermeasures or STRIDE defaults."""
        if mapping and mapping.countermeasures:
            return [countermeasure.model_copy() for countermeasure in mapping.countermeasures]

        return self.for_category(stride_category)

    def for_category(self, stride_category: str) -> list[Countermeasure]:
        """Return generic countermeasures for a STRIDE category."""
        countermeasures = DEFAULT_COUNTERMEASURES.get(stride_category.upper(), ())
        return [countermeasure.model_copy() for countermeasure in countermeasures]


__all__ = ["CountermeasureLookup", "DEFAULT_COUNTERMEASURES"]
