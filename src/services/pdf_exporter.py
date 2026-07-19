"""Exportação de relatório HTML para PDF via WeasyPrint (RF-05).

Inclui fallback automático para HTML quando WeasyPrint não estiver disponível
ou falhar (ex.: ausência de fontes no ambiente do servidor).
"""

from src.core.logging import get_logger

logger = get_logger(__name__)

# Mensagem exibida dentro do HTML quando o PDF não pôde ser gerado.
_FALLBACK_NOTICE = """
<div style="
    background:#fef3c7;
    border:2px solid #f59e0b;
    border-radius:8px;
    padding:16px 20px;
    margin:24px 0;
    font-family:sans-serif;
    font-size:14px;
    color:#92400e;
">
  <strong>⚠️ PDF não disponível neste ambiente</strong><br/>
  Para gerar o PDF, abra esta página no navegador e use
  <strong>Arquivo → Imprimir → Salvar como PDF</strong>.
</div>
"""


def export_html_to_pdf(html_content: str) -> bytes:
    """Converte HTML para PDF usando WeasyPrint.

    Tenta importar e executar WeasyPrint. Se falhar por qualquer motivo
    (biblioteca ausente, GTK não encontrado, fontes faltando), levanta
    ``WeasyPrintUnavailableError`` para que o chamador possa acionar o fallback.

    Args:
        html_content: Conteúdo HTML já renderizado (string).

    Returns:
        bytes: Conteúdo do PDF gerado.

    Raises:
        WeasyPrintUnavailableError: Se WeasyPrint não estiver disponível
            ou falhar durante a renderização.
    """
    try:
        from weasyprint import HTML  # type: ignore[import-untyped]
    except ImportError as exc:
        raise WeasyPrintUnavailableError(
            "WeasyPrint não está instalado. "
            "Instale com: pip install weasyprint"
        ) from exc
    except Exception as exc:
        # Captura erros de inicialização do GTK / Pango / Cairo em Linux headless
        raise WeasyPrintUnavailableError(
            f"Falha ao inicializar WeasyPrint: {exc}"
        ) from exc

    try:
        pdf_bytes: bytes = HTML(string=html_content).write_pdf()
        logger.debug(f"PDF gerado com sucesso: {len(pdf_bytes):,} bytes")
        return pdf_bytes
    except Exception as exc:
        logger.warning(f"WeasyPrint falhou ao gerar PDF: {exc}")
        raise WeasyPrintUnavailableError(
            f"Falha na geração do PDF: {exc}"
        ) from exc


def export_html_to_pdf_with_fallback(html_content: str) -> tuple[bytes, str]:
    """Tenta gerar PDF; retorna HTML com aviso se WeasyPrint não disponível.

    Args:
        html_content: Conteúdo HTML já renderizado.

    Returns:
        tuple[bytes, str]: (conteúdo em bytes, media_type).
            - Se PDF OK: (pdf_bytes, "application/pdf")
            - Se fallback: (html_bytes, "text/html")
    """
    try:
        pdf_bytes = export_html_to_pdf(html_content)
        return pdf_bytes, "application/pdf"
    except WeasyPrintUnavailableError as exc:
        logger.warning(
            f"Usando fallback HTML para PDF: {exc}. "
            "Retornando HTML com instruções de impressão."
        )
        # Injeta o aviso logo após o <body>
        fallback_html = html_content.replace(
            "<body>",
            f"<body>{_FALLBACK_NOTICE}",
            1,
        )
        return fallback_html.encode("utf-8"), "text/html"


class WeasyPrintUnavailableError(RuntimeError):
    """Levantado quando WeasyPrint não está disponível ou falha ao renderizar."""
