# ui.py
import tkinter as tk
import subprocess
from tkinter import ttk, messagebox, filedialog
from pathlib import Path

from ai.ollama import OllamaClient

from core import (
    laad_yaml_string,
    valideer_toetsstructuur,
    render_document,
    genereer_pdf,
)

def get_ollama_models() -> list[str]:
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            check=True
        )
    except Exception:
        return []

    lines = result.stdout.strip().splitlines()
    if len(lines) <= 1:
        return []

    models = []
    for line in lines[1:]:  # skip header
        parts = line.split()
        if parts:
            models.append(parts[0])

    return models

class ToetsUI(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Toetsgenerator v0.2 (AI)")
        self.geometry("1200x800")
        self.ai_outputs = []
        self.ai_index = -1
        self.available_models = get_ollama_models()
        self.selected_model = tk.StringVar()

        default = (
            self.available_models[0]
            if self.available_models
            else "phi3:latest"
        )
        self.selected_model.set(default)

        self.ai = OllamaClient(model=default)

        self._build_ui()

    # ======================
    # UI layout
    # ======================

    def _build_ui(self):
        main = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main.pack(fill=tk.BOTH, expand=True)

        # ======================
        # LINKS: AI + acties
        # ======================
        left = ttk.Frame(main, width=280)
        main.add(left, weight=0)
        ttk.Label(left, text="Ollama model").pack(
            anchor="w", padx=10, pady=(10, 0)
        )

        self.model_dropdown = ttk.Combobox(
            left,
            textvariable=self.selected_model,
            values=self.available_models,
            state="readonly"
        )
        self.model_dropdown.pack(fill=tk.X, padx=10, pady=(0, 10))
        self.model_dropdown.bind("<<ComboboxSelected>>", self.on_model_change)

        # AI prompt
        ttk.Label(left, text="AI prompt").pack(
            anchor="w", padx=10, pady=(10, 0)
        )

        self.prompt_text = tk.Text(left, height=8, wrap="word")
        self.prompt_text.pack(fill=tk.X, padx=10, pady=(0, 10))

        # Voorbeeldprompt
        self.prompt_text.insert(
            "1.0",
            "Maak een korte toets voor vwo 3 over herleiden en kwadratische vergelijkingen."
        )

        ttk.Button(
            left,
            text="Genereer YAML (AI)",
            command=self.prompt_ai
        ).pack(fill=tk.X, padx=10, pady=5)

        ttk.Separator(left).pack(fill=tk.X, padx=10, pady=10)
        ttk.Label(left, text="AI-voorstel").pack(
            anchor="w", padx=10, pady=(10, 0)
        )

        self.ai_output_text = tk.Text(
            left,
            height=10,
            wrap="word",
            state="disabled",
            background="#f5f5f5"
        )
        self.ai_output_text.pack(fill=tk.X, padx=10, pady=(0, 10))

        ttk.Button(
            left,
            text="Preview → LaTeX",
            command=self.preview
        ).pack(fill=tk.X, padx=10, pady=5)

        ttk.Button(
            left,
            text="Genereer PDF",
            command=self.gen_pdf
        ).pack(fill=tk.X, padx=10, pady=5)

        # ======================
        # RECHTS: editors
        # ======================
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

    def on_model_change(self, event=None):
        model = self.selected_model.get()
        self.ai.model = model


    def prompt_ai(self):
        """
        AI → genereer YAML-voorstel (zonder YAML te wijzigen)
        """
        user_prompt = self.prompt_text.get("1.0", tk.END).strip()

        if not user_prompt:
            messagebox.showwarning(
                "Geen prompt",
                "Voer eerst een AI-prompt in."
            )
            return

        try:
            yaml_text = self.ai.generate_yaml(user_prompt)

            # bewaar in geschiedenis
            self.ai_outputs.append(yaml_text)
            self.ai_index = len(self.ai_outputs) - 1

            # toon in AI-uitvoervak
            self.ai_output_text.configure(state="normal")
            self.ai_output_text.delete("1.0", tk.END)
            self.ai_output_text.insert("1.0", yaml_text)
            self.ai_output_text.configure(state="disabled")

        except Exception as e:
            messagebox.showerror("AI-fout", str(e))


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
                "Er staat geen LaTeX in het preview-venster."
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
            import traceback
            messagebox.showerror(
                "PDF-fout",
                str(e) + "\n\n" + traceback.format_exc()
            )


    # ======================
    # Helpers
    # ======================

    def _load_template(self) -> str:
        """
        Laad template altijd relatief aan dit bestand
        """
        base = Path(__file__).resolve().parent
        return (base / "templates" / "standaard.tex").read_text(
            encoding="utf-8"
        )


if __name__ == "__main__":
    app = ToetsUI()
    app.mainloop()
