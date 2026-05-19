"""
detector.py — Identificação automática do tipo de documento fiscal eletrônico.

Lê a estrutura do XML e classifica como NFe (55), NFCe (65) ou CTe (57).
Extrai metadados básicos para preview na interface.
"""

import xml.etree.ElementTree as ET
from enum import Enum
from dataclasses import dataclass
from typing import Optional


class DocType(Enum):
    """Tipos de documento fiscal eletrônico suportados."""
    NFE = "NFe (Modelo 55)"
    NFCE = "NFCe (Modelo 65)"
    CTE = "CTe (Modelo 57)"


@dataclass
class DocInfo:
    """Metadados extraídos do XML para preview."""
    tipo: DocType
    chave_acesso: str = ""
    emitente: str = ""
    destinatario: str = ""
    valor_total: str = ""
    data_emissao: str = ""
    natureza_operacao: str = ""
    numero: str = ""


# Namespaces comuns dos documentos fiscais brasileiros
NS_NFE = "http://www.portalfiscal.inf.br/nfe"
NS_CTE = "http://www.portalfiscal.inf.br/cte"


def _find_text(root: ET.Element, xpath: str, namespaces: dict) -> str:
    """Busca texto em um elemento XML usando xpath simplificado com namespace."""
    for prefix, uri in namespaces.items():
        xpath = xpath.replace(f"{prefix}:", f"{{{uri}}}")
    
    elem = root.find(xpath)
    if elem is not None and elem.text:
        return elem.text.strip()
    return ""


def _buscar_com_namespace(root: ET.Element, tag: str, ns: str) -> Optional[ET.Element]:
    """Busca uma tag considerando o namespace ou sem namespace."""
    # Tenta com namespace
    elem = root.find(f".//{{{ns}}}{tag}")
    if elem is not None:
        return elem
    
    # Tenta sem namespace
    elem = root.find(f".//{tag}")
    return elem


def _extrair_chave_acesso(root: ET.Element, ns: str) -> str:
    """Extrai a chave de acesso do protocolo ou da infNFe/infCte."""
    # Tenta buscar no protocolo de autorização
    for tag in ["protNFe", "protCTe"]:
        prot = _buscar_com_namespace(root, tag, ns)
        if prot is not None:
            ch = _buscar_com_namespace(prot, "chNFe", ns) or _buscar_com_namespace(prot, "chCTe", ns)
            if ch is not None and ch.text:
                return ch.text.strip()
    
    # Tenta buscar no atributo Id da infNFe/infCte
    for tag in ["infNFe", "infCte"]:
        inf = _buscar_com_namespace(root, tag, ns)
        if inf is not None:
            id_attr = inf.get("Id", "")
            if id_attr.startswith("NFe") or id_attr.startswith("CTe"):
                return id_attr[3:]  # Remove prefixo "NFe" ou "CTe"
    
    return ""


def _formatar_chave(chave: str) -> str:
    """Formata a chave de acesso em grupos de 4 dígitos."""
    chave = chave.replace(" ", "")
    if len(chave) == 44:
        return " ".join(chave[i:i+4] for i in range(0, 44, 4))
    return chave


def _formatar_valor(valor: str) -> str:
    """Formata valor numérico para moeda brasileira."""
    try:
        v = float(valor)
        inteiro = int(v)
        decimal = int(round((v - inteiro) * 100))
        inteiro_fmt = f"{inteiro:,}".replace(",", ".")
        return f"R$ {inteiro_fmt},{decimal:02d}"
    except (ValueError, TypeError):
        return valor if valor else ""


