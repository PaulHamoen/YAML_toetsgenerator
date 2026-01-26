# core.py
import yaml
import subprocess
import tempfile
from pathlib import Path


# ======================
# Exceptions
# ======================

class ToetsFout(Exception):
    pass


class YAMLSyntaxFout(Exception):
    pass


# ======================
# YAML laden
# ======================

def laad_yaml_string(yaml_text: str) -> dict:
    try:
        data = yaml.safe_load(yaml_text)
    except yaml.YAMLError as e:
        raise YAMLSyntaxFout(str(e))

    if not isinstance(data, dict):
        raise ToetsFout("YAML root moet een dictionary zijn")

    return data

def bereken_punten(toets: dict) -> dict:
    totaal = 0
    verl = 0

    for opg in toets.get("opgaven", []):
        for deel in opg.get("delen", []):
            for ond in deel.get("onderdelen", []):
                punten = int(ond.get("punten", 0))
                totaal += punten
                if ond.get("verlenger", False):
                    verl += punten

    return {
        "totaal": totaal,
        "verlengers": verl,
    }


# ======================
# Validatie
# ======================

def valideer_toetsstructuur(toets: dict):
    if "opgaven" not in toets:
        raise ToetsFout("YAML mist sleutel: toets.opgaven")

    if not isinstance(toets["opgaven"], list):
        raise ToetsFout("toets.opgaven moet een lijst zijn")

    for i, opg in enumerate(toets["opgaven"], start=1):
        if "titel" not in opg:
            raise ToetsFout(f"Opgave {i} mist 'titel'")
        if "delen" not in opg:
            raise ToetsFout(f"Opgave {i} mist 'delen'")


# ======================
# Rendering helpers
# ======================

def render_block(mode: str, inhoud: str) -> str:
    if not inhoud:
        return ""
    if mode == "math":
        return rf"\( {inhoud} \)"
    return inhoud


# ======================
# Opgaven → LaTeX
# ======================

def render_opgaven(toets: dict) -> str:
    out = []

    out.append(r"\begin{enumerate}[label=\textbf{\arabic*.}, ref=\arabic*]")

    for opg in toets.get("opgaven", []):
        if opg.get("needspace_cm"):
            out.append(rf"\needspace{{{opg['needspace_cm']}cm}}")

        out.append(rf"\item \opgave{{{opg['titel']}}}")
        out.append(r"\begin{enumerate}[label=\alph*), ref=\alph*]")

        enumerate_open = True
        had_item = False

        for deel in opg.get("delen", []):
            if "tekst" in deel:
                out.append(rf"\item[] {render_block('latex', deel['tekst'])}")

            for ond in deel.get("onderdelen", []):
                if "grafiek" in ond and ond["grafiek"].strip():
                    if enumerate_open:
                        out.append(r"\end{enumerate}")
                        enumerate_open = False

                    out.append(ond["grafiek"])

                    if had_item:
                        out.append(
                            r"\begin{enumerate}[resume*, label=\alph*), ref=\alph*]"
                        )
                        enumerate_open = True
                    continue

                punten = int(ond.get("punten", 0))
                verl = ond.get("verlenger", False)

                punten_cmd = ""
                if punten:
                    punten_cmd = (
                        rf"\verlpunt{{{punten}}} "
                        if verl else rf"\punten{{{punten}}} "
                    )

                inhoud = render_block(
                    ond.get("mode", "latex"),
                    ond.get("inhoud", "")
                )

                out.append(rf"\item {punten_cmd}{inhoud}")
                had_item = True

        if enumerate_open:
            out.append(r"\end{enumerate}")

        out.append(r"\vspace{1cm}")
        out.append("\n% ======================\n")

    out.append(r"\end{enumerate}")
    return "\n".join(out)


# ======================
# Document
# ======================

def render_document(
    toets: dict,
    template_text: str,
    titel: str = "Toets",
    inleiding: str = "",
    logo: str = "",
) -> str:
    from core import bereken_punten

    stats = bereken_punten(toets)
    toets_latex = render_opgaven(toets)

    return (
        template_text
        .replace("{{TOETS}}", toets_latex)
        .replace("{{TITEL}}", titel)
        .replace("{{INLEIDING}}", inleiding)
        .replace("{{TOTAAL_PUNTEN}}", str(stats["totaal"]))
        .replace("{{VERL_PUNTEN}}", str(stats["verlengers"]))
        .replace("{{LOGO}}", logo)
    )


# ======================
# PDF generatie
# ======================

def genereer_pdf(latex_text: str, output_pdf: str):
    with tempfile.TemporaryDirectory() as tmpdir:
        tex = Path(tmpdir) / "toets.tex"
        tex.write_text(latex_text, encoding="utf-8")

        try:
            subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", tex.name],
                cwd=tmpdir,
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(e.stderr)

        pdf = Path(tmpdir) / "toets.pdf"
        if not pdf.exists():
            raise RuntimeError("PDF niet gegenereerd")

        Path(output_pdf).write_bytes(pdf.read_bytes())
