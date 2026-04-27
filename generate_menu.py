#!/usr/bin/env python3
"""
Ukemeny generator – kjører hver lørdag kl. 10
Leser Google Calendar, kaller Claude API, genererer ny index.html
"""

import os
import json
import datetime
import anthropic
from google.oauth2 import service_account
from googleapiclient.discovery import build

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
GOOGLE_CREDENTIALS = os.environ["GOOGLE_CREDENTIALS"]
CALENDAR_ID = "valeriya.naumova@cognite.com"

FAMILY_PREFS = """
Familie: 2 voksne + 2 barn (nesten 2 år og 3,5 år). Norsk.
Middag kl. 17:00. Hjemme fra jobb kl. 16:00.

Regler for middagsplanlegging:
- Møter som slutter ETTER 16:00 Oslo-tid = sen dag = trenger rask rett (maks 20 min) ELLER forberedelse kvelden før
- OOO / ferie / fridag = mer tid = kan lage noe litt mer krevende
- Tom kjøleskap etter ferie = kun hyllevarer første dag
- Én suppedag, én fiskedag, én kyllingdag, én vegetardag, én taco/pizza-fredag per uke
- Lørdager og søndager er helgemiddager – kan ta litt lenger tid
- Barnevennlig, ingen allergier

Foretrukne oppskriftskilder:
- meny.no/oppskrifter
- oda.com/no/recipes
- matprat.no/oppskrifter
- tine.no/oppskrifter

Returnér KUN gyldig JSON, ingen forklaring, ingen markdown.
"""

MENY_LINKS = {
    "kyllingfilet": "https://meny.no/varer/kylling-og-fjaerkre/kylling/kyllingfilet",
    "laks": "https://meny.no/varer/fisk-og-skalldyr/laks",
    "kjøttdeig": "https://meny.no/varer/kjott/karbonader-og-kjoettdeig/kjoettdeig",
    "scampi": "https://meny.no/varer/fisk-og-skalldyr/reker-og-skalldyr",
    "halloumi": "https://meny.no/varer/meieri-ost-og-egg/ost/halloumi",
    "lettmelk": "https://meny.no/varer/meieri-ost-og-egg/melk/lettmelk",
    "fløte": "https://meny.no/varer/meieri-ost-og-egg/floete-og-romme/floete",
    "smør": "https://meny.no/varer/meieri-ost-og-egg/smor-og-margarin/smor",
    "egg": "https://meny.no/varer/meieri-ost-og-egg/egg",
    "parmesan": "https://meny.no/varer/meieri-ost-og-egg/ost/parmesan",
    "fetaost": "https://meny.no/varer/meieri-ost-og-egg/ost/fetaost",
    "cottage cheese": "https://meny.no/varer/meieri-ost-og-egg/cottage-cheese",
    "rømme": "https://meny.no/varer/meieri-ost-og-egg/floete-og-romme/romme",
    "sjampinjong": "https://meny.no/varer/frukt-og-gront/sopp/sjampinjong",
    "søtpotet": "https://meny.no/varer/frukt-og-gront/rotfrukter/sotpotet",
    "spinat": "https://meny.no/varer/frukt-og-gront/salat/spinat",
    "paprika": "https://meny.no/varer/frukt-og-gront/paprika/rod-paprika",
    "løk": "https://meny.no/varer/frukt-og-gront/lok",
    "hvitløk": "https://meny.no/varer/frukt-og-gront/lok/hvitlok",
    "gulrøtter": "https://meny.no/varer/frukt-og-gront/rotfrukter/gulrot",
    "poteter": "https://meny.no/varer/frukt-og-gront/poteter",
    "avokado": "https://meny.no/varer/frukt-og-gront/eksotisk-frukt/avokado",
    "cherrytomater": "https://meny.no/varer/frukt-og-gront/tomater/cherrytomater",
    "sitron": "https://meny.no/varer/frukt-og-gront/sitrusfrukter/sitron",
    "bananer": "https://meny.no/varer/frukt-og-gront/banan",
    "epler": "https://meny.no/varer/frukt-og-gront/epler",
    "appelsin": "https://meny.no/varer/frukt-og-gront/sitrusfrukter/appelsin",
    "mango": "https://meny.no/varer/frukt-og-gront/eksotisk-frukt/mango",
    "pasta": "https://meny.no/varer/kolonial/pasta",
    "ris": "https://meny.no/varer/kolonial/ris-og-gryn/ris",
    "quinoa": "https://meny.no/varer/kolonial/ris-og-gryn/quinoa",
    "hermetiske tomater": "https://meny.no/varer/kolonial/hermetikk/hermetiske-tomater",
    "kidneybønner": "https://meny.no/varer/kolonial/hermetikk/bonner",
    "mais": "https://meny.no/varer/kolonial/hermetikk/mais",
    "tacokrydder": "https://meny.no/varer/kolonial/krydder-og-smakstilsetninger/tacokrydder",
    "salsa": "https://meny.no/varer/kolonial/sauser-og-dressinger/salsa",
    "tortillachips": "https://meny.no/varer/snacks/chips/tortillachips",
    "buljong": "https://meny.no/varer/kolonial/suppe-og-buljong/buljong",
    "olivenolje": "https://meny.no/varer/kolonial/oljer-og-eddik/olivenolje",
    "brød": "https://meny.no/varer/bakervarer/brod/grovbrod",
    "knekkebrød": "https://meny.no/varer/bakervarer/knekkebroed",
    "syltetøy": "https://meny.no/varer/kolonial/syltetoy-og-paalegg/syltetoy",
    "brunost": "https://meny.no/varer/meieri-ost-og-egg/ost/brunost",
    "kaviar": "https://meny.no/varer/fisk-og-skalldyr/kaviar-og-rogn",
    "leverpostei": "https://meny.no/varer/paaleg/leverpostei",
    "appelsinjuice": "https://meny.no/varer/drikke/juice/appelsinjuice",
    "yoghurt": "https://meny.no/varer/meieri-ost-og-egg/yoghurt",
    "müsli": "https://meny.no/varer/kolonial/frokostblandinger/musli",
    "riskaker": "https://meny.no/varer/snacks/kjeks-og-riskaker/riskaker",
    "koljekaker": "https://meny.no/varer/fisk-og-skalldyr/fiskekaker-og-fiskeprodukter",
    "bleier": "https://meny.no/varer/baby-og-barn/bleier",
    "trusebleier": "https://meny.no/varer/baby-og-barn/bleier/trusebleier",
}

