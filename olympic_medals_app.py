import pandas as pd
import plotly.express as px
import streamlit as st
import requests

# -----------------------------------------------------------
# Grundkonfiguration der Streamlit-App
# -----------------------------------------------------------
# page_title: Titel, der im Browser-Tab angezeigt wird
# layout="wide": breites Layout, damit Karte und Textfelder nebeneinander passen
# Dies ist der erste Aufruf, der vor allen anderen st.*-Befehlen stehen muss.
st.set_page_config(page_title="Olympische Medaillen – Europa", layout="wide")

# -----------------------------------------------------------
# 1. Datenbasis: Liste aller betrachteten europäischen Länder
# -----------------------------------------------------------
# Russland und die Türkei werden hier – wie in der Aufgabenstellung gefordert –
# als europäische Länder behandelt und daher in die Liste aufgenommen.
# Die Liste dient als Referenz für das Länder-Dropdown und die Basistabelle,
# damit auch Länder ohne Medaillen auf der Karte erscheinen.
EUROPA_LAENDER = [
    "Albania", "Andorra", "Armenia", "Austria", "Azerbaijan", "Belarus", "Belgium",
    "Bosnia and Herzegovina", "Bulgaria", "Croatia", "Cyprus", "Czech Republic",
    "Denmark", "Estonia", "Finland", "France", "Georgia", "Germany", "Great Britain",
    "Greece", "Hungary", "Iceland", "Ireland", "Italy", "Kosovo", "Latvia",
    "Liechtenstein", "Lithuania", "Luxembourg", "Malta", "Moldova", "Monaco",
    "Montenegro", "Netherlands", "North Macedonia", "Norway", "Poland", "Portugal",
    "Romania", "Russia", "San Marino", "Serbia", "Slovakia", "Slovenia", "Spain",
    "Sweden", "Switzerland", "Turkey", "Ukraine"
]

# -----------------------------------------------------------
# 2. Mapping von Ländernamen auf ISO‑3‑Ländercodes
# -----------------------------------------------------------
# Plotly und GeoJSON arbeiten intern mit dreistelligen ISO‑3‑Codes (DEU, FRA, ITA ...).
# Dieses Dictionary verbindet den englischen Ländernamen, wie er in der CSV steht,
# mit dem passenden ISO‑3‑Code. So können Medaillendaten und Kartengeometrie
# zuverlässig verknüpft werden, auch wenn die Schreibweisen leicht abweichen.
LAENDER_ZU_ISO3 = {
    "Albania": "ALB", "Andorra": "AND", "Armenia": "ARM", "Austria": "AUT",
    "Azerbaijan": "AZE", "Belarus": "BLR", "Belgium": "BEL",
    "Bosnia and Herzegovina": "BIH", "Bulgaria": "BGR", "Croatia": "HRV",
    "Cyprus": "CYP", "Czech Republic": "CZE", "Denmark": "DNK", "Estonia": "EST",
    "Finland": "FIN", "France": "FRA", "Georgia": "GEO", "Germany": "DEU",
    "Great Britain": "GBR", "Greece": "GRC", "Hungary": "HUN", "Iceland": "ISL",
    "Ireland": "IRL", "Italy": "ITA", "Kosovo": "XKX", "Latvia": "LVA",
    "Liechtenstein": "LIE", "Lithuania": "LTU", "Luxembourg": "LUX", "Malta": "MLT",
    "Moldova": "MDA", "Monaco": "MCO", "Montenegro": "MNE", "Netherlands": "NLD",
    "North Macedonia": "MKD", "Norway": "NOR", "Poland": "POL", "Portugal": "PRT",
    "Romania": "ROU", "Russia": "RUS", "San Marino": "SMR", "Serbia": "SRB",
    "Slovakia": "SVK", "Slovenia": "SVN", "Spain": "ESP", "Sweden": "SWE",
    "Switzerland": "CHE", "Turkey": "TUR", "Ukraine": "UKR"
}

