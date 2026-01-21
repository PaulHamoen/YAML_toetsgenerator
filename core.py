# core.py
import yaml
import os
import subprocess
import tempfile
from pathlib import Path
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
# YAML laden & validatie
# ============================================================

def laad_yaml(pad: Path) -> dict:
    try:
        return yaml.safe_load(pad.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        raise YAMLSyntaxFout(str(e))


def valideer_toetsstructuur(toets: dict):
    if not isinstance(toets, dict):
        raise ToetsFout("Root 'toets' moet een dictionary zijn")

    if "opgaven" not in toets:
        raise ToetsFout("YAML mist sleutel: toets.opgaven")

    if not isinstance(toets["opgaven"], list):
        raise ToetsFout("toets.opgaven moet een lijst zijn")

    for i, opg in enumerate(toets["opgaven"], start=1):
        if "titel" not in opg:
            raise ToetsFout(f"Opgave {i} mist 'titel'")
        if "onderdelen" not in opg:
            raise ToetsFout(f"Opgave {i} mist 'onderdelen'")

        for j, ond in enumerate(opg["onderdelen"], start=1):
            if "punten" not in ond:
                raise ToetsFout(f"Opgave {i}, onderdeel {j}: mist 'punten'")
            if "inhoud" not in ond:
                raise ToetsFout(f"Opgave {i}, onderdeel {j}: mist 'inhoud'")
            if ond.get("mode", "latex") not in ("math", "latex"):
                raise ToetsFout(
                    f"Opgave {i}, onderdeel {j}: mode moet 'math' of 'latex' zijn"
                )


# ============================================================
# Statistiek
# ============================================================

def bereken_statistiek(toets: dict) -> dict:
    """
    Bereken het aantal opgaven, totaal punten en verlengers.
    Retourneert altijd een dictionary, ook als er geen opgaven zijn.
    """
    totaal_punten = 0
    verlengers = 0

    for opg in toets.get("opgaven", []):
        for ond in opg.get("onderdelen", []):
            try:
                punten = int(ond.get("punten", 0))
                totaal_punten += punten
                if ond.get("verlenger", False):
                    verlengers += punten
            except (ValueError, TypeError):
                raise ToetsFout(f"Ongeldige puntenwaarde: {ond.get('punten')} (moet een getal zijn)")

    return {
        "aantal_opgaven": len(toets.get("opgaven", [])),
        "totaal_punten": totaal_punten,
        "verlengers": verlengers
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
    Render alle opgaven naar LaTeX, inclusief:
    - needspace_cm op opgave-niveau
    - Meerdere delen per opgave (met eigen tekst)
    - Doorlopende a), b), c) over alle delen
    - Grafieken tussen onderdelen zonder enumerate-fouten
    - Punten en verlengers
    """
    out = []

    for opg in toets.get("opgaven", []):
        # Ruimte afdwingen vóór de opgave
        needspace = opg.get("needspace_cm", 0)
        if needspace:
            out.append(rf"\needspace{{{needspace}cm}}")

        # Start opgave
        out.append(r"\begin{enumerate}[label=\textbf{\arabic*.}, ref=\arabic*]")
        out.append(rf"\item \opgave{{{opg['titel']}}}")

        # Start één doorlopende onderdelen-enumerate
        out.append(r"\begin{enumerate}[label=\alph*), ref=\alph*]")

        for deel in opg.get("delen", []):
            # tekst per deel
            if "tekst" in deel:
                tekst_mode = deel.get("tekst_mode", "latex")
                tekst = render_block(tekst_mode, deel["tekst"])
                out.append(rf"\item[] {tekst}")
            # LET OP: tekst moet altijd via \item[] binnen enumerate

            default_verl = deel.get("verlenger", False)

            for ond in deel.get("onderdelen", []):
                # Grafiek → enumerate tijdelijk sluiten
                if "grafiek" in ond:
                    out.append(r"\end{enumerate}")
                    out.append(ond["grafiek"])
                    out.append(
                        r"\begin{enumerate}[resume*, label=\alph*), ref=\alph*]"
                    )
                    continue

                punten = int(ond.get("punten", 0))
                is_verl = ond.get("verlenger", default_verl)

                punten_cmd = ""
                if punten > 0:
                    cmd = r"\verlpunt" if is_verl else r"\punten"
                    punten_cmd = rf"{cmd}{{{punten}}} "

                inhoud_mode = ond.get("mode", "latex")
                inhoud_latex = render_block(inhoud_mode, ond.get("inhoud", ""))

                out.append(rf"\item {punten_cmd}{inhoud_latex}")

        # Sluit onderdelen-enumerate
        out.append(r"\end{enumerate}")

        # Sluit opgave
        out.append(r"\end{enumerate}")
        out.append(r"\vspace{1cm}")
        out.append("\n% ======================\n")

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

        pdf_bron.rename(output_pdf)