def _detectar_e_extrair_nfe(root: ET.Element) -> Optional[DocInfo]:
    """Tenta detectar e extrair dados de NFe/NFCe."""
    ns = NS_NFE
    
    # Verifica se é NFe/NFCe
    inf_nfe = _buscar_com_namespace(root, "infNFe", ns)
    if inf_nfe is None:
        return None
    
    # Detecta modelo (55 = NFe, 65 = NFCe)
    mod_elem = _buscar_com_namespace(root, "mod", ns)
    modelo = mod_elem.text.strip() if mod_elem is not None and mod_elem.text else "55"
    
    tipo = DocType.NFCE if modelo == "65" else DocType.NFE
    
    # Extrai metadados
    chave = _extrair_chave_acesso(root, ns)
    
    # Emitente
    emit = _buscar_com_namespace(root, "emit", ns)
    emitente = ""
    if emit is not None:
        x_nome = _buscar_com_namespace(emit, "xNome", ns)
        emitente = x_nome.text.strip() if x_nome is not None and x_nome.text else ""
    
    # Destinatário
    dest = _buscar_com_namespace(root, "dest", ns)
    destinatario = ""
    if dest is not None:
        x_nome = _buscar_com_namespace(dest, "xNome", ns)
        destinatario = x_nome.text.strip() if x_nome is not None and x_nome.text else ""
    
    # Valor total
    v_nf = _buscar_com_namespace(root, "vNF", ns)
    valor_total = v_nf.text.strip() if v_nf is not None and v_nf.text else ""
    
    # Natureza da operação
    nat_op = _buscar_com_namespace(root, "natOp", ns)
    natureza = nat_op.text.strip() if nat_op is not None and nat_op.text else ""
    
    # Data de emissão
    dh_emi = _buscar_com_namespace(root, "dhEmi", ns)
    data = ""
    if dh_emi is not None and dh_emi.text:
        data = dh_emi.text.strip()[:10]  # Pega apenas YYYY-MM-DD
        # Converte para DD/MM/YYYY
        if len(data) == 10 and "-" in data:
            partes = data.split("-")
            data = f"{partes[2]}/{partes[1]}/{partes[0]}"
    
    # Número da nota
    n_nf = _buscar_com_namespace(root, "nNF", ns)
    numero = n_nf.text.strip() if n_nf is not None and n_nf.text else ""
    
    return DocInfo(
        tipo=tipo,
        chave_acesso=_formatar_chave(chave),
        emitente=emitente,
        destinatario=destinatario,
        valor_total=_formatar_valor(valor_total),
        data_emissao=data,
        natureza_operacao=natureza,
        numero=numero,
    )


def _detectar_e_extrair_cte(root: ET.Element) -> Optional[DocInfo]:
    """Tenta detectar e extrair dados de CTe."""
    ns = NS_CTE
    
    # Verifica se é CTe
    inf_cte = _buscar_com_namespace(root, "infCte", ns)
    if inf_cte is None:
        return None
    
    # Extrai metadados
    chave = _extrair_chave_acesso(root, ns)
    
    # Emitente
    emit = _buscar_com_namespace(root, "emit", ns)
    emitente = ""
    if emit is not None:
        x_nome = _buscar_com_namespace(emit, "xNome", ns)
        emitente = x_nome.text.strip() if x_nome is not None and x_nome.text else ""
    
    # Destinatário (no CTe pode ser "dest" ou "receb")
    dest = _buscar_com_namespace(root, "dest", ns)
    destinatario = ""
    if dest is not None:
        x_nome = _buscar_com_namespace(dest, "xNome", ns)
        destinatario = x_nome.text.strip() if x_nome is not None and x_nome.text else ""
    
    # Valor total do frete
    v_rec = _buscar_com_namespace(root, "vRec", ns)
    valor_total = v_rec.text.strip() if v_rec is not None and v_rec.text else ""
    if not valor_total:
        v_tprest = _buscar_com_namespace(root, "vTPrest", ns)
        valor_total = v_tprest.text.strip() if v_tprest is not None and v_tprest.text else ""
    
    # Natureza da operação
    nat_op = _buscar_com_namespace(root, "natOp", ns)
    natureza = nat_op.text.strip() if nat_op is not None and nat_op.text else ""
    
    # Data de emissão
    dh_emi = _buscar_com_namespace(root, "dhEmi", ns)
    data = ""
    if dh_emi is not None and dh_emi.text:
        data = dh_emi.text.strip()[:10]
        if len(data) == 10 and "-" in data:
            partes = data.split("-")
            data = f"{partes[2]}/{partes[1]}/{partes[0]}"
    
    # Número do CTe
    n_ct = _buscar_com_namespace(root, "nCT", ns)
    numero = n_ct.text.strip() if n_ct is not None and n_ct.text else ""
    
    return DocInfo(
        tipo=DocType.CTE,
        chave_acesso=_formatar_chave(chave),
        emitente=emitente,
        destinatario=destinatario,
        valor_total=_formatar_valor(valor_total),
        data_emissao=data,
        natureza_operacao=natureza,
        numero=numero,
    )


def identificar(xml_content: str) -> DocInfo:
    """
    Identifica o tipo de documento fiscal e extrai metadados do XML.
    
    Args:
        xml_content: Conteúdo do arquivo XML como string.
    
    Returns:
        DocInfo com tipo e metadados extraídos.
    
    Raises:
        ValueError: Se o XML não puder ser interpretado ou não for um DFe válido.
    """
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as e:
        raise ValueError(f"XML inválido: {e}")
    
    # Tenta CTe primeiro (para não confundir com NFe)
    info = _detectar_e_extrair_cte(root)
    if info is not None:
        return info
    
    # Tenta NFe/NFCe
    info = _detectar_e_extrair_nfe(root)
    if info is not None:
        return info
    
    raise ValueError(
        "Documento não reconhecido. O XML não parece ser uma NFe, NFCe ou CTe válida."
    )