# -----------------------------------------------------------
# 3. CSV mit Medaillendaten laden und vorbereiten
# -----------------------------------------------------------
# @st.cache_data sorgt dafür, dass das Ergebnis dieser Funktion nach dem ersten
# Aufruf im Arbeitsspeicher zwischengespeichert (gecacht) wird.
# Bei jedem weiteren Aufruf mit denselben Parametern wird das gespeicherte
# Ergebnis zurückgegeben, ohne die CSV erneut einzulesen. Das spart Ladezeit.
@st.cache_data
def lade_daten():
    # CSV-Datei mit allen Olympia-Jahren und europäischen Ländern einlesen.
    # Die Datei enthält die Spalten: year, country, gold, silver, bronze.
    df = pd.read_csv("olympic_medals_europe.csv")

    # Gesamtzahl der Medaillen pro Zeile berechnen und als neue Spalte speichern.
    # Dies erspart wiederholte Addition an anderen Stellen im Code.
    df["total"] = df["gold"] + df["silver"] + df["bronze"]

    # Sonderfall „ROC" (Russisches Olympisches Komitee) vereinheitlichen:
    # Bei den Spielen 2020 (Tokio) trat Russland wegen Dopingsperren als „ROC" an.
    # Damit Russland über alle Jahre hinweg einheitlich gezählt wird,
    # ersetzen wir „ROC" durch „Russia".
    df["country"] = df["country"].replace({"ROC": "Russia"})

    # Jeden Ländernamen in der CSV in den entsprechenden ISO‑3‑Code übersetzen.
    # Die neue Spalte „iso3" wird später genutzt, um Datenpunkte mit den
    # Kartenpolygonen zu verknüpfen. Länder, die nicht im Mapping stehen,
    # erhalten dabei automatisch NaN als Wert.
    df["iso3"] = df["country"].map(LAENDER_ZU_ISO3)

    return df

# -----------------------------------------------------------
# 4. GeoJSON mit Ländergrenzen Europas laden (Geodaten)
# -----------------------------------------------------------
# Quelle: GitHub-Projekt „map-of-europe" von leakyMirror.
# Der GeoJSON enthält für jedes europäische Land ein Polygon (Umriss)
# sowie Properties wie NAME und ISO3, die wir zur Verknüpfung nutzen.
@st.cache_data
def lade_geojson():
    url = (
        "https://raw.githubusercontent.com/leakyMirror/"
        "map-of-europe/master/GeoJSON/europe.geojson"
    )

    # GeoJSON von GitHub laden. timeout=30 verhindert, dass die App unbegrenzt wartet,
    # falls der Server nicht antwortet.
    antwort = requests.get(url, timeout=30)

    # raise_for_status() wirft eine Ausnahme, wenn der HTTP-Statuscode auf einen
    # Fehler hinweist (z. B. 404 Not Found oder 500 Server Error).
    antwort.raise_for_status()

    # Antwort als Python-Dictionary (JSON) parsen
    geojson = antwort.json()

    # Sicherstellen, dass in den Properties jedes Polygons sowohl der Ländername
    # als auch der ISO‑3‑Code vorhanden sind. Manche GeoJSON-Varianten verwenden
    # „NAME", andere „name" – deshalb prüfen wir beide Varianten.
    for feature in geojson["features"]:
        props = feature.get("properties", {})

        # Ländernamen aus den Properties auslesen (Groß- oder Kleinschreibung)
        name = props.get("NAME") or props.get("name")
        feature["properties"]["name"] = name

        # ISO‑3‑Code aus den Properties lesen; falls er fehlt, aus unserem
        # Mapping ergänzen, damit die Verknüpfung mit den Medaillendaten klappt.
        feature["properties"]["iso3"] = props.get("ISO3") or LAENDER_ZU_ISO3.get(name)

    return geojson

# -----------------------------------------------------------
# 5. Aggregation der Medaillendaten je nach Auswahl
# -----------------------------------------------------------
# Diese Funktion gibt immer einen DataFrame zurück, der pro Land eine Zeile
# mit summierten Medaillenzahlen enthält – entweder für ein bestimmtes Jahr
# oder für den gesamten Zeitraum 1996–2024.
def aggregiere_daten(df: pd.DataFrame, auswahl: str) -> pd.DataFrame:
    if auswahl == "Gesamt 1996–2024":
        # Alle Jahre zusammenfassen: Medaillen je Land über den gesamten Zeitraum summieren.
        # groupby fasst alle Zeilen mit gleichem Land zusammen; sum() addiert die Spalten.
        erg = df.groupby(["country", "iso3"], as_index=False)[
            ["gold", "silver", "bronze", "total"]
        ].sum()
    else:
        # Einzelnes Jahr: Zuerst nur die Zeilen des gewählten Jahres behalten.
        jahr = int(auswahl)  # Auswahl ist ein String, muss in int umgewandelt werden
        df_jahr = df[df["year"] == jahr].copy()

        # Dann je Land aggregieren (mehrere Einträge pro Land im gleichen Jahr
        # können z. B. durch ROC-Umbenennung entstehen).
        erg = df_jahr.groupby(["country", "iso3"], as_index=False)[
            ["gold", "silver", "bronze", "total"]
        ].sum()
    return erg

