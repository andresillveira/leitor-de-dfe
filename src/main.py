"""
main.py — Interface gráfica do Leitor de DFe.

GUI Tkinter minimalista com drag-and-drop para visualização
de documentos fiscais eletrônicos (NFe, NFCe, CTe).
"""

import sys
import os
import threading
from pathlib import Path
from tkinter import filedialog, messagebox
import tkinter as tk

# Adiciona o diretório src ao path
sys.path.insert(0, str(Path(__file__).parent))

# Tenta importar tkinterdnd2 para drag-and-drop
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except ImportError:
    HAS_DND = False

from detector import DocInfo
import viewer

__version__ = "1.1.0"


# ──────────────────────────────────────────────
# Paleta de cores (tema escuro moderno)
# ──────────────────────────────────────────────
COLORS = {
    "bg":           "#1e1e2e",
    "bg_secondary": "#181825",
    "surface":      "#313244",
    "surface_hover":"#45475a",
    "border":       "#585b70",
    "text":         "#cdd6f4",
    "text_dim":     "#a6adc8",
    "text_muted":   "#6c7086",
    "accent":       "#89b4fa",
    "accent_hover": "#74c7ec",
    "green":        "#a6e3a1",
    "red":          "#f38ba8",
    "yellow":       "#f9e2af",
    "lavender":     "#b4befe",
}

FONT_FAMILY = "Segoe UI"
FONT_TITLE = (FONT_FAMILY, 14, "bold")
FONT_NORMAL = (FONT_FAMILY, 10)
FONT_SMALL = (FONT_FAMILY, 9)
FONT_LABEL = (FONT_FAMILY, 9, "bold")
FONT_VALUE = (FONT_FAMILY, 10)
FONT_DROP = (FONT_FAMILY, 12)
FONT_BTN = (FONT_FAMILY, 10, "bold")


