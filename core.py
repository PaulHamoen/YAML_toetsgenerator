# core.py
import yaml
import os
import subprocess
import tempfile
import shutil

from pathlib import Path

def _heeft_echte_items(onderdelen: list, start_index: int) -> bool:
    """
    True als er na start_index nog minstens één onderdeel is dat een echte \item oplevert
    (dus: niet alleen grafiek-blokken).
    """
    for ond in onderdelen[start_index:]:
        if "grafiek" in ond:
            continue
        # een "echte" item: heeft inhoud of punten, maakt niet uit
        if ond.get("inhoud") or ond.get("punten", 0):
            return True
    return False


# ============================================================
# Exceptions
# ============================================================

class ToetsFout(Exception):
    """Fout in toets-YAML (structuur of inhoud)."""
    pass

class YAMLSyntaxFout(Exception):
    """Syntaxfout in YAML."""
    pass

# ============================================================
# Check system dependancies
# ============================================================

def check_pdflatex():
    if shutil.which("pdflatex") is None:
        raise RuntimeError(
            "pdflatex niet gevonden.\n"
            "Installeer MiKTeX (Windows) of TeX Live.\n"
            "Controleer met: pdflatex --version"
        )

# ============================================================
# YAML laden & validatie
# ============================================================

def laad_yaml_string(yaml_text: str) -> dict:
    try:
        return yaml.safe_load(yaml_text)
    except yaml.YAMLError as e:
        raise Exception(f"YAML-fout: {e}")



def valideer_toetsstructuur(toets: dict):
    if "opgaven" not in toets or not isinstance(toets["opgaven"], list):
        raise ToetsFout("YAML mist sleutel: toets.opgaven")

    for i, opg in enumerate(toets["opgaven"], start=1):
        if "titel" not in opg:
            raise ToetsFout(f"Opgave {i} mist 'titel'")

        if "delen" not in opg or not isinstance(opg["delen"], list):
            raise ToetsFout(f"Opgave {i} mist 'delen'")

        for j, deel in enumerate(opg["delen"], start=1):
            if "onderdelen" not in deel or not isinstance(deel["onderdelen"], list):
                raise ToetsFout(f"Opgave {i}, deel {j} mist 'onderdelen'")

            for k, ond in enumerate(deel["onderdelen"], start=1):
                if "grafiek" in ond:
                    continue  # grafiek heeft geen punten/inhoud

                if "punten" not in ond:
                    raise ToetsFout(
                        f"Opgave {i}, deel {j}, onderdeel {k} mist 'punten'"
                    )

                if "inhoud" not in ond:
                    raise ToetsFout(
                        f"Opgave {i}, deel {j}, onderdeel {k} mist 'inhoud'"
                    )

                if ond.get("mode", "latex") not in ("math", "latex"):
                    raise ToetsFout(
                        f"Opgave {i}, deel {j}, onderdeel {k}: ongeldige mode"
                    )


# ============================================================
# Statistiek
# ============================================================

def bereken_statistiek(toets: dict) -> dict:
    totaal_punten = 0
    verlengers = 0

    for opg in toets.get("opgaven", []):
        for deel in opg.get("delen", []):
            default_verl = deel.get("verlenger", False)

            for ond in deel.get("onderdelen", []):
                if "grafiek" in ond:
                    continue

                punten = int(ond.get("punten", 0))
                totaal_punten += punten

                if ond.get("verlenger", default_verl):
                    verlengers += punten

    return {
        "aantal_opgaven": len(toets.get("opgaven", [])),
        "totaal_punten": totaal_punten,
        "verlengers": verlengers,
    }


# ============================================================
# Rendering helpers
# ============================================================

def render_se_voorblad(titel: str, statistiek: dict) -> str:
    """
    Genereer een SE-voorblad met de gegeven titel en statistiek.
    """
    return rf"""
\begin{{center}}
\textbf{{\Huge {titel}}} \\
\vspace{{1cm}}
Aantal opgaven: {statistiek['aantal_opgaven']} \\
Totaal punten: {statistiek['totaal_punten']} \\
Verlengers: {statistiek['verlengers']} \\
\end{{center}}
\clearpage
"""

def render_block(mode: str, inhoud: str) -> str:
    if not inhoud:
        return ""
    if mode == "math":
        return rf"\( {inhoud} \)"
    return inhoud


