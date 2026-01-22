# Toetsgenerator (YAML → LaTeX)

Een Python-tool om wiskundetoetsen te genereren vanuit **YAML**, met optionele
**AI-ondersteuning** en **lokale PDF-generatie** via LaTeX.

De tool scheidt strikt:
- **inhoud** (YAML),
- **logica** (Python),
- **opmaak** (LaTeX-template),

waardoor dezelfde toets eenvoudig hergebruikt kan worden voor
proefwerken, SE’s, herkansingen en inhaaltoetsen.

---

## Status

**v0.2 – stabiele kern**

- YAML-model met `opgaven → delen → onderdelen`
- Doorlopende nummering (a, b, c, …)
- Grafieken via TikZ / pgfplots
- Verlengers en puntentelling
- UI met bewerkbare YAML- en LaTeX-vensters
- PDF-generatie met duidelijke foutafhandeling

Actieve ontwikkeling op branch: **AI-UI**

---

## Features

- ✔ YAML als enige bron voor toetsinhoud
- ✔ Meerdere delen per opgave (`delen`)
- ✔ Contextregels via `tekst` (LaTeX-veilige `\item[]`)
- ✔ Grafieken als puur LaTeX-blok
- ✔ Doorlopende lettertelling over delen
- ✔ Handmatige correctie van YAML en LaTeX mogelijk
- ✔ Lokale PDF-generatie (MiKTeX / TeX Live)
- ✔ Klaar voor AI-integratie (Ollama / API)

---

## Projectstructuur

