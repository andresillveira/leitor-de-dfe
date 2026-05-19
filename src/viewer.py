"""
viewer.py — Motor de visualização de documentos fiscais.

Gera PDFs de DANFE/DACTE usando a biblioteca brazilfiscalreport
e abre no leitor padrão do sistema operacional.
"""

import os
import tempfile
import shutil
from pathlib import Path

from brazilfiscalreport.danfe import Danfe
from brazilfiscalreport.dacte import Dacte

from detector import DocInfo, DocType, identificar


# Diretório temporário para cache de PDFs gerados
TEMP_DIR = Path(tempfile.gettempdir()) / "leitor_dfe"


def _garantir_temp_dir():
    """Cria o diretório temporário se não existir."""
    TEMP_DIR.mkdir(parents=True, exist_ok=True)


def _nome_pdf_cache(chave_acesso: str) -> Path:
    """Gera o caminho do PDF em cache baseado na chave de acesso."""
    chave_limpa = chave_acesso.replace(" ", "")
    if not chave_limpa:
        chave_limpa = "documento_sem_chave"
    return TEMP_DIR / f"{chave_limpa}.pdf"


def gerar_pdf(xml_content: str, doc_info: DocInfo) -> str:
    """
    Gera o PDF (DANFE ou DACTE) a partir do conteúdo XML.
    
    Args:
        xml_content: Conteúdo do arquivo XML.
        doc_info: Informações do documento já identificado.
    
    Returns:
        Caminho absoluto do PDF gerado.
    
    Raises:
        RuntimeError: Se a geração do PDF falhar.
    """
    _garantir_temp_dir()
    
    pdf_path = _nome_pdf_cache(doc_info.chave_acesso)
    
    # Cache: reutiliza PDF se já existe
    if pdf_path.exists():
        return str(pdf_path)
    
    try:
        if doc_info.tipo in (DocType.NFE, DocType.NFCE):
            doc = Danfe(xml=xml_content)
        elif doc_info.tipo == DocType.CTE:
            doc = Dacte(xml=xml_content)
        else:
            raise RuntimeError(f"Tipo de documento não suportado: {doc_info.tipo}")
        
        doc.output(str(pdf_path))
        return str(pdf_path)
    
    except Exception as e:
        # Remove arquivo parcial se houver falha
        if pdf_path.exists():
            pdf_path.unlink()
        raise RuntimeError(f"Erro ao gerar PDF: {e}")


def abrir_pdf(pdf_path: str):
    """
    Abre o PDF no leitor padrão do sistema operacional.
    
    Args:
        pdf_path: Caminho absoluto do arquivo PDF.
    """
    os.startfile(pdf_path)


def salvar_pdf_como(pdf_path: str, destino: str):
    """
    Copia o PDF gerado para o destino escolhido pelo usuário.
    
    Args:
        pdf_path: Caminho do PDF gerado (cache).
        destino: Caminho de destino escolhido pelo usuário.
    """
    shutil.copy2(pdf_path, destino)


def limpar_cache():
    """Remove todos os PDFs do cache temporário."""
    if TEMP_DIR.exists():
        shutil.rmtree(TEMP_DIR, ignore_errors=True)


def processar_xml(xml_path: str) -> tuple[DocInfo, str]:
    """
    Pipeline completo: lê XML → identifica → gera PDF.
    
    Args:
        xml_path: Caminho do arquivo XML.
    
    Returns:
        Tupla (DocInfo, caminho_do_pdf).
    
    Raises:
        FileNotFoundError: Se o arquivo XML não existir.
        ValueError: Se o XML não for um DFe válido.
        RuntimeError: Se a geração do PDF falhar.
    """
    path = Path(xml_path)
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {xml_path}")
    
    if not path.suffix.lower() == ".xml":
        raise ValueError("O arquivo selecionado não é um XML.")
    
    # Tenta ler com diferentes encodings
    xml_content = None
    for encoding in ("utf-8", "latin-1", "cp1252"):
        try:
            xml_content = path.read_text(encoding=encoding)
            break
        except (UnicodeDecodeError, UnicodeError):
            continue
    
    if xml_content is None:
        raise ValueError("Não foi possível ler o arquivo XML (encoding não suportado).")
    
    # Remove BOM se presente
    if xml_content.startswith("\ufeff"):
        xml_content = xml_content[1:]
    
    doc_info = identificar(xml_content)
    pdf_path = gerar_pdf(xml_content, doc_info)
    
    return doc_info, pdf_path