# -----------------------------------------------------------
# 6. Top‑3‑Länder bestimmen
# -----------------------------------------------------------
# Sortierung nach olympischer Rangfolge: Zuerst Gold, dann Silber, dann Bronze,
# dann Gesamtmedaillen. Bei Gleichstand wird alphabetisch nach Ländernamen sortiert,
# damit die Reihenfolge immer eindeutig und reproduzierbar ist.
def top3(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.sort_values(
            ["gold", "silver", "bronze", "total", "country"],
            ascending=[False, False, False, False, True],
        )
        .head(3)  # Nur die drei besten Länder zurückgeben
    )

# -----------------------------------------------------------
# 7. Textformat für die rechte Spalte (Top 3 / ausgewähltes Land)
# -----------------------------------------------------------
# Erzeugt aus einer Datenzeile (pd.Series) einen kompakten Anzeigetext
# mit Gesamt-, Gold-, Silber- und Bronzemedaillen.
# int()-Umwandlung verhindert, dass Zahlen mit Dezimalstellen angezeigt werden.
def formatiere_medailen_text(zeile: pd.Series) -> str:
    return (
        f"Gesamt: {int(zeile.total)} | "
        f"Gold: {int(zeile.gold)} | "
        f"Silber: {int(zeile.silver)} | "
        f"Bronze: {int(zeile.bronze)}"
    )

# -----------------------------------------------------------
# 8. Daten und GeoJSON laden (Initialisierung beim App-Start)
# -----------------------------------------------------------
# Beide Funktionen nutzen @st.cache_data, daher werden die Daten
# nur beim ersten Aufruf tatsächlich geladen und danach aus dem Cache geholt.
df = lade_daten()
geojson = lade_geojson()

# Alle verfügbaren Jahre aus den Daten ermitteln und sortieren.
# Das Jahr 2021 wird laut Aufgabenstellung nicht verwendet und daher gefiltert.
# (Die Tokio-Spiele fanden offiziell als „Tokyo 2020" im Jahr 2021 statt –
# in unseren Daten sind sie unter 2020 erfasst, 2021 ist ein Platzhalter.)
jahre = sorted(j for j in df["year"].unique() if j != 2021)

# Auswahloptionen für das Dropdown: „Gesamt" als erste Option, dann einzelne Jahre
auswahl_optionen = ["Gesamt 1996–2024"] + [str(j) for j in jahre]

# -----------------------------------------------------------
# 9. Benutzeroberfläche (Titel, Beschreibung, Auswahlfelder)
# -----------------------------------------------------------
# Seitentitel und erläuternde Bildunterschrift anzeigen
st.title("Olympische Medaillen – Europäische Länder")
st.caption(
    "Olympische Sommerspiele 1996–2024. "
    "Russland und Türkei werden hier als europäische Länder gezählt."
)

# Zwei nebeneinanderliegende Spalten für die beiden Auswahlfelder erstellen
spalte_links, spalte_rechts = st.columns(2)

with spalte_links:
    # Dropdown zur Auswahl des Jahres oder des Gesamtzeitraums.
    # index=0 setzt „Gesamt 1996–2024" als Standardauswahl (Startzustand laut Aufgabe).
    auswahl = st.selectbox("Jahr oder Gesamtzeitraum", auswahl_optionen, index=0)

with spalte_rechts:
    # Dropdown zur Auswahl eines bestimmten Landes.
    # Standardmäßig ist Deutschland vorausgewählt (Aufgabenpunkt h).
    alle_laender = sorted(EUROPA_LAENDER)  # alphabetisch sortierte Länderliste
    index_de = alle_laender.index("Germany") if "Germany" in alle_laender else 0
    ausgewaehltes_land = st.selectbox("Ausgewähltes Land", alle_laender, index=index_de)

# -----------------------------------------------------------
# 10. Daten gemäß aktueller Auswahl aufbereiten
# -----------------------------------------------------------
# Medaillen für das gewählte Jahr bzw. den Gesamtzeitraum zusammenfassen
sicht = aggregiere_daten(df, auswahl)

