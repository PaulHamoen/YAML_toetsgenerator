import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
from pathlib import Path
import yaml

from core import (
    laad_yaml,
    render_document,
    genereer_pdf,
    ToetsFout,
    YAMLSyntaxFout,
)

TEMPLATES_DIR = Path("templates")

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Toetsgenerator")
        self.geometry("900x800")

        self.yaml_path = None
        self.template_path = None
        self.yaml_content = ""

        self._build_ui()

    def _build_ui(self):
        main_frame = tk.Frame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # YAML invoer sectie
        yaml_frame = tk.LabelFrame(main_frame, text="YAML Invoer", padx=5, pady=5)
        yaml_frame.pack(fill="x", pady=5)

        # Keuzemenu voor invoermethode
        self.input_method = tk.StringVar(value="file")
        tk.Radiobutton(yaml_frame, text="Uit bestand", variable=self.input_method,
                      value="file", command=self.toggle_input_method).pack(anchor="w")
        tk.Radiobutton(yaml_frame, text="Direct invoeren", variable=self.input_method,
                      value="direct", command=self.toggle_input_method).pack(anchor="w")

        # Bestand selectie
        self.file_frame = tk.Frame(yaml_frame)
        self.file_frame.pack(fill="x", pady=5)
        tk.Button(self.file_frame, text="Kies YAML", command=self.kies_yaml).pack(side="left")
        self.file_label = tk.Label(self.file_frame, text="Geen bestand geselecteerd")
        self.file_label.pack(side="left", padx=5)

        # Directe YAML invoer
        self.direct_frame = tk.Frame(yaml_frame)
        self.direct_frame.pack(fill="both", expand=True)
        self.yaml_text = scrolledtext.ScrolledText(self.direct_frame, wrap="word", height=10)
        self.yaml_text.pack(fill="both", expand=True)

        # Preview knop
        tk.Button(main_frame, text="Preview", command=self.preview).pack(anchor="w", pady=5)
        tk.Button(main_frame, text="Genereer PDF", command=self.genereer_pdf).pack(anchor="w", pady=5)

        # Toetsinstellingen
        settings_frame = tk.LabelFrame(main_frame, text="Toetsinstellingen", padx=5, pady=5)
        settings_frame.pack(fill="x", pady=5)

        tk.Label(settings_frame, text="Titel").pack(anchor="w")
        self.ent_titel = tk.Entry(settings_frame)
        self.ent_titel.pack(fill="x")

        tk.Label(settings_frame, text="Instructie").pack(anchor="w")
        self.txt_instr = tk.Text(settings_frame, height=4)
        self.txt_instr.pack(fill="x")

        self.var_se = tk.BooleanVar()
        tk.Checkbutton(settings_frame, text="SE-toets", variable=self.var_se).pack(anchor="w")

        # Preview sectie
        tk.Label(main_frame, text="Preview (LaTeX)").pack(anchor="w")
        self.preview_box = scrolledtext.ScrolledText(main_frame, wrap="word")
        self.preview_box.pack(fill="both", expand=True)

        # Templates laden
        templates = sorted(TEMPLATES_DIR.glob("*.tex"))
        if templates:
            self.template_path = templates[0]

        # Initial state
        self.toggle_input_method()

    def toggle_input_method(self):
        if self.input_method.get() == "file":
            self.file_frame.pack(fill="x", pady=5)
            self.direct_frame.pack_forget()
        else:
            self.file_frame.pack_forget()
            self.direct_frame.pack(fill="both", expand=True, pady=5)

    def kies_yaml(self):
        path = filedialog.askopenfilename(
            filetypes=[("YAML", "*.yaml *.yml")]
        )
        if path:
            self.yaml_path = Path(path)
            self.file_label.config(text=f"Geselecteerd: {self.yaml_path.name}")

    def get_yaml_data(self):
        if self.input_method.get() == "file":
            if not self.yaml_path:
                raise ValueError("Geen YAML-bestand geselecteerd")
            return laad_yaml(self.yaml_path)
        else:
            yaml_content = self.yaml_text.get("1.0", "end-1c")
            if not yaml_content.strip():
                raise ValueError("Geen YAML ingevoerd")
            try:
                return yaml.safe_load(yaml_content)
            except yaml.YAMLError as e:
                raise YAMLSyntaxFout(str(e))

    def preview(self):
        if not self.template_path:
            messagebox.showwarning("Ontbreekt", "Geen template beschikbaar")
            return

        try:
            data = self.get_yaml_data()
            toets = data.get("toets", {})
            template = self.template_path.read_text(encoding="utf-8")

            tex = render_document(
                toets=toets,
                template_text=template,
                titel=self.ent_titel.get() or "Toets",
                instructie=self.txt_instr.get("1.0", "end").strip(),
                se=self.var_se.get(),
            )

            self.preview_box.delete("1.0", "end")
            self.preview_box.insert("1.0", tex)

            # Sla LaTeX op voor PDF-generatie
            self.laatste_latex = tex

        except Exception as e:
            messagebox.showerror("Fout", str(e))

    def genereer_pdf(self):
        if not hasattr(self, "laatste_latex") or not self.laatste_latex:
            messagebox.showwarning("Ontbreekt", "Genereer eerst een preview")
            return

        try:
            pdf_pad = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF", "*.pdf")]
            )
            if pdf_pad:
                genereer_pdf(self.laatste_latex, pdf_pad)
                messagebox.showinfo("Succes", f"PDF gegenereerd: {pdf_pad}")
        except Exception as e:
            messagebox.showerror("Fout", str(e))         


if __name__ == "__main__":
    App().mainloop()