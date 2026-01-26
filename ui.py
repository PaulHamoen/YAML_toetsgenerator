# ui.py
import tkinter as tk
import subprocess
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / "ai" / ".env")

from ai.ollama import OllamaClient
from ai.mistral import MistralClient

from core import (
    laad_yaml_string,
    valideer_en_normaliseer_toets,
    render_document,
    genereer_pdf,
)


def get_ollama_models():
    try:
        r = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            check=True,
        )
    except Exception:
        return []

    lines = r.stdout.strip().splitlines()[1:]
    return [line.split()[0] for line in lines if line.strip()]


class ToetsUI(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Toetsgenerator v0.3 (AI)")
        self.geometry("1200x800")

        self.available_ollama_models = get_ollama_models()
        self.available_mistral_models = [
            "mistral-small",
            "mistral-medium",
            "mistral-large",
        ]

        self.ai_provider = tk.StringVar(value="ollama")
        self.selected_model = tk.StringVar(
            value=self.available_ollama_models[0]
            if self.available_ollama_models else ""
        )

        self._build_ui()
        self.on_provider_change()

    # ======================
    # UI
    # ======================

    def _build_ui(self):
        main = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main.pack(fill=tk.BOTH, expand=True)

        left = ttk.Frame(main, width=280)
        main.add(left, weight=0)

        ttk.Label(left, text="AI provider").pack(padx=10, pady=(10, 2))

        ttk.Radiobutton(
            left, text="Ollama (local)",
            variable=self.ai_provider,
            value="ollama",
            command=self.on_provider_change
        ).pack(anchor="w", padx=20)

        ttk.Radiobutton(
            left, text="Mistral (API)",
            variable=self.ai_provider,
            value="mistral",
            command=self.on_provider_change
        ).pack(anchor="w", padx=20)

        self.model_label = ttk.Label(left, text="Model")
        self.model_label.pack(anchor="w", padx=10, pady=(10, 0))

        self.model_dropdown = ttk.Combobox(
            left,
            textvariable=self.selected_model,
            state="readonly"
        )
        self.model_dropdown.pack(fill=tk.X, padx=10, pady=(0, 10))

        ttk.Label(left, text="AI prompt").pack(anchor="w", padx=10)
        self.prompt_text = tk.Text(left, height=7, wrap="word")
        self.prompt_text.pack(fill=tk.X, padx=10)

        self.prompt_text.insert(
            "1.0",
            "Maak een korte toets voor vwo 3 over herleiden."
        )

        ttk.Button(
            left, text="Genereer YAML (AI)", command=self.prompt_ai
        ).pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(left, text="AI-voorstel").pack(anchor="w", padx=10)
        self.ai_output_text = tk.Text(
            left, height=10, wrap="word",
            state="disabled", background="#f5f5f5"
        )
        self.ai_output_text.pack(fill=tk.X, padx=10)

        ttk.Button(left, text="Preview → LaTeX", command=self.preview)\
            .pack(fill=tk.X, padx=10, pady=5)

        ttk.Button(left, text="Genereer PDF", command=self.gen_pdf)\
            .pack(fill=tk.X, padx=10)

        right = ttk.PanedWindow(main, orient=tk.VERTICAL)
        main.add(right, weight=1)

        yaml_frame = ttk.LabelFrame(right, text="YAML")
        right.add(yaml_frame, weight=1)
        self.yaml_text = tk.Text(yaml_frame)
        self.yaml_text.pack(fill=tk.BOTH, expand=True)

        latex_frame = ttk.LabelFrame(right, text="LaTeX")
        right.add(latex_frame, weight=1)
        self.latex_text = tk.Text(latex_frame)
        self.latex_text.pack(fill=tk.BOTH, expand=True)

    # ======================
    # Logic
    # ======================

    def on_provider_change(self):
        if self.ai_provider.get() == "ollama":
            self.model_label.config(text="Ollama model")
            models = self.available_ollama_models
        else:
            self.model_label.config(text="Mistral model")
            models = self.available_mistral_models

        self.model_dropdown["values"] = models
        self.selected_model.set(models[0] if models else "")

    def _get_ai_client(self):
        model = self.selected_model.get()
        if self.ai_provider.get() == "ollama":
            return OllamaClient(model=model)
        return MistralClient(model=model)

    def prompt_ai(self):
        try:
            client = self._get_ai_client()
            result = client.generate_yaml(
                self.prompt_text.get("1.0", tk.END)
            )
            self.ai_output_text.config(state="normal")
            self.ai_output_text.delete("1.0", tk.END)
            self.ai_output_text.insert("1.0", result)
            self.ai_output_text.config(state="disabled")
        except Exception as e:
            messagebox.showerror("AI-fout", str(e))

    def preview(self):
        raw = self.yaml_text.get("1.0", tk.END)

        print("=== RAW YAML (repr) ===")
        print(repr(raw))
        print("=======================")

        try:
            data = laad_yaml_string(self.yaml_text.get("1.0", tk.END))
            toets = valideer_en_normaliseer_toets(data)
            template = self._load_template()

            voorblad = ""

            if toets["modus"] == "se":
                voorblad = rf"""
            \thispagestyle{{empty}}
            \vspace*{{\fill}}
            \begin{{center}}
            \Large SE-toets

            \vspace{{1cm}}
            \textbf{{Naam:}}\hfill\textbf{{Klas:}}

            \vspace{{1cm}}
            Beantwoord alle vragen duidelijk en volledig.
            \end{{center}}
            \vspace*{{\fill}}
            \newpage
            """

            latex = render_document(
                toets,
                template,
                voorblad=voorblad
            )


            self.latex_text.delete("1.0", tk.END)
            self.latex_text.insert("1.0", latex)

        except Exception as e:
            messagebox.showerror("Preview-fout", str(e))

    def gen_pdf(self):
        out = filedialog.asksaveasfilename(defaultextension=".pdf")
        if not out:
            return
        try:
            genereer_pdf(self.latex_text.get("1.0", tk.END), out)
            messagebox.showinfo("Klaar", out)
        except Exception as e:
            messagebox.showerror("PDF-fout", str(e))

    def _load_template(self):
        return (
            Path(__file__).resolve().parent
            / "templates" / "standaard.tex"
        ).read_text(encoding="utf-8")


if __name__ == "__main__":
    ToetsUI().mainloop()