FIXED_ITEMS = [
    {"n": "Jordbærsyltetøy", "q": MENY_LINKS["syltetøy"], "f": "monthly"},
    {"n": "Bringebærsyltetøy", "q": MENY_LINKS["syltetøy"], "f": "monthly"},
    {"n": "Brunost G35", "q": MENY_LINKS["brunost"], "f": "biweekly"},
    {"n": "Kaviar tube", "q": MENY_LINKS["kaviar"], "f": "biweekly"},
    {"n": "Leverpostei", "q": MENY_LINKS["leverpostei"], "f": "biweekly"},
    {"n": "Appelsinjuice", "q": MENY_LINKS["appelsinjuice"], "f": "weekly"},
    {"n": "Yoghurt med frukt (barn)", "q": MENY_LINKS["yoghurt"], "f": "weekly"},
    {"n": "Müsli / havregryn", "q": MENY_LINKS["müsli"], "f": "weekly"},
    {"n": "Riskaker", "q": MENY_LINKS["riskaker"], "f": "biweekly"},
    {"n": "Koljekaker 95g × 2", "q": MENY_LINKS["koljekaker"], "f": "biweekly"},
    {"n": "Libero trusebleier str. 6", "q": MENY_LINKS["trusebleier"], "f": "monthly"},
    {"n": "Libero bleier str. 4", "q": MENY_LINKS["bleier"], "f": "monthly"},
]


