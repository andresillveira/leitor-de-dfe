# 📄 Leitor de DFe — Visualizador de Documentos Fiscais Eletrônicos

![Versão](https://img.shields.io/badge/vers%C3%A3o-1.1.0-blue)

Utilitário desktop **100% offline** e leve para visualizar e exportar DANFE/DACTE a partir de arquivos XML de NFe, NFCe e CTe.

## ✨ Funcionalidades

- **Identificação automática** do tipo de documento (NFe, NFCe, CTe)
- **Geração de DANFE/DACTE** em PDF com layout oficial
- **Código de barras Code128** gerado localmente
- **Drag & Drop** — arraste o XML direto para a janela
- **Visualização** no leitor de PDF padrão do sistema
- **Salvar como** — escolha onde salvar o PDF gerado
- **Cache inteligente** — PDFs já gerados são reutilizados
- **Menu de contexto do Windows** — clique direito em qualquer `.xml` → "Abrir DFe" *(novo na v1.1.0)*

## 📋 Requisitos

- Python 3.9 ou superior
- Windows 10/11

## 🚀 Como usar

### Opção 1 — Duplo clique
Execute o arquivo `iniciar.bat`. As dependências serão instaladas automaticamente na primeira execução.

### Opção 2 — Menu de contexto do Windows *(recomendado)*
1. Execute `instalar_menu.bat` **como administrador** (apenas uma vez)
2. Clique com o botão direito em qualquer arquivo `.xml`
3. Selecione **"📄 Abrir DFe"**
4. O programa abre com o documento já carregado

> **Nota (Windows 11):** A opção aparece dentro do submenu "Mostrar mais opções".

Para remover a integração, execute `desinstalar_menu.bat` como administrador.

### Opção 3 — Terminal
```bash
pip install -r requirements.txt
python src/main.py
```

Também é possível passar o caminho do XML diretamente:
```bash
python src/main.py "C:\caminho\para\nota.xml"
```

## 📦 Dependências

| Pacote | Função |
|--------|--------|
| `brazilfiscalreport` | Geração de DANFE/DACTE em PDF |
| `tkinterdnd2` | Drag & Drop na interface |
| `fpdf2` | Motor de PDF (sub-dependência) |
| `python-barcode` | Código de barras Code128 (sub-dependência) |
| `qrcode` | QR Code para CTe (sub-dependência) |

## 🏗️ Estrutura

```
leitor_de_dfe/
├── IDEA.MD                # Especificação original
├── README.md              # Este arquivo
├── requirements.txt       # Dependências pip
├── iniciar.bat            # Launcher para Windows
├── instalar_menu.bat      # Instala menu de contexto (admin)
├── desinstalar_menu.bat   # Remove menu de contexto (admin)
└── src/
    ├── main.py            # Interface gráfica (Tkinter)
    ├── viewer.py          # Geração e abertura de PDF
    ├── detector.py        # Identificação do tipo de documento
    └── instalar_menu.py   # Gerenciador do registro do Windows
```

## ⚠️ Restrições por design

- **Zero conexão de rede** — nenhuma requisição é feita
- **Sem consulta SEFAZ** — leitura "as is" do XML
- **Sem validação criptográfica** — assinaturas digitais são ignoradas
- **Sem validação XSD** — tolerante a XMLs com pequenas falhas estruturais
