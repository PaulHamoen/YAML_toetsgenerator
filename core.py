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


# ======================
# Validatie
# ======================

def valideer_en_normaliseer_toets(data: dict) -> dict:
    print("=== VALIDATOR ENTRY ===")
    print("DATA KEYS IN VALIDATOR:", list(data.keys()))

    if not isinstance(data, dict):
        raise ToetsFout("YAML root moet een dictionary zijn")

    print("CHECK se/pw:", "se" in data, "pw" in data)

    if "se" not in data and "pw" not in data:
        raise ToetsFout("YAML moet beginnen met 'se:' of 'pw:'")

    if "se" in data and "pw" in data:
        raise ToetsFout("YAML mag niet tegelijk 'se:' en 'pw:' bevatten")

    modus = "se" if "se" in data else "pw"
    items = data[modus]

    if not isinstance(items, list):
        raise ToetsFout(f"'{modus}' moet een lijst zijn")

    opgaven = []
    huidige_opgave = None

    def start_opgave(titel: str):
        return {"titel": titel, "items": []}

    if modus == "se":
        huidige_opgave = start_opgave("")
        opgaven.append(huidige_opgave)

    for idx, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            raise ToetsFout(f"Item {idx} is geen dictionary")

        # ---------- opgave ----------
        if "opgave" in item:
            if modus == "se":
                raise ToetsFout("Sleutel 'opgave' is niet toegestaan in 'se'")

            titel = item["opgave"]
            if not isinstance(titel, str):
                raise ToetsFout("Opgave-titel moet een string zijn")

            huidige_opgave = start_opgave(titel)
            opgaven.append(huidige_opgave)
            continue

        if huidige_opgave is None:
            raise ToetsFout(
                "Proefwerk moet beginnen met een 'opgave'"
            )

        # ---------- vraag ----------
        if "punten" in item:
            if "vraag" not in item:
                raise ToetsFout(
                    f"Item {idx} heeft 'punten' maar geen 'vraag'"
                )
            if not isinstance(item["punten"], int):
                raise ToetsFout(
                    f"Item {idx}: 'punten' moet een integer zijn"
                )

            huidige_opgave["items"].append({
                "type": "vraag",
                "punten": item["punten"],
                "verlenger": item.get("verlenger", False),
                "mode": item.get("mode", "latex"),
                "inhoud": item["vraag"],
            })
            continue

        # ---------- tekst ----------
        if "tekst" in item:
            huidige_opgave["items"].append({
                "type": "tekst",
                "mode": item.get("mode", "latex"),
                "inhoud": item["tekst"],
            })
            continue

        # ---------- grafiek ----------
        if "grafiek" in item:
            huidige_opgave["items"].append({
                "type": "grafiek",
                "inhoud": item["grafiek"],
            })
            continue

        raise ToetsFout(f"Onbekend item op positie {idx}")

    return {
        "modus": modus,
        "opgaven": opgaven,
    }


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

    if toets["modus"] == "se":
        out.append(r"\begin{enumerate}[label=\textbf{\arabic*.}]")

        for opg in toets["opgaven"]:
            for item in opg["items"]:
                if item["type"] == "tekst":
                    out.append(r"\item[] " + render_block(item["mode"], item["inhoud"]))

                elif item["type"] == "grafiek":
                    out.append(r"\item[] " + item["inhoud"])
                elif item["type"] == "vraag":
                    punten = item["punten"]
                    verl = item["verlenger"]
                    cmd = r"\verlpunt" if verl else r"\punten"
                    out.append(
                        rf"\item {cmd}{{{punten}}} "
                        + render_block(item["mode"], item["inhoud"])
                    )

        out.append(r"\end{enumerate}")
        return "\n".join(out)

    # =========================
    # PROEFWERK
    # =========================

    out.append(r"\begin{enumerate}[label=\textbf{\arabic*.}]")

    for opg in toets["opgaven"]:
        out.append(rf"\item \opgave{{{opg['titel']}}}")
        out.append(r"\begin{enumerate}[label=\alph*)]")

        for item in opg["items"]:
            if item["type"] == "tekst":
                out.append(rf"\item[] {render_block(item['mode'], item['inhoud'])}")
            elif item["type"] == "grafiek":
                    out.append(r"\item[] " + item["inhoud"])
            elif item["type"] == "vraag":
                punten = item["punten"]
                verl = item["verlenger"]
                cmd = r"\verlpunt" if verl else r"\punten"
                out.append(
                    rf"\item {cmd}{{{punten}}} "
                    + render_block(item["mode"], item["inhoud"])
                )

        out.append(r"\end{enumerate}")
        out.append(r"\vspace{1cm}")

    out.append(r"\end{enumerate}")
    return "\n".join(out)



# ======================
# Document
# ======================

def render_document(
    toets: dict,
    template_text: str,
    titel: str = "Toets",
    instructie: str = "",
    se: bool = False,
) -> str:
    opgaven_latex = render_opgaven(toets)
    return template_text.replace("{{TOETS}}", opgaven_latex)

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