def render_opgaven(toets: dict) -> str:
    """
    Definitieve renderer (EINDVERSIE):

    - Opgaven: 1., 2., 3. (exact één enumerate)
    - Onderdelen per opgave: a), b), c. (exact één enumerate per opgave)
    - Tekst altijd als \\item[]
    - Grafieken mogen vóór / tussen / na items staan
    - Enumerate wordt alleen hervat als dat structureel logisch is
    - Nooit \\item buiten een enumerate
    - Nooit lege enumerate
    """
    out = []

    # === OPGAVEN-ENUMERATE (1x) ===
    out.append(r"\begin{enumerate}[label=\textbf{\arabic*.}, ref=\arabic*]")

    for opg in toets.get("opgaven", []):
        # Ruimte vóór opgave
        if opg.get("needspace_cm"):
            out.append(rf"\needspace{{{opg['needspace_cm']}cm}}")

        # Opgave-titel (genummerd)
        out.append(rf"\item \opgave{{{opg['titel']}}}")

        # === ONDERDELEN-ENUMERATE (1x per opgave) ===
        out.append(r"\begin{enumerate}[label=\alph*), ref=\alph*]")

        enumerate_open = True
        item_ooit_gehad = False     # elk \\item of \\item[]
        resume_open = False
        item_na_resume = False

        for deel in opg.get("delen", []):
            # Tekst → altijd geldig enumerate-item
            if "tekst" in deel:
                tekst = render_block(
                    deel.get("tekst_mode", "latex"),
                    deel["tekst"]
                )
                out.append(rf"\item[] {tekst}")
                item_ooit_gehad = True

            default_verl = deel.get("verlenger", False)

            for ond in deel.get("onderdelen", []):
                grafiek = ond.get("grafiek", "")
                if isinstance(grafiek, str) and grafiek.strip():
                    # Sluit enumerate vóór grafiek
                    if enumerate_open:
                        out.append(r"\end{enumerate}")
                        enumerate_open = False

                    out.append(grafiek)

                    # Hervat enumerate ALLEEN als er al items waren
                    if item_ooit_gehad:
                        out.append(
                            r"\begin{enumerate}[resume*, label=\alph*), ref=\alph*]"
                        )
                        enumerate_open = True
                        resume_open = True
                        item_na_resume = False
                    continue

                # ===== NORMAAL ITEM =====
                punten = int(ond.get("punten", 0))
                is_verl = ond.get("verlenger", default_verl)

                punten_cmd = ""
                if punten > 0:
                    cmd = r"\verlpunt" if is_verl else r"\punten"
                    punten_cmd = rf"{cmd}{{{punten}}} "

                inhoud = render_block(
                    ond.get("mode", "latex"),
                    ond.get("inhoud", "")
                )

                out.append(rf"\item {punten_cmd}{inhoud}")
                item_ooit_gehad = True

                if resume_open:
                    item_na_resume = True

        # Dummy item als grafiek het laatste was NA resume
        if resume_open and not item_na_resume:
            out.append(r"\item[]~")

        # Sluit onderdelen-enumerate
        if enumerate_open:
            out.append(r"\end{enumerate}")

        out.append(r"\vspace{1cm}")
        out.append("\n% ======================\n")

    # Sluit opgaven-enumerate
    out.append(r"\end{enumerate}")

    return "\n".join(out)



# ============================================================
# Document rendering
# ============================================================

def render_document(toets: dict, template_text: str, titel: str = "Toets", instructie: str = "", se: bool = False) -> str:
    """
    Render het volledige LaTeX-document, inclusief voorblad (indien SE).
    Vervangt de placeholders {{VOORBLAD}} en {{TOETS}} in het template.
    """
    # Genereer de opgaven-LaTeX
    opgaven_latex = render_opgaven(toets)
    statistiek = bereken_statistiek(toets)

    # Genereer het voorblad (indien SE)
    voorblad_latex = ""
    if se:
        voorblad_latex = render_se_voorblad(titel, statistiek)

    # Vervang de placeholders in het template
    document = template_text.replace("{{VOORBLAD}}", voorblad_latex)
    document = document.replace("{{TOETS}}", opgaven_latex)

    return document
import subprocess
import tempfile
from pathlib import Path

def genereer_pdf(laatst_gegenereerde_latex: str, output_pdf: str) -> None:
    check_pdflatex()
    """
    Genereer een PDF van de LaTeX-code met pdflatex.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tex_bestand = Path(tmpdir) / "toets.tex"
        tex_bestand.write_text(laatst_gegenereerde_latex, encoding="utf-8")

        try:
            # Compileer 2x voor zekerheid (voor referenties)
            for _ in range(2):
                subprocess.run(
                    ["pdflatex", "-interaction=nonstopmode", str(tex_bestand)],
                    cwd=tmpdir,
                    check=True,
                    capture_output=True,
                    text=True
                )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"PDF-generatie mislukt: {e.stderr}") from e

        pdf_bron = Path(tmpdir) / "toets.pdf"
        if not pdf_bron.exists():
            raise FileNotFoundError("PDF niet gegenereerd (pdflatex-fout)")

        pdf_bron.replace(output_pdf)
