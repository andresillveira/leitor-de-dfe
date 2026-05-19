# Especificação de Requisitos: Visualizador Leve de Documentos Fiscais Eletrônicos (NFe, NFCe, CTe)

## 1. Visão Geral do Projeto
O objetivo deste projeto é desenvolver um utilitário de software estritamente offline e de baixíssimo consumo de recursos (CPU/RAM) para visualização de arquivos XML de documentos fiscais eletrônicos brasileiros. O sistema deve receber um arquivo `.xml`, interpretar sua estrutura e renderizar visualmente os dados no formato tradicional do DANFE (para NFe/NFCe) ou DACTE (para CTe).

**O problema a ser resolvido:** Soluções de mercado (como o DANFE View) são pesadas, consomem muitos recursos em ambientes de servidor e possuem funções desnecessárias que degradam a performance. 

## 2. Premissas e Restrições Absolutas (Gatilhos de Exclusão)
A IA encarregada do desenvolvimento deve seguir estas regras rigorosamente:
- **100% Offline:** O software NÃO PODE fazer NENHUMA requisição de rede. 
- **Sem SEFAZ:** Proibido implementar consultas de status na SEFAZ.
- **Sem Validação Criptográfica:** Proibido implementar verificação de assinatura digital (RSA/Certificado Digital). O XML deve ser lido "as is" (como está).
- **Sem Validação de Schema (XSD):** O foco é extração de dados. O sistema deve ser tolerante a falhas estruturais menores, contanto que as tags principais estejam acessíveis.
- **Leveza:** Evitar frameworks pesados (ex: Electron). Priorizar renderização via HTML/CSS estático ou bibliotecas GUI nativas/leves.

## 3. Requisitos Funcionais

### 3.1. Identificação do Tipo de Documento
Ao abrir um arquivo XML, o sistema deve ler a raiz e identificar automaticamente o modelo do documento fiscal:
- **NFe (Modelo 55):** Identificado pelas tags `<nfeProc>` / `<NFe>` / `<infNFe>`.
- **NFCe (Modelo 65):** Identificado pelas tags da NFe, porém com a tag `<mod>` igual a `65`.
- **CTe (Modelo 57):** Identificado pelas tags `<cteProc>` / `<CTe>` / `<infCte>`.

### 3.2. Extração de Dados (Parsing)
O motor de extração deve buscar os dados utilizando XPath ou bibliotecas de parsing XML eficientes. Dados essenciais incluem:
- **Cabeçalho:** Chave de Acesso, Natureza da Operação, Protocolo de Autorização, Data/Hora de Emissão.
- **Entidades:** Emitente, Destinatário, Transportadora (Razão Social, CNPJ/CPF, IE, Endereço completo).
- **Itens (Produtos/Serviços):** Código, Descrição, NCM, CFOP, Unidade, Quantidade, Valor Unitário, Valor Total. Para CTe, extrair os dados da carga e componentes do frete.
- **Impostos e Totais:** Base de Cálculo de ICMS, Valor do ICMS, Valor Total dos Produtos, Valor Total da Nota/Frete.
- **Informações Adicionais:** Dados Adicionais/Observações do Fisco e do Contribuinte.

### 3.3. Renderização Visual (DANFE / DACTE)
- Gerar uma representação visual que imite a disposição gráfica padrão instituída pelo manual do contribuinte.
- O código de barras (Code 128C) correspondente à Chave de Acesso deve ser gerado localmente e renderizado na tela.
- **Impressão/Exportação:** A interface deve permitir a impressão nativa ou salvamento em PDF (tudo gerado localmente).

## 4. Requisitos Não Funcionais e Arquitetura
- **Performance:** A abertura do arquivo e a renderização devem ocorrer em menos de 1 segundo.
- **Tolerância a Erros:** Caso o XML seja inválido ou falte uma tag não-crítica, o sistema deve renderizar o que for possível ou exibir uma mensagem de erro clara e rápida, sem "crashar".
- **Interface Gráfica (UI):** Deve ser minimalista. O usuário arrasta o arquivo para a janela ou seleciona via menu, e o documento é renderizado imediatamente.

## 5. Sugestão de Abordagem Técnica
*Nota para a IA: Escolher a abordagem que garanta menor consumo de memória.*
- **Backend/Parser:** Python puro com `xml.etree.ElementTree` ou `lxml` (rápido e nativo/leve).
- **Motor Visualização:** 
  - *Opção A:* Conversão do XML para um template HTML estático (Jinja2) e abertura no navegador padrão do sistema operacional. (Mais leve, ideal para servidores).
  - *Opção B:* GUI leve em Python (PyQt ou Tkinter) com um componente de visualização.
- **Gerador de Código de Barras:** Biblioteca local leve (ex: `python-barcode`).