# Sicherstellen, dass alle europäischen Länder in der Tabelle vorkommen,
# auch wenn sie keine Medaillen gewonnen haben. Dazu wird zuerst eine
# vollständige Basistabelle aller Länder erstellt und per Left-Join mit
# den aggregierten Medaillendaten verbunden.
# → Länder ohne Medaillen erhalten NaN-Werte, die im nächsten Schritt durch 0 ersetzt werden.
basis = pd.DataFrame({"country": EUROPA_LAENDER})
basis["iso3"] = basis["country"].map(LAENDER_ZU_ISO3)
sicht = basis.merge(sicht, on=["country", "iso3"], how="left")

# NaN-Werte (Länder ohne Medaillen) durch 0 ersetzen und in Integer umwandeln,
# damit alle numerischen Spalten einheitlich verarbeitbar sind.
for spalte in ["gold", "silver", "bronze", "total"]:
    sicht[spalte] = sicht[spalte].fillna(0).astype(int)

# Für die Choropleth-Karte sollen Länder ohne Medaillen nicht eingefärbt werden.
# Dazu wird eine Hilfsspalte „gold_anzeige" erstellt, die für Länder mit 0 Medaillen
# den Wert None enthält. Plotly lässt diese Länder dann ungefärbt (weiß/grau).
sicht["gold_anzeige"] = sicht["gold"].where(sicht["total"] > 0)

# Tooltip-Spalten: Nur Länder mit mindestens einer Medaille sollen einen Tooltip
# anzeigen (Aufgabenpunkt g). None-Werte werden von Plotly ignoriert.
sicht["tooltip_land"] = sicht["country"].where(sicht["total"] > 0, None)
sicht["tooltip_gesamt"] = sicht["total"].where(sicht["total"] > 0, None)

# Vollständiger Tooltip-Text für das Hover-Label (Ländername + Gesamtmedaillen)
sicht["tooltip_text"] = sicht.apply(
    lambda z: f"{z['country']}: {int(z['total'])} Medaillen gesamt"
    if z["total"] > 0
    else "",
    axis=1,
)

# -----------------------------------------------------------
# 11. Choropleth-Karte mit Plotly erstellen
# -----------------------------------------------------------
# Eine Choropleth-Karte (Flächenkarte) färbt Polygone (hier: Länder) je nach
# einem numerischen Wert ein. Hier basiert die Färbung auf der Anzahl der Goldmedaillen,
# da diese laut Aufgabe die Platzierung im Medaillenspiegel bestimmt (Punkt f).
fig = px.choropleth(
    sicht,
    geojson=geojson,                   # GeoJSON mit Länderpolygonen
    locations="iso3",                  # Spalte im DataFrame mit den ISO‑3‑Codes
    featureidkey="properties.iso3",    # Schlüssel im GeoJSON, der die ISO‑3‑Codes enthält
    color="gold_anzeige",              # Einfärbung nach Goldmedaillen; None = ungefärbt
    color_continuous_scale="YlOrRd",   # Farbverlauf: Gelb (wenig) → Rot (viel)
    hover_name="tooltip_land",         # Ländername als Hauptüberschrift im Tooltip
    hover_data={
        "tooltip_gesamt": True,        # Gesamtmedaillen im Tooltip anzeigen
        "tooltip_text": False,         # Interner Hilfstext nicht im Tooltip anzeigen
        "gold": False,                 # Goldmedaillen separat nicht im Tooltip anzeigen
        "silver": False,               # Silbermedaillen nicht im Tooltip anzeigen
        "bronze": False,               # Bronzemedaillen nicht im Tooltip anzeigen
        "iso3": False,                 # ISO‑3‑Code nicht im Tooltip anzeigen
        "gold_anzeige": False,         # Hilfsspalte nicht im Tooltip anzeigen
    },
    labels={
        "tooltip_gesamt": "Medaillen gesamt",   # Beschriftung im Tooltip
        "gold_anzeige": "Goldmedaillen",         # Beschriftung der Farbskala
    },
)

