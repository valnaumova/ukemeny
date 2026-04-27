# 🍽️ Ukemeny – Familien

En enkel webapp med ukentlig middagsmeny, handlekurv med direktelenker til Meny.no, og faste varer.

**Live:** [valnaumova.github.io/ukemeny](https://valnaumova.github.io/ukemeny/)

---

## Funksjoner

- **Middager** – 7 dagers meny med oppskriftslenker og ingredienser
- **Kalender-tilpasning** – travle dager får raskere retter (basert på Google Calendar)
- **Handlekurv** – alle ukehandel-varer med 🛒 direktelenke til Meny.no-søk
- **Faste varer** – staples merket ukentlig / annenhver uke / månedlig
- **Mobilvennlig** – fungerer på telefon, nettbrett og PC

---

## Oppdatere menyen

Hver uke genereres en ny `index.html` av Claude basert på:
- Ukens oppskrifter (fra meny.no, oda.no, matprat.no m.fl.)
- Google Calendar – sjekker hvilke dager som er travle (møter som slutter etter 16:00)
- Norske helligdager – fridag = mer tid = festligere mat

For å oppdatere:
1. Last opp ny `index.html` til dette repoet
2. GitHub Pages oppdaterer siden automatisk innen 1–2 minutter

---

## Teknisk

- Ren HTML/CSS/JS – ingen avhengigheter, ingen byggsteg
- Hostet gratis på GitHub Pages
- Fonter: [Fraunces](https://fonts.google.com/specimen/Fraunces) + [DM Sans](https://fonts.google.com/specimen/DM+Sans) via Google Fonts

---

## Struktur

```
ukemeny/
└── index.html   # Hele appen i én fil
└── README.md    # Denne filen
```