def get_calendar_events():
    """Henter kalenderhendelser for neste uke (mandag–søndag) i Oslo-tid."""
    creds_info = json.loads(GOOGLE_CREDENTIALS)
    creds = service_account.Credentials.from_service_account_info(
        creds_info,
        scopes=["https://www.googleapis.com/auth/calendar.readonly"]
    )
    delegated = creds.with_subject(CALENDAR_ID)
    service = build("calendar", "v3", credentials=delegated)

    # Finn neste mandag
    today = datetime.date.today()
    days_until_monday = (7 - today.weekday()) % 7
    if days_until_monday == 0:
        days_until_monday = 7
    next_monday = today + datetime.timedelta(days=days_until_monday)
    next_sunday = next_monday + datetime.timedelta(days=6)

    time_min = datetime.datetime.combine(next_monday, datetime.time.min).isoformat() + "+02:00"
    time_max = datetime.datetime.combine(next_sunday, datetime.time(23, 59)).isoformat() + "+02:00"

    events_result = service.events().list(
        calendarId=CALENDAR_ID,
        timeMin=time_min,
        timeMax=time_max,
        singleEvents=True,
        orderBy="startTime",
        timeZone="Europe/Oslo"
    ).execute()

    events = events_result.get("items", [])

    # Bygg en enkel dagsoppsummering
    summary = {}
    for i in range(7):
        d = next_monday + datetime.timedelta(days=i)
        summary[d.isoformat()] = {"date": d, "events": [], "last_end": None, "is_ooo": False}

    for e in events:
        start = e.get("start", {})
        date_str = start.get("dateTime", start.get("date", ""))[:10]
        if date_str not in summary:
            continue
        day = summary[date_str]

        # Sjekk OOO
        if e.get("eventType") == "outOfOffice" or "out of office" in e.get("summary", "").lower():
            day["is_ooo"] = True

        # Finn sluttid i Oslo-tid
        end = e.get("end", {})
        end_str = end.get("dateTime", "")
        if end_str:
            # Parse og konverter til Oslo-tid (CEST = UTC+2 om sommeren)
            from datetime import timezone, timedelta
            dt = datetime.datetime.fromisoformat(end_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone(timedelta(hours=2)))
            oslo = dt.astimezone(timezone(timedelta(hours=2)))
            end_hour = oslo.hour + oslo.minute / 60

            if day["last_end"] is None or end_hour > day["last_end"]:
                day["last_end"] = end_hour

        day["events"].append(e.get("summary", ""))

    return summary, next_monday


def build_calendar_context(summary):
    """Bygger tekstbeskrivelse av uka for Claude."""
    lines = []
    weekdays = ["Mandag", "Tirsdag", "Onsdag", "Torsdag", "Fredag", "Lørdag", "Søndag"]
    for i, (date_str, day) in enumerate(sorted(summary.items())):
        d = day["date"]
        name = weekdays[i]
        date_fmt = d.strftime("%-d. %B")

        if day["is_ooo"]:
            status = "OOO / ferie"
        elif day["last_end"] and day["last_end"] > 16.0:
            status = f"Sen dag – siste møte slutter {day['last_end']:.0f}:{int((day['last_end'] % 1)*60):02d}"
        else:
            status = "Normal dag – fri fra 16:00"

        lines.append(f"{name} {date_fmt}: {status}")
        if day["events"]:
            lines.append(f"  Møter: {', '.join(day['events'][:4])}")

    return "\n".join(lines)


def generate_menu_with_claude(calendar_context, week_num, monday):
    """Kaller Claude API og får tilbake JSON med meny og handleliste."""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    prompt = f"""Du er en familiekokk som planlegger ukemeny for en norsk familie.

Familieprofil og regler:
{FAMILY_PREFS}

Kalender for uke {week_num} ({monday.strftime('%-d. %B')} – {(monday + datetime.timedelta(days=6)).strftime('%-d. %B')}):
{calendar_context}

Tilgjengelige Meny-lenker for handlevarer: {json.dumps(list(MENY_LINKS.keys()))}

Generer ukemeny og handleliste. Returner KUN dette JSON-formatet:

{{
  "summary": "Kort norsk oppsummering av uka og hva som påvirker middagsvalgene (2-3 setninger)",
  "days": [
    {{
      "abbr": "Man",
      "num": "5",
      "mon": "mai",
      "tag": "tag-poultry",
      "label": "Kylling",
      "cardCls": "",
      "calNote": "✅ Normal dag – fri fra 16:00",
      "calCls": "ok",
      "name": "Rettens navn på norsk",
      "time": "25 min · Beskrivelse",
      "link": "https://meny.no/oppskrifter/...",
      "ing": "Ingrediens 1, ingrediens 2, ingrediens 3",
      "prepNote": null
    }}
  ],
  "shopping": [
    {{ "category": "Kjøtt & fisk", "items": [
      {{ "n": "Kyllingfilet 700g", "key": "kyllingfilet", "f": "weekly" }}
    ]}}
  ]
}}

Regler for tag: tag-poultry (kylling), tag-fish (fisk), tag-veg (vegetar), tag-soup (suppe), tag-taco (taco/pizza), tag-weekend (helg), tag-holiday (fridag), tag-ooo (ferie/OOO)
Regler for cardCls: "" (normal), "late" (sent møte), "precook" (forberedt), "holiday" (fridag), "ooo" (ferie)
Regler for calCls: "ok" (grønn), "warn" (rød/advarsel), "precook" (oransje), "ooo" (lilla), "" (ingen)

For shopping.items.key: bruk en av disse nøklene: {list(MENY_LINKS.keys())}
Hvis ingen nøkkel passer, bruk den nærmeste. f-verdier: weekly, biweekly, monthly."""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )

    text = message.content[0].text.strip()
    # Fjern eventuelle markdown-blokker
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        text = text.rsplit("```", 1)[0]

    return json.loads(text)