# Darstellungseinstellungen der Karte anpassen:
# - Ländergrenzen in Weiß anzeigen (Aufgabenpunkt c)
# - Keine Küstenlinien (reduziert visuelle Unruhe)
# - Kartenausschnitt auf Europa begrenzen (Lat-/Lon-Bereich)
# - Meere/Wasser mit leichtem Blau hinterlegen
fig.update_geos(
    showcountries=True,         # Ländergrenzen einblenden
    countrycolor="white",       # Farbe der Ländergrenzen
    showcoastlines=False,       # Keine Küstenlinien
    visible=False,              # Basiskartenebene ausblenden (nur unsere Polygone)
    fitbounds="locations",      # Kartenausschnitt automatisch an die Daten anpassen
    lataxis_range=[30, 73],     # Breitengrad-Bereich (Südeuropa bis Nordkap)
    lonaxis_range=[-25, 55],    # Längengrad-Bereich (Island bis Kaukasus)
    bgcolor="#e6f2ff",          # Hintergrundfarbe für Wasser/Meere (helles Blau)
)

# Stil der Ländergrenzen auf der Karte anpassen:
# Dünne schwarze Linie um jedes Land für bessere Erkennbarkeit der Grenzen.
fig.update_traces(
    marker_line_color="black",   # Farbe der Länderumrandung
    marker_line_width=0.8,       # Breite der Länderumrandung in Pixeln
    selector=dict(type="choropleth"),
)

# Hover-Label-Stil: Dunkler Hintergrund mit weißer Schrift für gute Lesbarkeit
fig.update_traces(
    hoverlabel=dict(bgcolor="navy", font_color="white")
)

# Benutzerdefiniertes Hover-Template: Zeigt Ländername fett und Gesamtmedaillen.
# <extra></extra> entfernt die standardmäßige Plotly-Zusatzbox neben dem Tooltip.
fig.update_traces(
    hovertemplate="<b>%{hovertext}</b><br>Medaillen gesamt: %{customdata[0]}<extra></extra>"
)

# Randabstände der Grafik auf null setzen, damit die Karte den verfügbaren
# Platz vollständig ausfüllt. Farbbalken-Titel setzen (Aufgabenpunkt f).
fig.update_layout(
    margin={"r": 0, "t": 0, "l": 0, "b": 0},
    coloraxis_colorbar_title="Goldmedaillen",
)

# -----------------------------------------------------------
# 12. Seitenlayout: Karte links (größer), Textauswertung rechts (schmaler)
# -----------------------------------------------------------
# Verhältnis 3:1.6 gibt der Karte deutlich mehr Platz als dem Textbereich.
karte_spalte, text_spalte = st.columns([3, 1.6])

with karte_spalte:
    # Choropleth-Karte in voller Breite der linken Spalte anzeigen.
    # use_container_width=True passt die Grafik automatisch an die Spaltenbreite an.
    st.plotly_chart(fig, use_container_width=True)

with text_spalte:
    # --- Top 3 Länder ---
    # Zeigt die drei erfolgreichsten Länder mit allen Medaillenangaben (Aufgabenpunkt e).
    st.subheader("Top 3 Länder")
    top_drei = top3(sicht)
    for i, (_, zeile) in enumerate(top_drei.iterrows(), start=1):
        # Platznummer und Ländername fett hervorgehoben
        st.markdown(f"**{i}. {zeile.country}**")
        # Medaillendetails als kompakter Text
        st.write(formatiere_medailen_text(zeile))

    # --- Ausgewähltes Land ---
    # Zeigt die Medaillendetails für das im Dropdown gewählte Land (Aufgabenpunkt e).
    st.subheader("Ausgewähltes Land")

    # Zeile für das ausgewählte Land aus dem DataFrame herausfiltern.
    # iloc[0] nimmt die erste (und einzige) Zeile des gefilterten DataFrames.
    zeile_land = sicht[sicht["country"] == ausgewaehltes_land].iloc[0]
    st.markdown(f"**{ausgewaehltes_land}**")
    st.write(formatiere_medailen_text(zeile_land))

# -----------------------------------------------------------
# 13. Hinweise für den Nutzer am Ende der Seite
# -----------------------------------------------------------
st.markdown("### Hinweise")

# Erklärung zur Farbgebung und zu nicht eingefärbten Ländern
st.write(
    "Länder ohne Medaillen bleiben ungefärbt. "
    "Die Farbskala basiert auf der Anzahl der Goldmedaillen, "
    "da diese die Platzierung im Medaillenspiegel bestimmt."
)

# Hinweis zur technischen Umsetzung und zum Browsertest
st.write(
    "Die Anwendung wurde mit Streamlit und Plotly umgesetzt. "
    "Vor der Abgabe sollte sie in mindestens zwei verschiedenen Browsern "
    "(z. B. Chrome und Firefox) getestet werden."
)