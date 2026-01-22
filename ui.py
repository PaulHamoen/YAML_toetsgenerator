# ui.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from pathlib import Path

from core import (
    laad_yaml_string,
    valideer_toetsstructuur,
    render_document,
    genereer_pdf,
)

# (later) AI
# from ai.ollama import OllamaClient
# from ai.openai import OpenAIClient


class ToetsUI(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Toetsgenerator v0.2")
        self.geometry("1200x800")

        self._build_ui()

    # ======================
    # UI layout
    # ======================

    def _build_ui(self):
        main = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main.pack(fill=tk.BOTH, expand=True)

        # ========== LINKS: knoppen ==========
        left = ttk.Frame(main, width=200)
        main.add(left, weight=0)

        ttk.Button(left, text="Prompt AI → YAML", command=self.prompt_ai).pack(
            fill=tk.X, padx=10, pady=5
        )

        ttk.Separator(left).pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(left, text="Preview → LaTeX", command=self.preview).pack(
            fill=tk.X, padx=10, pady=5
        )

        ttk.Button(left, text="Genereer PDF", command=self.gen_pdf).pack(
            fill=tk.X, padx=10, pady=5
        )

        # ========== RECHTS: editors ==========
        right = ttk.PanedWindow(main, orient=tk.VERTICAL)
        main.add(right, weight=1)

        # YAML editor
        yaml_frame = ttk.LabelFrame(right, text="YAML (bron)")
        right.add(yaml_frame, weight=1)

        self.yaml_text = tk.Text(yaml_frame, wrap="none")
        self.yaml_text.pack(fill=tk.BOTH, expand=True)

        # LaTeX editor
        latex_frame = ttk.LabelFrame(right, text="LaTeX (bron voor PDF)")
        right.add(latex_frame, weight=1)

        self.latex_text = tk.Text(latex_frame, wrap="none")
        self.latex_text.pack(fill=tk.BOTH, expand=True)

    # ======================
    # Acties
    # ======================

    def prompt_ai(self):
        """
        (Voorlopig placeholder)
        Hier komt straks:
        - prompt ophalen
        - AI aanroepen
        - YAML terugzetten in editor
        """
        messagebox.showinfo(
            "AI",
            "AI-integratie volgt.\n\nDit vult straks de YAML-editor.",
        )

    def preview(self):
        """
        YAML → parse → validatie → LaTeX → tonen
        """
        yaml_text = self.yaml_text.get("1.0", tk.END)

        try:
            data = laad_yaml_string(yaml_text)

            if "toets" not in data:
                raise Exception("YAML mist hoofdsleutel: toets")

            toets = data["toets"]

            valideer_toetsstructuur(toets)

            template = self._load_template()

            latex = render_document(
                toets,
                template_text=template,
                titel="Toets",
                instructie="",
                se=False,
            )

            self.latex_text.delete("1.0", tk.END)
            self.latex_text.insert("1.0", latex)

        except Exception as e:
            messagebox.showerror("Fout bij preview", str(e))

    def gen_pdf(self):
        """
        Gebruikt EXACT wat in het LaTeX-venster staat
        """
        latex_text = self.latex_text.get("1.0", tk.END)

        if not latex_text.strip():
            messagebox.showwarning(
                "Geen LaTeX",
                "Er staat geen LaTeX in het preview-venster.",
            )
            return

        out = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
        )
        if not out:
            return

        try:
            genereer_pdf(latex_text, out)
            messagebox.showinfo("Klaar", f"PDF gegenereerd:\n{out}")
        except Exception as e:
            messagebox.showerror("PDF-fout", str(e))

    # ======================
    # Helpers
    # ======================

    def _load_template(self) -> str:
        """
        Laad template altijd relatief aan dit bestand
        """
        base = Path(__file__).resolve().parent
        return (base / "templates" / "standaard.tex").read_text(encoding="utf-8")


if __name__ == "__main__":
    app = ToetsUI()
    app.mainloop()
