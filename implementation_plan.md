# Visualizador Leve de DFe — Plano de Implementação

Utilitário desktop 100% offline para visualizar e exportar DANFE/DACTE a partir de arquivos XML de NFe, NFCe e CTe.

## Contexto

O `IDEA.MD` especifica um software que substitua soluções pesadas (como DANFE View) por um utilitário mínimo: abrir XML → identificar tipo → renderizar visualmente → permitir impressão/PDF. Restrições absolutas: **zero rede, zero SEFAZ, zero validação criptográfica/XSD**.

---

## Decisões de Arquitetura

### Motor de Renderização: `brazilfiscalreport`

> [!IMPORTANT]
> A pesquisa revelou a biblioteca **[BrazilFiscalReport](https://github.com/Engenere/BrazilFiscalReport)** (v0.7.3, LGPL-3.0) — ela já resolve 90% do problema:
> - Gera DANFE e DACTE em PDF a partir de XML puro
> - Usa `fpdf2` (levíssimo) como motor — **sem Electron, sem navegador**
> - Gera código de barras Code128 via `python-barcode` embutido
> - Gera QR Code para CTe via `qrcode`
> - **100% offline**, sem nenhuma chamada de rede

Isso elimina a necessidade de implementar manualmente o parsing de XML, o layout do DANFE/DACTE, e a geração de código de barras. O foco do projeto passa a ser **a interface gráfica e a experiência do usuário**.

### GUI: Tkinter + `tkinterdnd2`

| Critério | Tkinter | PyQt | Electron |
|---|---|---|---|
| Peso em memória | ~15 MB | ~80 MB | ~200+ MB |
| Dependência externa | Nenhuma (stdlib) | pip install | Node + Chromium |
| Drag & Drop nativo | Via `tkinterdnd2` | Nativo | Nativo |
| Startup time | < 0.3s | ~1s | ~3s |

**Escolha: Tkinter** — já incluso no Python, consome mínima memória e abre instantaneamente.
`tkinterdnd2` adiciona drag-and-drop de arquivos (~50 KB extra).

### Visualizador de PDF integrado

Para exibir o PDF gerado dentro da própria janela (sem abrir um leitor externo), temos duas opções:

- **Opção A — Abrir no leitor padrão do SO:** `os.startfile()` (Windows) abre o PDF no leitor padrão. Ultra leve, zero dependências extras.
- **Opção B — Preview embutido na GUI:** Converter primeira página do PDF em imagem com `PyMuPDF (fitz)` e exibir no canvas do Tkinter.

> [!NOTE]
> Recomendo a **Opção A como padrão** (abrir no leitor de PDF do sistema) com **Opção B como melhoria futura**. Isso mantém o MVP enxuto.

---

## Estrutura do Projeto

```
d:\leitor_de_dfe\
├── IDEA.MD                    # Especificação original
├── README.md                  # [NEW] Documentação do projeto
├── requirements.txt           # [NEW] Dependências pip
├── iniciar.bat                # [NEW] Script para rodar com duplo-clique
│
├── src/
│   ├── __init__.py
│   ├── main.py                # [NEW] Ponto de entrada — GUI Tkinter
│   ├── viewer.py              # [NEW] Lógica de renderização (brazilfiscalreport)
│   ├── detector.py            # [NEW] Identificação do tipo de documento (NFe/NFCe/CTe)
│   └── utils.py               # [NEW] Utilitários (temp files, formatação)
│
└── assets/
    └── icon.ico               # [NEW] Ícone da aplicação
```

---

## Proposed Changes

### Componente 1 — Detector de Tipo de Documento

#### [NEW] [detector.py](file:///d:/leitor_de_dfe/src/detector.py)

Módulo responsável por ler a tag raiz do XML e classificar o documento:

- Usa `xml.etree.ElementTree` (stdlib) para parsing rápido
- Detecta o tipo verificando tags na seguinte ordem:
  1. `<cteProc>` / `<CTe>` / `<infCte>` → **CTe (Modelo 57)**
  2. `<nfeProc>` / `<NFe>` / `<infNFe>` com `<mod>65` → **NFCe (Modelo 65)**
  3. `<nfeProc>` / `<NFe>` / `<infNFe>` com `<mod>55` → **NFe (Modelo 55)**
- Retorna enum `DocType.NFE | DocType.NFCE | DocType.CTE`
- Trata XMLs mal-formados com `try/except` e mensagem amigável
- Extrai também metadados básicos para preview (chave de acesso, emitente, valor total)

---

### Componente 2 — Motor de Visualização

#### [NEW] [viewer.py](file:///d:/leitor_de_dfe/src/viewer.py)

Orquestra a geração do PDF a partir do XML usando `brazilfiscalreport`:

```python
# Lógica central simplificada:
def gerar_pdf(xml_path: str, output_path: str) -> str:
    xml_content = Path(xml_path).read_text(encoding="utf-8")
    doc_type = detector.identificar(xml_content)
    
    if doc_type in (DocType.NFE, DocType.NFCE):
        doc = Danfe(xml=xml_content)
    elif doc_type == DocType.CTE:
        doc = Dacte(xml=xml_content)
    
    doc.output(output_path)
    return output_path
```

- O PDF é salvo em `%TEMP%\leitor_dfe\` com nome baseado na chave de acesso
- Cache: se o PDF já existe para aquela chave, reutiliza sem re-gerar
- Função `abrir_pdf()` usa `os.startfile()` para abrir no leitor padrão
- Função `salvar_como()` permite o usuário escolher onde salvar via `filedialog.asksaveasfilename()`

---

### Componente 3 — Interface Gráfica (GUI)

#### [NEW] [main.py](file:///d:/leitor_de_dfe/src/main.py)

Interface Tkinter minimalista com as seguintes áreas:

```
┌──────────────────────────────────────────────┐
│  📄 Leitor de DFe              [─] [□] [✕]  │
├──────────────────────────────────────────────┤
│                                              │
│   ┌──────────────────────────────────────┐   │
│   │                                      │   │
│   │    🔽 Arraste o arquivo XML aqui     │   │
│   │       ou clique para selecionar      │   │
│   │                                      │   │
│   └──────────────────────────────────────┘   │
│                                              │
│  ┌─ Informações do Documento ─────────────┐  │
│  │ Tipo:    NFe (Modelo 55)               │  │
│  │ Chave:   3525 0512 3456 7890 ...       │  │
│  │ Emitente: EMPRESA LTDA                 │  │
│  │ Valor:   R$ 1.234,56                   │  │
│  └────────────────────────────────────────┘  │
│                                              │
│  [ 👁 Visualizar PDF ]   [ 💾 Salvar PDF ]   │
│                                              │
│  Status: Pronto                              │
└──────────────────────────────────────────────┘
```

**Funcionalidades da GUI:**
- **Drag & Drop:** Área central aceita arrastar XMLs (via `tkinterdnd2`)
- **Seleção por clique:** Clicar na área abre `filedialog.askopenfilename()` filtrado para `*.xml`
- **Preview de info:** Após carregar, exibe metadados extraídos pelo `detector.py`
- **Botão "Visualizar":** Gera o PDF e abre no leitor padrão do sistema
- **Botão "Salvar":** Gera o PDF e abre diálogo "Salvar como..."
- **Barra de status:** Feedback ("Carregando...", "PDF gerado com sucesso", "Erro: XML inválido")
- **Processamento em lote:** Aceitar múltiplos XMLs arrastados, gerando um PDF para cada

**Estilo visual:**
- Paleta escura moderna (fundo `#1e1e2e`, texto `#cdd6f4`, acentos `#89b4fa`)
- Bordas arredondadas na zona de drop
- Ícone animado de loading durante geração
- Janela dimensionada em `600x450`, centrável

---

### Componente 4 — Scripts de Suporte

#### [NEW] [requirements.txt](file:///d:/leitor_de_dfe/requirements.txt)

```
brazilfiscalreport[dacte]>=0.7.3
tkinterdnd2>=0.4.2
```

> [!NOTE]
> Total de dependências pip: apenas **2 pacotes diretos**. As sub-dependências (`fpdf2`, `python-barcode`, `qrcode`, `phonenumbers`) são automaticamente instaladas e são todas leves e pure-Python.

#### [NEW] [iniciar.bat](file:///d:/leitor_de_dfe/iniciar.bat)

Script batch para o usuário final executar com duplo-clique:

```batch
@echo off
cd /d "%~dp0"
pip install -r requirements.txt --quiet 2>nul
python src/main.py
```

#### [NEW] [README.md](file:///d:/leitor_de_dfe/README.md)

Documentação com:
- Descrição do projeto
- Requisitos (Python 3.9+)
- Instruções de instalação e uso
- Screenshots da interface

---

## Fases de Execução

| Fase | Descrição | Estimativa |
|------|-----------|------------|
| **1** | Setup do projeto (`requirements.txt`, estrutura de pastas, `iniciar.bat`) | 5 min |
| **2** | `detector.py` — Identificação automática de NFe/NFCe/CTe | 10 min |
| **3** | `viewer.py` — Integração com `brazilfiscalreport`, geração de PDF | 10 min |
| **4** | `main.py` — GUI Tkinter completa com drag-and-drop, preview e botões | 25 min |
| **5** | Testes end-to-end e polimento visual | 10 min |

---

## User Review Required

> [!IMPORTANT]
> **Visualização do PDF:** O plano assume abrir o PDF no leitor padrão do Windows (Adobe Reader, Edge, etc.) via `os.startfile()`. Deseja um preview embutido dentro da própria janela? Isso adicionaria a dependência `PyMuPDF` (~30 MB).

> [!IMPORTANT]
> **Processamento em lote:** Deseja a funcionalidade de arrastar uma **pasta inteira** de XMLs e gerar todos os PDFs de uma vez? Ou apenas arquivo por arquivo é suficiente?

---

## Open Questions

1. **NFCe:** O layout da NFCe (cupom fiscal) é diferente do DANFE padrão. A `brazilfiscalreport` trata a NFCe como DANFE. Deseja um layout de cupom fiscal específico para NFCe (modelo 65)?

2. **Empacotamento (`.exe`):** Para distribuir a ferramenta sem exigir Python instalado, posso empacotar com `PyInstaller` como etapa final. Isso é desejável?

---

## Verification Plan

### Automated Tests
1. `python -m pytest` com XMLs de teste para cada tipo (NFe, NFCe, CTe)
2. Validar que o detector identifica corretamente os 3 tipos
3. Validar que o PDF é gerado sem erros para cada tipo

### Manual Verification
1. Executar `iniciar.bat` e validar que a GUI abre em < 1 segundo
2. Arrastar um XML de NFe e verificar geração do DANFE em PDF
3. Arrastar um XML de CTe e verificar geração do DACTE em PDF
4. Testar com um XML malformado e verificar mensagem de erro amigável
5. Verificar consumo de memória (meta: < 50 MB em uso)
