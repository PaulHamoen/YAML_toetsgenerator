# core.py
from pathlib import Path
import yaml
import argparse
from pathlib import Path
from core import laad_yaml, render_document, genereer_pdf, valideer_toetsstructuur
BASE_DIR = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description="Genereer een toets uit YAML.")
    parser.add_argument("yaml", help="Pad naar het YAML-bestand")
    parser.add_argument("--titel", default="Toets", help="Titel van de toets")
    parser.add_argument("--instructie", default="", help="Instructie voor de toets")
    parser.add_argument("--se", action="store_true", help="Genereer een SE-voorblad")
    parser.add_argument("--pdf", action="store_true", help="Genereer ook een PDF")
    parser.add_argument("--pdf-pad", default="toets.pdf", help="Pad voor de PDF (standaard: toets.pdf)")
    args = parser.parse_args()

    # Laad YAML en template
    data = laad_yaml(Path(args.yaml))
    valideer_toetsstructuur(data["toets"])
    template = (BASE_DIR / "templates" / "standaard.tex").read_text(encoding="utf-8")

    # Genereer LaTeX
    latex = render_document(
        toets=data["toets"],
        template_text=template,
        titel=args.titel,
        instructie=args.instructie,
        se=args.se
    )

    # Sla LaTeX op
    Path("laatste_toets.tex").write_text(latex, encoding="utf-8")

    # Genereer PDF indien gevraagd
    if args.pdf:
        genereer_pdf(latex, args.pdf_pad)
        print(f"PDF gegenereerd: {args.pdf_pad}")

    print("Toets gegenereerd!")

if __name__ == "__main__":
    main()
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
    totaalpunten = 0
    verlengerspunten = 0
    aantal_opgaven = 0

    for opg in toets.get("opgaven", []):
        aantal_opgaven += 1
        default_verl = opg.get("verlenger", False)

        for ond in opg.get("onderdelen", []):
            p = int(ond.get("punten", 0))
            totaalpunten += p
            if ond.get("verlenger", default_verl):
                verlengerspunten += p

    return {
        "aantal_opgaven": aantal_opgaven,
        "totaalpunten": totaalpunten,
        "verlengerspunten": verlengerspunten,
    }


# ============================================================
# Rendering helpers
# ============================================================

def render_block(mode: str, inhoud: str) -> str:
    if not inhoud:
        return ""
    if mode == "math":
        return rf"\( {inhoud} \)"
    return inhoud


def render_opgaven(toets: dict) -> str:
    out = []

    for opg in toets.get("opgaven", []):
        needspace = opg.get("needspace_cm", 0)
        if needspace:
            out.append(rf"\needspace{{{needspace}cm}}")

        out.append(rf"\opgave{{{opg['titel']}}}")

        if "tekst" in opg:
            out.append(
                render_block(
                    opg.get("tekst_mode", "latex"),
                    opg["tekst"]
                )
            )

        if "grafiek" in opg:
            out.append(opg["grafiek"])

        out.append(r"\begin{enumerate}")
        default_verl = opg.get("verlenger", False)

        for ond in opg.get("onderdelen", []):
            out.append(r"\item")

            punten = int(ond.get("punten", 0))
            is_verl = ond.get("verlenger", default_verl)

            if punten > 0:
                cmd = r"\verlpunt" if is_verl else r"\punten"
                out.append(rf"{cmd}{{{punten}}}")

            out.append(render_block(
                ond.get("mode", "latex"),
                ond.get("inhoud", "")
            ))

        out.append(r"\end{enumerate}")
        out.append(r"\vspace{1cm}")
        out.append("\n% ======================\n")

    return "\n".join(out)


# ============================================================
# Document rendering
# ============================================================

def render_document(
    toets: dict,
    template_text: str,
    titel: str,
    instructie: str,
    se: bool
) -> str:
    valideer_toetsstructuur(toets)
    stats = bereken_statistiek(toets)
    opgaven_tex = render_opgaven(toets)

    voorblad = ""
    if se:
        voorblad = rf"""
\thispagestyle{{empty}}
\vspace*{{\fill}}
\begin{{center}}
\Huge SE-toets

\vspace{{1cm}}
\Large {titel}

\vspace{{1cm}}
Aantal opgaven: {stats['aantal_opgaven']}\\
Totaal aantal punten: {stats['totaalpunten']}
\end{{center}}
\vspace*{{\fill}}
\newpage
"""

    toetsblok = rf"""
\section*{{{titel}}}

{instructie.replace("\n", "\\\\\n")}

\bigskip
\begin{{enumerate}}[leftmargin=*, label=\textbf{{\arabic*.}}]
{opgaven_tex}
\end{{enumerate}}

\bigskip
\hrule
\bigskip

\textbf{{Overzicht punten}}

\begin{{tabular}}{{@{{}}lr@{{}}}}
Totaal aantal punten: & \textbf{{{stats['totaalpunten']}}} \\
Verlengerspunten:    & \textbf{{{stats['verlengerspunten']}}}
\end{{tabular}}
"""

    return (
        template_text
        .replace("{{VOORBLAD}}", voorblad)
        .replace("{{TOETS}}", toetsblok)
    )