class LeitorDFeApp:
    """Aplicação principal do Leitor de DFe."""

    def __init__(self):
        # Cria janela principal
        if HAS_DND:
            self.root = TkinterDnD.Tk()
        else:
            self.root = tk.Tk()

        self.root.title(f"Leitor de DFe - v{__version__}")
        self.root.configure(bg=COLORS["bg"])
        self.root.resizable(False, False)

        # Dimensões da janela
        width, height = 580, 520
        self.root.geometry(f"{width}x{height}")

        # Centraliza na tela
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"+{x}+{y}")

        # Tenta definir ícone
        icon_path = Path(__file__).parent.parent / "assets" / "icon.ico"
        if icon_path.exists():
            self.root.iconbitmap(str(icon_path))

        # Estado
        self.current_doc_info: DocInfo | None = None
        self.current_pdf_path: str | None = None
        self.is_processing = False

        # Constrói a interface
        self._build_ui()

    def _build_ui(self):
        """Constrói todos os widgets da interface."""
        main_frame = tk.Frame(self.root, bg=COLORS["bg"])
        main_frame.pack(fill="both", expand=True, padx=20, pady=15)

        # ── Título ──
        title_frame = tk.Frame(main_frame, bg=COLORS["bg"])
        title_frame.pack(fill="x", pady=(0, 12))

        tk.Label(
            title_frame,
            text="📄  Leitor de DFe",
            font=FONT_TITLE,
            fg=COLORS["accent"],
            bg=COLORS["bg"],
        ).pack(side="left")

        tk.Label(
            title_frame,
            text="NFe  ·  NFCe  ·  CTe",
            font=FONT_SMALL,
            fg=COLORS["text_muted"],
            bg=COLORS["bg"],
        ).pack(side="right", pady=(4, 0))

        # ── Zona de Drop ──
        self.drop_frame = tk.Frame(
            main_frame,
            bg=COLORS["surface"],
            highlightbackground=COLORS["border"],
            highlightthickness=2,
            cursor="hand2",
        )
        self.drop_frame.pack(fill="x", ipady=28, pady=(0, 12))

        self.drop_icon_label = tk.Label(
            self.drop_frame,
            text="⬇",
            font=(FONT_FAMILY, 28),
            fg=COLORS["accent"],
            bg=COLORS["surface"],
        )
        self.drop_icon_label.pack(pady=(8, 2))

        self.drop_text_label = tk.Label(
            self.drop_frame,
            text="Arraste o arquivo XML aqui",
            font=FONT_DROP,
            fg=COLORS["text"],
            bg=COLORS["surface"],
        )
        self.drop_text_label.pack()

        self.drop_hint_label = tk.Label(
            self.drop_frame,
            text="ou clique para selecionar",
            font=FONT_SMALL,
            fg=COLORS["text_muted"],
            bg=COLORS["surface"],
        )
        self.drop_hint_label.pack(pady=(0, 5))

        # Eventos de clique na zona de drop
        for widget in (self.drop_frame, self.drop_icon_label,
                       self.drop_text_label, self.drop_hint_label):
            widget.bind("<Button-1>", self._on_click_select)
            widget.bind("<Enter>", self._on_drop_hover_enter)
            widget.bind("<Leave>", self._on_drop_hover_leave)

        # Registra drag-and-drop
        if HAS_DND:
            self.drop_frame.drop_target_register(DND_FILES)
            self.drop_frame.dnd_bind("<<Drop>>", self._on_file_drop)

        # ── Painel de informações ──
        self.info_frame = tk.LabelFrame(
            main_frame,
            text="  Informações do Documento  ",
            font=FONT_LABEL,
            fg=COLORS["text_dim"],
            bg=COLORS["bg_secondary"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
            bd=0,
            padx=15,
            pady=10,
        )
        self.info_frame.pack(fill="x", pady=(0, 12))

        # Grid de informações
        self.info_labels = {}
        info_fields = [
            ("Tipo", "tipo"),
            ("Número", "numero"),
            ("Chave", "chave"),
            ("Emitente", "emitente"),
            ("Destinatário", "dest"),
            ("Valor Total", "valor"),
            ("Data Emissão", "data"),
        ]

        for i, (label_text, key) in enumerate(info_fields):
            lbl = tk.Label(
                self.info_frame,
                text=f"{label_text}:",
                font=FONT_LABEL,
                fg=COLORS["text_muted"],
                bg=COLORS["bg_secondary"],
                anchor="w",
            )
            lbl.grid(row=i, column=0, sticky="w", padx=(0, 10), pady=1)

            val = tk.Label(
                self.info_frame,
                text="—",
                font=FONT_VALUE,
                fg=COLORS["text_dim"],
                bg=COLORS["bg_secondary"],
                anchor="w",
            )
            val.grid(row=i, column=1, sticky="w", pady=1)

            self.info_labels[key] = val

        self.info_frame.columnconfigure(1, weight=1)

        # ── Botões ──
        btn_frame = tk.Frame(main_frame, bg=COLORS["bg"])
        btn_frame.pack(fill="x", pady=(0, 10))

        self.btn_visualizar = tk.Button(
            btn_frame,
            text="👁  Visualizar PDF",
            font=FONT_BTN,
            fg=COLORS["bg"],
            bg=COLORS["accent"],
            activebackground=COLORS["accent_hover"],
            activeforeground=COLORS["bg"],
            relief="flat",
            cursor="hand2",
            padx=20,
            pady=8,
            state="disabled",
            command=self._on_visualizar,
        )
        self.btn_visualizar.pack(side="left", expand=True, fill="x", padx=(0, 5))

        self.btn_salvar = tk.Button(
            btn_frame,
            text="💾  Salvar PDF",
            font=FONT_BTN,
            fg=COLORS["text"],
            bg=COLORS["surface"],
            activebackground=COLORS["surface_hover"],
            activeforeground=COLORS["text"],
            relief="flat",
            cursor="hand2",
            padx=20,
            pady=8,
            state="disabled",
            command=self._on_salvar,
        )
        self.btn_salvar.pack(side="right", expand=True, fill="x", padx=(5, 0))

        # ── Barra de Status ──
        status_frame = tk.Frame(main_frame, bg=COLORS["bg_secondary"], height=30)
        status_frame.pack(fill="x", side="bottom")
        status_frame.pack_propagate(False)

        self.status_label = tk.Label(
            status_frame,
            text="Pronto — Aguardando arquivo XML",
            font=FONT_SMALL,
            fg=COLORS["text_muted"],
            bg=COLORS["bg_secondary"],
            anchor="w",
            padx=10,
        )
        self.status_label.pack(fill="both", expand=True)

    # ──────────────────────────────────────────
    # Eventos
    # ──────────────────────────────────────────

    def _on_drop_hover_enter(self, event=None):
        """Hover visual na zona de drop."""
        if not self.is_processing:
            self.drop_frame.configure(highlightbackground=COLORS["accent"])

    def _on_drop_hover_leave(self, event=None):
        """Remove hover visual."""
        self.drop_frame.configure(highlightbackground=COLORS["border"])

    def _on_click_select(self, event=None):
        """Abre diálogo para selecionar arquivo XML."""
        if self.is_processing:
            return

        file_path = filedialog.askopenfilename(
            title="Selecionar arquivo XML",
            filetypes=[
                ("Arquivos XML", "*.xml"),
                ("Todos os arquivos", "*.*"),
            ],
        )
        if file_path:
            self._processar_arquivo(file_path)

    def _on_file_drop(self, event):
        """Processa arquivo arrastado para a zona de drop."""
        if self.is_processing:
            return

        # tkinterdnd2 retorna caminhos entre chaves se houver espaços
        file_path = event.data.strip()
        if file_path.startswith("{") and file_path.endswith("}"):
            file_path = file_path[1:-1]

        # Se múltiplos arquivos forem arrastados, usa apenas o primeiro
        if " " in file_path and not os.path.exists(file_path):
            # Pode ser múltiplos arquivos separados por espaço
            file_path = file_path.split()[0]
            if file_path.startswith("{"):
                file_path = file_path[1:]

        self._processar_arquivo(file_path)

    def _on_visualizar(self):
        """Abre o PDF no leitor padrão do sistema."""
        if self.current_pdf_path:
            try:
                viewer.abrir_pdf(self.current_pdf_path)
                self._set_status("PDF aberto no leitor padrão", "green")
            except Exception as e:
                self._set_status(f"Erro ao abrir PDF: {e}", "red")

    def _on_salvar(self):
        """Salva o PDF no local escolhido pelo usuário."""
        if not self.current_pdf_path or not self.current_doc_info:
            return

        # Sugere nome baseado no tipo e número
        chave = self.current_doc_info.chave_acesso.replace(" ", "")
        tipo = self.current_doc_info.tipo.name
        default_name = f"{tipo}_{chave}.pdf" if chave else f"{tipo}_documento.pdf"

        destino = filedialog.asksaveasfilename(
            title="Salvar PDF como",
            defaultextension=".pdf",
            initialfile=default_name,
            filetypes=[("Arquivo PDF", "*.pdf")],
        )
        if destino:
            try:
                viewer.salvar_pdf_como(self.current_pdf_path, destino)
                self._set_status(f"PDF salvo em: {Path(destino).name}", "green")
            except Exception as e:
                self._set_status(f"Erro ao salvar: {e}", "red")

    # ──────────────────────────────────────────
    # Processamento
    # ──────────────────────────────────────────

    def _processar_arquivo(self, xml_path: str):
        """Inicia o processamento do arquivo XML em uma thread separada."""
        if self.is_processing:
            return

        self.is_processing = True
        self._set_status("Processando XML...", "yellow")
        self._desabilitar_controles()

        # Processa em thread separada para não travar a GUI
        thread = threading.Thread(
            target=self._processar_worker,
            args=(xml_path,),
            daemon=True,
        )
        thread.start()

    def _processar_worker(self, xml_path: str):
        """Worker thread para processar o XML e gerar PDF."""
        try:
            doc_info, pdf_path = viewer.processar_xml(xml_path)
            # Atualiza a GUI na thread principal
            self.root.after(0, self._on_processamento_sucesso, doc_info, pdf_path)
        except (FileNotFoundError, ValueError, RuntimeError) as e:
            self.root.after(0, self._on_processamento_erro, str(e))
        except Exception as e:
            self.root.after(0, self._on_processamento_erro, f"Erro inesperado: {e}")

    def _on_processamento_sucesso(self, doc_info: DocInfo, pdf_path: str):
        """Callback após processamento bem-sucedido."""
        self.current_doc_info = doc_info
        self.current_pdf_path = pdf_path
        self.is_processing = False

        # Atualiza informações
        self._atualizar_info(doc_info)
        self._habilitar_controles()
        self._set_status("✓ PDF gerado com sucesso!", "green")

        # Atualiza visual da zona de drop
        self.drop_icon_label.configure(text="✓", fg=COLORS["green"])
        self.drop_text_label.configure(text="Documento carregado")
        self.drop_hint_label.configure(text="Arraste outro XML para substituir")

    def _on_processamento_erro(self, mensagem: str):
        """Callback após erro no processamento."""
        self.is_processing = False
        self._set_status(f"✗ {mensagem}", "red")
        self._resetar_info()

        # Visual de erro na zona de drop
        self.drop_icon_label.configure(text="✗", fg=COLORS["red"])
        self.drop_text_label.configure(text="Erro no processamento")
        self.drop_hint_label.configure(text="Tente outro arquivo XML")

        # Restaura após 3 segundos
        self.root.after(3000, self._resetar_drop_zone)

    # ──────────────────────────────────────────
    # Helpers da UI
    # ──────────────────────────────────────────

    def _set_status(self, text: str, color: str = "text_muted"):
        """Atualiza a barra de status."""
        fg = COLORS.get(color, color)
        self.status_label.configure(text=text, fg=fg)

    def _atualizar_info(self, info: DocInfo):
        """Preenche o painel de informações com os dados do documento."""
        # Cor do tipo de documento
        tipo_cores = {
            "NFe (Modelo 55)": COLORS["accent"],
            "NFCe (Modelo 65)": COLORS["lavender"],
            "CTe (Modelo 57)": COLORS["yellow"],
        }

        self.info_labels["tipo"].configure(
            text=info.tipo.value,
            fg=tipo_cores.get(info.tipo.value, COLORS["text"]),
        )
        self.info_labels["numero"].configure(
            text=info.numero or "—",
            fg=COLORS["text"],
        )
        self.info_labels["chave"].configure(
            text=info.chave_acesso or "—",
            fg=COLORS["text"],
        )
        self.info_labels["emitente"].configure(
            text=info.emitente or "—",
            fg=COLORS["text"],
        )
        self.info_labels["dest"].configure(
            text=info.destinatario or "—",
            fg=COLORS["text"],
        )
        self.info_labels["valor"].configure(
            text=info.valor_total or "—",
            fg=COLORS["green"] if info.valor_total else COLORS["text_dim"],
        )
        self.info_labels["data"].configure(
            text=info.data_emissao or "—",
            fg=COLORS["text"],
        )

    def _resetar_info(self):
        """Limpa o painel de informações."""
        for val_label in self.info_labels.values():
            val_label.configure(text="—", fg=COLORS["text_dim"])

    def _desabilitar_controles(self):
        """Desabilita botões durante processamento."""
        self.btn_visualizar.configure(state="disabled")
        self.btn_salvar.configure(state="disabled")

    def _habilitar_controles(self):
        """Habilita botões após processamento."""
        self.btn_visualizar.configure(state="normal")
        self.btn_salvar.configure(state="normal")

    def _resetar_drop_zone(self):
        """Restaura a zona de drop ao estado inicial."""
        self.drop_icon_label.configure(text="⬇", fg=COLORS["accent"])
        self.drop_text_label.configure(text="Arraste o arquivo XML aqui")
        self.drop_hint_label.configure(text="ou clique para selecionar")
        self._set_status("Pronto — Aguardando arquivo XML")

    def run(self, xml_path: str | None = None):
        """Inicia o loop principal da aplicação.

        Args:
            xml_path: Caminho opcional de um arquivo XML para processar
                      automaticamente ao iniciar (usado pelo menu de contexto).
        """
        if xml_path:
            # Agenda o processamento após a GUI estar pronta
            self.root.after(100, self._processar_arquivo, xml_path)
        self.root.mainloop()


def main():
    # Verifica se um arquivo XML foi passado via linha de comando
    # (ex: menu de contexto do Windows → "Abrir DFe")
    if len(sys.argv) > 1:
        candidato = sys.argv[1]
        if os.path.isfile(candidato):
            try:
                # Processamento direto em segundo plano (sem GUI)
                _, pdf_path = viewer.processar_xml(candidato)
                viewer.abrir_pdf(pdf_path)
                sys.exit(0)
            except Exception as e:
                # Caso ocorra erro, exibe messagebox e encerra
                root = tk.Tk()
                root.withdraw()
                icon_path = Path(__file__).parent.parent / "assets" / "icon.ico"
                if icon_path.exists():
                    try:
                        root.iconbitmap(str(icon_path))
                    except Exception:
                        pass
                messagebox.showerror(
                    "Erro ao Abrir DFe",
                    f"Falha ao abrir o documento fiscal:\n{e}"
                )
                sys.exit(1)

    # Fluxo normal: abre a interface gráfica
    app = LeitorDFeApp()
    app.run()


if __name__ == "__main__":
    main()