def get_meny_url(key):
    return MENY_LINKS.get(key, f"https://meny.no/varer/vareutlistning?query={key}")


def build_html(data, week_num, monday):
    """Bygger komplett index.html fra JSON-data."""
    sunday = monday + datetime.timedelta(days=6)
    week_label = f"Uke {week_num} · {monday.strftime('%-d. %B')} – {sunday.strftime('%-d. %B')}"

    days_js = json.dumps(data["days"], ensure_ascii=False)
    summary_text = data["summary"]

    # Bygg handlekurv-HTML
    shop_html_parts = []
    for cat in data["shopping"]:
        items_js = []
        for item in cat["items"]:
            items_js.append({
                "n": item["n"],
                "q": get_meny_url(item.get("key", "")),
                "f": item.get("f", "weekly")
            })
        shop_html_parts.append({"name": cat["category"], "items": items_js})

    shop_js = json.dumps(shop_html_parts, ensure_ascii=False)
    fixed_js = json.dumps(FIXED_ITEMS, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="no">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Ukemeny – Familien</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,wght@0,300;0,400;0,600;1,300&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
<style>
  :root{{--cream:#FAF7F2;--paper:#F3EEE6;--ink:#1C1A17;--ink-muted:#6B6559;--ink-light:#A09890;--green:#2D5016;--green-bg:#EAF0E0;--orange:#C4521A;--orange-bg:#FAF0E8;--blue:#1A3A5C;--blue-bg:#E8EFF6;--amber:#8C5E00;--amber-bg:#FBF3E0;--red:#8B2020;--red-bg:#FCEBEB;--purple:#3C2A6B;--purple-bg:#EEEDFE;--border:rgba(28,26,23,0.1);--radius:12px;}}
  *{{box-sizing:border-box;margin:0;padding:0;}}
  body{{font-family:'DM Sans',sans-serif;background:var(--cream);color:var(--ink);min-height:100vh;}}
  header{{background:var(--ink);color:var(--cream);padding:2rem 1.5rem 1.5rem;}}
  .header-inner{{max-width:700px;margin:0 auto;}}
  .header-title{{font-family:'Fraunces',serif;font-size:clamp(2rem,6vw,2.8rem);font-weight:300;line-height:1.1;letter-spacing:-0.02em;}}
  .header-title em{{font-style:italic;color:rgba(255,255,255,0.45);}}
  .header-meta{{font-size:12px;color:rgba(255,255,255,0.45);margin-top:6px;}}
  .tab-bar{{display:flex;gap:4px;margin-top:1.5rem;flex-wrap:wrap;}}
  .tab-btn{{padding:7px 16px;border-radius:20px;border:0.5px solid rgba(255,255,255,0.2);background:transparent;color:rgba(255,255,255,0.55);font-family:'DM Sans',sans-serif;font-size:13px;font-weight:500;cursor:pointer;transition:all 0.15s;}}
  .tab-btn.active{{background:var(--cream);color:var(--ink);border-color:var(--cream);}}
  main{{max-width:700px;margin:0 auto;padding:1.5rem;}}
  .tab-panel{{display:none;}}.tab-panel.active{{display:block;}}
  .week-summary{{background:white;border:0.5px solid var(--border);border-radius:var(--radius);padding:1rem 1.25rem;margin-bottom:1.25rem;font-size:13px;line-height:1.9;color:var(--ink-muted);}}
  .week-summary strong{{color:var(--ink);}}
  .day-card{{background:white;border:0.5px solid var(--border);border-radius:var(--radius);margin-bottom:0.85rem;overflow:hidden;transition:box-shadow 0.2s;}}
  .day-card:hover{{box-shadow:0 4px 20px rgba(0,0,0,0.07);}}
  .day-card.late{{border-left:3px solid #E24B4A;border-radius:0 var(--radius) var(--radius) 0;}}
  .day-card.precook{{border-left:3px solid var(--amber);border-radius:0 var(--radius) var(--radius) 0;}}
  .day-card.holiday{{border-left:3px solid #1D9E75;border-radius:0 var(--radius) var(--radius) 0;}}
  .day-card.ooo{{border-left:3px solid #7F77DD;border-radius:0 var(--radius) var(--radius) 0;}}
  .card-top{{display:grid;grid-template-columns:68px 1fr auto;align-items:center;gap:1rem;padding:1.1rem 1.25rem;cursor:pointer;}}
  .day-col{{text-align:center;}}
  .day-abbr{{font-size:10px;font-weight:500;text-transform:uppercase;letter-spacing:0.08em;color:var(--ink-light);}}
  .day-num{{font-family:'Fraunces',serif;font-size:2rem;font-weight:300;line-height:1;color:var(--ink);}}
  .day-mon{{font-size:10px;color:var(--ink-light);}}
  .dish-tag{{display:inline-block;font-size:10px;font-weight:500;padding:2px 8px;border-radius:10px;margin-bottom:5px;text-transform:uppercase;letter-spacing:0.05em;}}
  .tag-poultry{{background:var(--purple-bg);color:var(--purple);}}
  .tag-fish{{background:var(--blue-bg);color:var(--blue);}}
  .tag-veg{{background:var(--green-bg);color:var(--green);}}
  .tag-soup{{background:var(--amber-bg);color:var(--amber);}}
  .tag-taco{{background:var(--orange-bg);color:var(--orange);}}
  .tag-weekend{{background:var(--paper);color:var(--ink-muted);}}
  .tag-holiday{{background:var(--green-bg);color:var(--green);}}
  .tag-ooo{{background:var(--purple-bg);color:var(--purple);}}
  .dish-name{{font-family:'Fraunces',serif;font-size:1.05rem;font-weight:400;line-height:1.3;color:var(--ink);}}
  .dish-time{{font-size:11px;color:var(--ink-light);margin-top:3px;}}
  .expand-icon{{font-size:16px;color:var(--ink-light);transition:transform 0.25s;}}
  .day-card.open .expand-icon{{transform:rotate(180deg);}}
  .card-body{{display:none;border-top:0.5px solid var(--border);padding:1rem 1.25rem;background:var(--paper);}}
  .day-card.open .card-body{{display:block;}}
  .cal-note{{font-size:12px;background:white;border-radius:8px;padding:6px 10px;margin-bottom:10px;border:0.5px solid var(--border);color:var(--ink-muted);line-height:1.6;}}
  .cal-note.warn{{border-color:rgba(226,75,74,0.3);background:var(--red-bg);color:var(--red);}}
  .cal-note.ok{{border-color:rgba(29,158,117,0.3);background:var(--green-bg);color:var(--green);}}
  .cal-note.precook{{border-color:rgba(140,94,0,0.3);background:var(--amber-bg);color:var(--amber);}}
  .cal-note.ooo{{border-color:rgba(127,119,221,0.3);background:var(--purple-bg);color:var(--purple);}}
  .ing-label{{font-size:10px;font-weight:500;text-transform:uppercase;letter-spacing:0.08em;color:var(--ink-light);margin-bottom:5px;}}
  .ing-list{{font-size:13px;color:var(--ink-muted);line-height:1.8;margin-bottom:1rem;}}
  .recipe-link{{display:inline-flex;align-items:center;gap:6px;font-size:12px;font-weight:500;color:var(--orange);text-decoration:none;border:0.5px solid currentColor;border-radius:20px;padding:5px 12px;transition:all 0.15s;}}
  .recipe-link:hover{{background:var(--orange);color:white;}}
  .legend{{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:1.25rem;}}
  .legend-item{{display:flex;align-items:center;gap:5px;font-size:11px;color:var(--ink-muted);}}
  .legend-dot{{width:10px;height:10px;border-radius:2px;flex-shrink:0;}}
  .shop-section{{margin-bottom:1.25rem;}}
  .section-title{{font-size:11px;font-weight:500;text-transform:uppercase;letter-spacing:0.1em;color:var(--ink-light);margin-bottom:8px;padding-left:2px;}}
  .shop-items{{background:white;border:0.5px solid var(--border);border-radius:var(--radius);overflow:hidden;}}
  .shop-item{{display:grid;grid-template-columns:28px 1fr auto auto;align-items:center;gap:8px;padding:9px 14px;border-bottom:0.5px solid var(--border);cursor:pointer;transition:background 0.1s;}}
  .shop-item:last-child{{border-bottom:none;}}
  .shop-item:hover{{background:var(--paper);}}
  .shop-item.checked{{opacity:0.4;}}
  .check-c{{width:18px;height:18px;border-radius:50%;border:1.5px solid var(--border);display:flex;align-items:center;justify-content:center;transition:all 0.15s;flex-shrink:0;}}
  .shop-item.checked .check-c{{background:var(--green);border-color:var(--green);}}
  .check-c svg{{display:none;}}
  .shop-item.checked .check-c svg{{display:block;}}
  .item-name{{font-size:13px;color:var(--ink);}}
  .shop-item.checked .item-name{{text-decoration:line-through;color:var(--ink-light);}}
  .freq-pill{{font-size:10px;font-weight:500;padding:2px 6px;border-radius:10px;white-space:nowrap;}}
  .freq-weekly{{background:var(--green-bg);color:var(--green);}}
  .freq-biweekly{{background:var(--purple-bg);color:var(--purple);}}
  .freq-monthly{{background:var(--amber-bg);color:var(--amber);}}
  .meny-btn{{display:inline-flex;align-items:center;gap:3px;font-size:11px;font-weight:500;color:var(--blue);background:var(--blue-bg);border-radius:7px;padding:3px 8px;text-decoration:none;white-space:nowrap;transition:all 0.15s;}}
  .meny-btn:hover{{background:var(--blue);color:white;}}
  .freq-legend{{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:1rem;}}
  footer{{text-align:center;padding:2rem 1rem;font-size:12px;color:var(--ink-light);}}
  footer a{{color:var(--orange);text-decoration:none;}}
  @media(max-width:480px){{.card-top{{grid-template-columns:50px 1fr auto;gap:0.75rem;}}.day-num{{font-size:1.6rem;}}}}
</style>
</head>
<body>
<header>
  <div class="header-inner">
    <div class="header-title">Uke&shy;meny<br><em>for familien</em></div>
    <div class="header-meta">{week_label}</div>
    <div class="tab-bar">
      <button class="tab-btn active" onclick="switchTab('menu',this)">Middager</button>
      <button class="tab-btn" onclick="switchTab('shop',this)">Handlekurv</button>
      <button class="tab-btn" onclick="switchTab('fixed',this)">Faste varer</button>
    </div>
  </div>
</header>
<main>
  <div class="tab-panel active" id="tab-menu">
    <div class="legend">
      <div class="legend-item"><div class="legend-dot" style="background:var(--green)"></div> Fri fra 16:00</div>
      <div class="legend-item"><div class="legend-dot" style="background:#E24B4A"></div> Sent møte – rask rett</div>
      <div class="legend-item"><div class="legend-dot" style="background:var(--amber)"></div> Forbered dagen før</div>
      <div class="legend-item"><div class="legend-dot" style="background:#7F77DD"></div> OOO / ferie</div>
      <div class="legend-item"><div class="legend-dot" style="background:#1D9E75"></div> Fridag</div>
    </div>
    <div class="week-summary">{summary_text}</div>
    <div id="days-container"></div>
  </div>
  <div class="tab-panel" id="tab-shop">
    <div class="freq-legend">
      <span class="freq-pill freq-weekly">Ukentlig</span>
      <span class="freq-pill freq-biweekly">Annenhver uke</span>
      <span class="freq-pill freq-monthly">Månedlig</span>
    </div>
    <div id="shop-container"></div>
  </div>
  <div class="tab-panel" id="tab-fixed">
    <div class="freq-legend">
      <span class="freq-pill freq-weekly">Ukentlig</span>
      <span class="freq-pill freq-biweekly">Annenhver uke</span>
      <span class="freq-pill freq-monthly">Månedlig</span>
    </div>
    <div id="fixed-container"></div>
  </div>
</main>
<footer>Sist oppdatert: {monday.strftime('%-d. %B %Y')} · <a href="https://meny.no/nettbutikk" target="_blank">Bestill på meny.no</a></footer>
<script>
const menu={days_js};
const shopCats={shop_js};
const fixedCats={fixed_js};
const freqLabel={{weekly:'Ukentlig',biweekly:'2 uker',monthly:'Månedlig'}};
const freqCls={{weekly:'freq-weekly',biweekly:'freq-biweekly',monthly:'freq-monthly'}};
const chk=`<svg width="10" height="8" viewBox="0 0 10 8" fill="none"><path d="M1 4L3.5 6.5L9 1" stroke="white" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>`;

const dc=document.getElementById('days-container');
menu.forEach((d,i)=>{{
  const cc=['day-card',d.cardCls].filter(Boolean).join(' ');
  const body=d.ing?`
    ${{d.prepNote?`<div class="cal-note precook">${{d.prepNote}}</div>`:''}}
    <div class="ing-label">Ingredienser</div>
    <div class="ing-list">${{d.ing}}</div>
    ${{d.link?`<a class="recipe-link" href="${{d.link}}" target="_blank">Åpne oppskrift →</a>`:''}}
  `:`<div style="font-size:13px;color:var(--ink-muted)">Ingen matlaging i dag – nyt!</div>`;
  dc.innerHTML+=`<div class="${{cc}}" id="card-${{i}}">
    <div class="card-top" onclick="toggleCard(${{i}})">
      <div class="day-col"><div class="day-abbr">${{d.abbr}}</div><div class="day-num">${{d.num}}</div><div class="day-mon">${{d.mon}}</div></div>
      <div><span class="dish-tag ${{d.tag}}">${{d.label}}</span><div class="dish-name">${{d.name}}</div><div class="dish-time">${{d.time}}</div></div>
      <div class="expand-icon">▾</div>
    </div>
    <div class="card-body">
      <div class="cal-note ${{d.calCls}}">${{d.calNote}}</div>
      ${{body}}
    </div>
  </div>`;
}});

function toggleCard(i){{document.getElementById('card-'+i).classList.toggle('open');}}

function renderShop(cats,cid){{
  const el=document.getElementById(cid);
  cats.forEach(cat=>{{
    const rows=cat.items.map((item,j)=>{{
      const id=`${{cid}}-${{j}}-${{cat.name.replace(/\\s/g,'')}}`;
      return `<div class="shop-item" id="${{id}}" onclick="toggleItem('${{id}}')">
        <div class="check-c">${{chk}}</div>
        <span class="item-name">${{item.n}}</span>
        <span class="freq-pill ${{freqCls[item.f]}}">${{freqLabel[item.f]}}</span>
        <a class="meny-btn" href="${{item.q}}" target="_blank" onclick="event.stopPropagation()">🛒 Meny</a>
      </div>`;
    }}).join('');
    el.innerHTML+=`<div class="shop-section"><div class="section-title">${{cat.name}}</div><div class="shop-items">${{rows}}</div></div>`;
  }});
}}

renderShop(shopCats,'shop-container');
renderShop(fixedCats,'fixed-container');
function toggleItem(id){{document.getElementById(id).classList.toggle('checked');}}
function switchTab(name,btn){{
  document.querySelectorAll('.tab-panel').forEach(p=>p.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(b=>b.classList.remove('active'));
  document.getElementById('tab-'+name).classList.add('active');
  btn.classList.add('active');
}}
</script>
</body>
</html>"""
    return html


def main():
    print("Henter kalenderdata...")
    summary, monday = get_calendar_events()
    calendar_context = build_calendar_context(summary)
    print(f"Kalender for uke fra {monday}:")
    print(calendar_context)

    week_num = monday.isocalendar()[1]

    print("\nKaller Claude API...")
    data = generate_menu_with_claude(calendar_context, week_num, monday)
    print(f"Generert meny med {len(data['days'])} dager")

    print("\nBygger HTML...")
    html = build_html(data, week_num, monday)

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ index.html oppdatert ({len(html)} tegn)")


if __name__ == "__main__":
    main()
