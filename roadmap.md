📌 Roadmap — YAML Toetsgenerator
Fase 0 — Stabilisatie (bijna klaar, maar belangrijk)

Status: vrijwel afgerond

0.1 Betere foutinformatie (YAML & LaTeX)

Waarom: wat je net meemaakte mag niet meer “gevoel” vereisen.

YAML

Gebruik yaml.safe_load() met try/except

Toon:

regelnummer

kolom

originele foutmelding

UI: foutpopup met:

YAML-fout
Regel 12, kolom 18
mapping values are not allowed here


Implementatieplek

laad_yaml_string()

ui.py → preview()

LaTeX

Bij pdflatex:

bewaar .log

parse laatste errorblok

Toon:

LaTeX error

relevante regel (of ±5 regels)

👉 Resultaat: jij hoeft nooit meer te “raden”.

Fase 1 — Syntax highlighting & UX (logische volgende stap)

← jij gaf dit zelf al aan

1.1 YAML syntax highlighting + regelnummers

Waarom: fouten zien vóór preview.

Aanpak (Tkinter-proof)

Gebruik tk.Text met:

line numbers canvas links

tags:

keys

strings

numbers

: en -

Highlight bij:

keypress

paste

focus loss

📌 Geen externe editor nodig.

Alternatief (sneller, minder werk):

tkinter.scrolledtext + alleen line numbers + error highlighting

syntax pas later verfijnen

1.2 LaTeX view verbeteren

Read-only toggle (checkbox)

Syntax highlight:

\begin

\item

\end

math $…$

👉 Vooral handig bij debuggen.

Fase 2 — AI-integratie professioneel maken

← jij neigt hier ook naar

2.1 AI-client abstractie (belangrijk!)

Je hebt dit impliciet al goed aangevoeld.

class BaseLLMClient:
    def generate_yaml(self, prompt: str) -> str:
        raise NotImplementedError


Implementaties:

OllamaClient

OpenAIClient

AnthropicClient

TogetherClient

UI kiest client + model.

2.2 API keys & providers

.env support

UI:

dropdown: provider

dropdown: model

api key veld (masked)

🔒 Sleutel nooit opslaan in YAML of repo.

2.3 Meerdere systeemprompts

Dit wordt goud voor didactiek

Systeemprompts:

“Strikt didactisch correct”

“Moeilijk / valkuilen”

“Diagnostische toets”

Opslag:

prompts/*.txt

UI:

dropdown → prompt selecteren

(later) editor

👉 Dit maakt AI stuurbaar i.p.v. gokken.

Fase 3 — Validatie & linting (kwaliteit omhoog)

Nu pas, omdat je basis moet kloppen.

3.1 YAML semantische checks

Niet alleen “syntactisch geldig”, maar:

grafiek zonder volgende vraag → waarschuwing

mode: math zonder $ → waarschuwing

leeg grafiek: → genegeerd + melding

vraag met antwoord → didactische hint

Output:

Waarschuwingen:
- Opgave 2, onderdeel b: grafiek zonder bijbehorende vraag

3.2 LaTeX sanity checks (light)

tel \begin / \end

check \item buiten enumerate (string-based)

check \( ... \) paren

Niet perfect, maar vroeg signaleren.

Fase 4 — Geschiedenis, iteraties & favorieten

Je hintte hier al subtiel op.

4.1 AI output history

elke AI-run → opslaan

back / forward

favoriet ⭐

4.2 Diff-view

verschil tussen:

vorige YAML

huidige YAML

Didactisch enorm sterk.

Fase 5 — Publicatie & toekomst

(alleen als je wilt)

CLI tool

Headless mode

Web-UI (FastAPI)

Export naar Magister / Word / PDF-bundel

🎯 Jouw logische volgende stap (advies)

Als ik puur kijk naar impact vs moeite:

1️⃣ Syntax highlighting + line numbers (Fase 1)
2️⃣ API-abstractie + off-site LLMs (Fase 2.1–2.2)
3️⃣ Betere error feedback (Fase 0.1)

Daarna pas:

prompts

linting

geschiedenis