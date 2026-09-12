import streamlit as st
from streamlit_gsheets import GSheetsConnection
import requests
import pandas as pd
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
import numpy as np

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Pylos Parlays | Sharp SK Command Center",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- RETRO-CYBER TERMINAL STYLES ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700;800&family=Plus+Jakarta+Sans:wght@500;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    .stApp {
        background: radial-gradient(circle at 15% 15%, #0f172a 0%, #070a12 85%);
        color: #f1f5f9;
    }
    section[data-testid="stSidebar"] {
        background-color: #0b0f19 !important;
        border-right: 1px solid #1e293b;
    }
    .terminal-title {
        font-weight: 800;
        font-size: 28px;
        letter-spacing: -0.5px;
        color: #ffffff;
    }
    .accent-pill {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: #ffffff;
        font-size: 13px;
        font-weight: 800;
        padding: 3px 10px;
        border-radius: 6px;
        display: inline-block;
        box-shadow: 0 0 12px rgba(16, 185, 129, 0.35);
        vertical-align: middle;
        margin-left: 6px;
    }
    .terminal-sub {
        color: #94a3b8;
        font-size: 13px;
        font-family: 'JetBrains Mono', monospace;
        margin-top: 4px;
        margin-bottom: 18px;
    }
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 12px;
        margin-bottom: 20px;
    }
    .stat-cube {
        background: rgba(15, 23, 42, 0.7);
        border: 1px solid #1e293b;
        border-radius: 12px;
        padding: 12px;
        text-align: center;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.4);
        backdrop-filter: blur(10px);
    }
    .stat-cube-val {
        font-family: 'JetBrains Mono', monospace;
        font-size: 24px;
        font-weight: 800;
        color: #38bdf8;
    }
    .stat-cube-lbl {
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        color: #64748b;
        margin-top: 2px;
    }
    .game-dossier {
        background: linear-gradient(145deg, rgba(15, 23, 42, 0.95) 0%, rgba(11, 15, 25, 0.98) 100%);
        border: 1px solid #334155;
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 22px;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5);
    }
    .dossier-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid #1e293b;
        padding-bottom: 12px;
        margin-bottom: 14px;
    }
    .matchup-headline {
        font-size: 20px;
        font-weight: 800;
        color: #ffffff;
        letter-spacing: -0.3px;
    }
    .matchup-records {
        font-size: 13px;
        color: #94a3b8;
        font-family: 'JetBrains Mono', monospace;
    }
    .weather-badge {
        background: rgba(56, 189, 248, 0.12);
        color: #38bdf8;
        border: 1px solid rgba(56, 189, 248, 0.3);
        border-radius: 6px;
        font-size: 12px;
        font-family: 'JetBrains Mono', monospace;
        padding: 4px 10px;
    }
    .tape-row {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 12px;
        margin-bottom: 14px;
    }
    .scout-card {
        background: #070a12;
        border: 1px solid #1e293b;
        border-radius: 8px;
        padding: 10px 14px;
    }
    .scout-title {
        font-size: 11px;
        text-transform: uppercase;
        color: #64748b;
        letter-spacing: 0.8px;
        margin-bottom: 4px;
    }
    .scout-name {
        font-size: 15px;
        font-weight: 800;
        color: #ffffff;
    }
    .scout-splits {
        font-size: 12px;
        font-family: 'JetBrains Mono', monospace;
        color: #38bdf8;
        margin-top: 2px;
    }
    .market-table {
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 14px;
        font-family: 'JetBrains Mono', monospace;
    }
    .market-table th {
        background: rgba(30, 41, 59, 0.6);
        color: #94a3b8;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        padding: 8px;
        text-align: center;
        border: 1px solid #1e293b;
    }
    .market-table td {
        padding: 8px 10px;
        border: 1px solid #1e293b;
        font-size: 13px;
        text-align: center;
    }
    .highlight-edge {
        color: #10b981;
        font-weight: 800;
    }
    .highlight-kelly {
        color: #38bdf8;
        font-weight: 700;
    }
    .intel-box {
        background: rgba(15, 23, 42, 0.8);
        border-left: 3px solid #10b981;
        border-radius: 6px;
        padding: 10px 14px;
        font-size: 12.5px;
        color: #cbd5e1;
        line-height: 1.5;
        margin-top: 10px;
    }
    .steam-badge-up {
        background: rgba(16, 185, 129, 0.15);
        color: #10b981;
        font-size: 11px;
        font-weight: 700;
        padding: 2px 6px;
        border-radius: 4px;
        border: 1px solid #10b981;
    }
    .steam-badge-down {
        background: rgba(239, 68, 68, 0.15);
        color: #f87171;
        font-size: 11px;
        font-weight: 700;
        padding: 2px 6px;
        border-radius: 4px;
        border: 1px solid #ef4444;
    }
    .steam-badge-flat {
        background: rgba(148, 163, 184, 0.15);
        color: #94a3b8;
        font-size: 11px;
        font-weight: 700;
        padding: 2px 6px;
        border-radius: 4px;
        border: 1px solid #475569;
    }
</style>
""", unsafe_allow_html=True)

# --- GLOBAL CONFIG & CONSTANTS ---
ODDS_API_KEY = st.secrets.get("ODDS_API_KEY", "")
BASE_URL = "https://api.the-odds-api.com/v4/sports"
conn = st.connection("gsheets", type=GSheetsConnection)
LOCAL_TZ = ZoneInfo("America/Regina")
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/12KN2zJqQUWxmbEznc-rBp-4gJuYwHMWvBJ6NnN2Pa-g/edit?usp=drivesdk"

SHARP_BENCHMARKS = ["pinnacle", "betfair_ex_eu", "betonlineag", "bookmaker"]

SPORT_PROPS_MAP = {
    "baseball_mlb": ["pitcher_strikeouts", "batter_home_runs", "batter_hits"],
    "americanfootball_nfl": ["player_pass_yds", "player_pass_tds", "player_rush_yds", "player_anytime_td"],
    "basketball_nba": ["player_points", "player_rebounds", "player_assists"],
    "icehockey_nhl": ["player_points", "player_shots_on_goal"]
}

INDOOR_VENUES = {
    "Detroit Lions": "Dome (Ford Field)", "New Orleans Saints": "Dome (Caesars Superdome)",
    "Minnesota Vikings": "Dome (U.S. Bank Stadium)", "Las Vegas Raiders": "Dome (Allegiant Stadium)",
    "Los Angeles Chargers": "Canopy (SoFi Stadium)", "Los Angeles Rams": "Canopy (SoFi Stadium)",
    "Tampa Bay Rays": "Dome (Tropicana Field)", "Atlanta Falcons": "Retractable Roof (Mercedes-Benz)",
    "Houston Texans": "Retractable Roof (NRG Stadium)", "Indianapolis Colts": "Retractable Roof (Lucas Oil)",
    "Dallas Cowboys": "Retractable Roof (AT&T Stadium)", "Arizona Cardinals": "Retractable Roof (State Farm)",
    "Miami Marlins": "Retractable Roof (loanDepot park)", "Toronto Blue Jays": "Retractable Roof (Rogers Centre)",
    "Milwaukee Brewers": "Retractable Roof (AmFam Field)", "Houston Astros": "Retractable Roof (Minute Maid)",
    "Texas Rangers": "Retractable Roof (Globe Life)", "Arizona Diamondbacks": "Retractable Roof (Chase Field)",
    "Seattle Mariners": "Retractable Roof (T-Mobile Park)"
}

STADIUM_COORDS = {
    "Miami Marlins": (25.778, -80.220), "Chicago Cubs": (41.948, -87.655),
    "Los Angeles Dodgers": (34.073, -118.240), "Arizona Diamondbacks": (33.445, -112.066),
    "New York Yankees": (40.829, -73.926), "Boston Red Sox": (42.346, -71.097),
    "Toronto Blue Jays": (43.641, -79.389), "Detroit Tigers": (42.339, -83.048),
    "Houston Astros": (29.757, -95.355), "New York Mets": (40.757, -73.845),
    "Philadelphia Phillies": (39.906, -75.166), "Atlanta Braves": (33.890, -84.468),
    "Seattle Mariners": (47.591, -122.332), "Detroit Lions": (42.340, -83.045),
    "New Orleans Saints": (29.951, -90.081), "Kansas City Chiefs": (39.048, -94.483),
    "Arizona Cardinals": (33.527, -112.262), "Los Angeles Chargers": (33.953, -118.338),
    "Minnesota Vikings": (44.973, -93.257), "Green Bay Packers": (44.501, -88.062)
}

# --- MATHEMATICAL ENGINES ---
def decimal_to_american(dec: float) -> str:
    if dec is None or dec <= 1.0:
        return "---"
    if dec >= 2.0:
        return f"+{int(round((dec - 1.0) * 100))}"
    return f"{int(round(-100 / (dec - 1.0)))}"

def american_to_decimal(us_str: str) -> float:
    try:
        cleaned = str(us_str).replace("+", "").strip()
        val = float(cleaned)
        if val == 0:
            return 1.909
        if val > 0:
            return round((val / 100.0) + 1.0, 3)
        return round((100.0 / abs(val)) + 1.0, 3)
    except Exception:
        return 1.909

def power_devig(raw_probs: list) -> list:
    if not raw_probs or sum(raw_probs) <= 0:
        return []
    total_raw = sum(raw_probs)
    if abs(total_raw - 1.0) < 0.0001:
        return raw_probs
    low, high = 0.01, 15.0
    for _ in range(35):
        mid = (low + high) / 2.0
        val = sum(p ** mid for p in raw_probs)
        if val > 1.0:
            low = mid
        else:
            high = mid
    k = (low + high) / 2.0
    adjusted = [p ** k for p in raw_probs]
    norm_sum = sum(adjusted)
    return [p / norm_sum for p in adjusted] if norm_sum > 0 else [p / total_raw for p in raw_probs]

def calculate_kelly(dec_odds: float, win_prob: float, bankroll: float, fraction: float = 0.25) -> tuple[float, float]:
    if dec_odds <= 1.0 or win_prob <= 0.0 or win_prob >= 1.0:
        return 0.0, 0.0
    b = dec_odds - 1.0
    q = 1.0 - win_prob
    full_k = (b * win_prob - q) / b
    if full_k <= 0:
        return 0.0, 0.0
    frac_k = full_k * fraction
    suggested_stake = round(bankroll * frac_k, 2)
    return round(frac_k * 100, 2), suggested_stake

# --- FREE SCOUTING INTEL & WEATHER ENGINES ---
@st.cache_data(ttl=7200, show_spinner=False)
def fetch_weather(home_team: str):
    if home_team in INDOOR_VENUES:
        return f"🏟️ {INDOOR_VENUES[home_team]} | 21°C Controlled"
    coords = STADIUM_COORDS.get(home_team, (41.878, -87.629))
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={coords[0]}&longitude={coords[1]}&current_weather=true"
        r = requests.get(url, timeout=5).json()
        cw = r.get("current_weather", {})
        temp_c = cw.get("temperature", 20)
        wind_kmh = cw.get("windspeed", 10)
        wind_dir = cw.get("winddirection", 0)
        dirs = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        wind_str = dirs[int((wind_dir + 22.5) % 360 / 45)]
        return f"{temp_c:.0f}°C | 💨 {wind_kmh:.0f} km/h {wind_str}"
    except Exception:
        return "Normal Outdoor Conditions"

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_mlb_deep_intel(date_str: str):
    try:
        url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={date_str}&hydrate=probablePitcher(stats(type=season)),team(standings)"
        res = requests.get(url, timeout=8).json()
        intel_map = {}
        for d in res.get("dates", []):
            for g in d.get("games", []):
                away = g.get("teams", {}).get("away", {})
                home = g.get("teams", {}).get("home", {})
                away_name = away.get("team", {}).get("name", "")
                home_name = home.get("team", {}).get("name", "")

                away_rec = f"{away.get('leagueRecord', {}).get('wins', 0)}-{away.get('leagueRecord', {}).get('losses', 0)}"
                home_rec = f"{home.get('leagueRecord', {}).get('wins', 0)}-{home.get('leagueRecord', {}).get('losses', 0)}"

                away_p = away.get("probablePitcher", {})
                away_p_name = away_p.get("fullName", "TBD")
                away_p_hand = away_p.get("pitchHand", {}).get("code", "R")
                away_p_splits = "0-0 | -.-- ERA"
                if "stats" in away_p and away_p["stats"]:
                    splits = away_p["stats"][0].get("splits", [{}])[0].get("stat", {})
                    w, l = splits.get("wins", 0), splits.get("losses", 0)
                    era = splits.get("era", "-.--")
                    whip = splits.get("whip", "-.--")
                    so = splits.get("strikeOuts", 0)
                    away_p_splits = f"({w}-{l}) | {era} ERA | {whip} WHIP | {so} K"

                home_p = home.get("probablePitcher", {})
                home_p_name = home_p.get("fullName", "TBD")
                home_p_hand = home_p.get("pitchHand", {}).get("code", "R")
                home_p_splits = "0-0 | -.-- ERA"
                if "stats" in home_p and home_p["stats"]:
                    splits = home_p["stats"][0].get("splits", [{}])[0].get("stat", {})
                    w, l = splits.get("wins", 0), splits.get("losses", 0)
                    era = splits.get("era", "-.--")
                    whip = splits.get("whip", "-.--")
                    so = splits.get("strikeOuts", 0)
                    home_p_splits = f"({w}-{l}) | {era} ERA | {whip} WHIP | {so} K"

                intel_map[f"{away_name} @ {home_name}"] = {
                    "away_rec": away_rec,
                    "home_rec": home_rec,
                    "away_p_name": away_p_name,
                    "away_p_hand": away_p_hand,
                    "away_p_splits": away_p_splits,
                    "home_p_name": home_p_name,
                    "home_p_hand": home_p_hand,
                    "home_p_splits": home_p_splits,
                    "venue": g.get("venue", {}).get("name", "Stadium")
                }
        return intel_map
    except Exception:
        return {}

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_espn_sport_intel(sport_slug: str):
    try:
        url = f"https://site.api.espn.com/apis/site/v2/sports/{sport_slug}/scoreboard"
        res = requests.get(url, timeout=8).json()
        stats_map = {}
        for ev in res.get("events", []):
            comp = ev.get("competitions", [{}])[0]
            competitors = comp.get("competitors", [])
            if len(competitors) < 2:
                continue
            home = next((c for c in competitors if c.get("homeAway") == "home"), {})
            away = next((c for c in competitors if c.get("homeAway") == "away"), {})

            h_name = home.get("team", {}).get("displayName", "")
            a_name = away.get("team", {}).get("displayName", "")
            h_rec = home.get("records", [{}])[0].get("summary", "--")
            a_rec = away.get("records", [{}])[0].get("summary", "--")

            notes = [headline.get("description", "") for headline in comp.get("notes", [])]
            headline_str = notes[0] if notes else "Conference Matchup"

            stats_map[f"{a_name} @ {h_name}"] = {
                "away_rec": a_rec,
                "home_rec": h_rec,
                "headline": headline_str,
                "venue": comp.get("venue", {}).get("fullName", "Stadium")
            }
        return stats_map
    except Exception:
        return {}

def fetch_events_and_odds(sport_key: str, markets_list: list[str]):
    url = f"{BASE_URL}/{sport_key}/odds"
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "ca,eu",
        "markets": ",".join(markets_list),
        "oddsFormat": "decimal",
    }
    res = requests.get(url, params=params, timeout=14)
    res.raise_for_status()
    return res.json(), res.headers.get("x-requests-remaining", "N/A"), res.headers.get("x-requests-used", "N/A")

# --- INITIALIZE PERSISTENT STATE ---
if "api_rem" not in st.session_state:
    st.session_state.api_rem = "---"
if "api_used" not in st.session_state:
    st.session_state.api_used = "---"
if "dossiers" not in st.session_state:
    st.session_state.dossiers = []
if "raw_events" not in st.session_state:
    st.session_state.raw_events = []
if "odds_history" not in st.session_state:
    st.session_state.odds_history = {}

# --- SIDEBAR CONTROLS ---
st.sidebar.markdown("<h3 style='color:#fff;'>⚡ PYLOS TERMINAL</h3>", unsafe_allow_html=True)
st.sidebar.caption("Benchmark: **Pinnacle / Sharp Consensus** | Target: **PlayNow SK**")

selected_sport_label = st.sidebar.selectbox("Sport Slate", ["⚾ MLB Baseball", "🏈 NFL Football", "🏀 NBA Basketball", "🏒 NHL Hockey"], key="sport_slate_select")
sport_map = {
    "⚾ MLB Baseball": "baseball_mlb",
    "🏈 NFL Football": "americanfootball_nfl",
    "🏀 NBA Basketball": "basketball_nba",
    "🏒 NHL Hockey": "icehockey_nhl"
}
sport_key = sport_map[selected_sport_label]

market_scope = st.sidebar.radio(
    "Market Scope",
    ["Team Markets Only", "Player and Team Props"],
    help="Team: Mainlines only (H2H, Spread, Total). Player & Team: Adds strikeouts, hits, yards, points, etc.",
    key="market_scope_radio"
)

now_local = datetime.now(LOCAL_TZ)
tomorrow_local = (now_local + timedelta(days=1)).date()
day_after_local = (now_local + timedelta(days=2)).date()

date_filter_mode = st.sidebar.selectbox(
    "Game Timeframe",
    [
        "Upcoming 24 Hours",
        f"Tomorrow ({tomorrow_local.strftime('%b %d')})",
        f"Day After Tomorrow ({day_after_local.strftime('%b %d')})",
        "Pick Specific Date (Calendar)"
    ],
    key="timeframe_select"
)

chosen_calendar_date = None
if date_filter_mode == "Pick Specific Date (Calendar)":
    chosen_calendar_date = st.sidebar.date_input("Select Date", value=now_local.date(), key="cal_date_picker")

st.sidebar.markdown("---")
st.sidebar.markdown("**Bankroll & Kelly Sizing**")
bankroll = st.sidebar.number_input("Bankroll ($ CAD)", min_value=10.0, value=1000.0, step=50.0, key="bankroll_input")
kelly_fraction_label = st.sidebar.selectbox("Kelly Risk Tier", ["Quarter Kelly (0.25) - Sharp Std", "Half Kelly (0.50) - Aggressive", "Full Kelly (1.00) - Theoretical Max"], key="kelly_fraction_select")
kelly_fraction = 0.25 if "Quarter" in kelly_fraction_label else (0.50 if "Half" in kelly_fraction_label else 1.0)

col_b1, col_b2 = st.sidebar.columns(2)
run_scan = col_b1.button("⚡ Scan Board", type="primary", key="scan_btn")
recalc_only = col_b2.button("🔄 Re-Analyze", key="recalc_btn")

# --- STATS SUMMARY BAR ---
st.markdown("<div class='terminal-title'>⚡ PYLOS PARLAYS <span class='accent-pill'>SHARP COMMAND</span></div>", unsafe_allow_html=True)
st.markdown("<div class='terminal-sub'>POWER DEVIGGED ➔ KELLY CRITERION ➔ DEEP SCOUTING INTEL ➔ SASKATCHEWAN TERMINAL</div>", unsafe_allow_html=True)

st.markdown(f"""
<div class='metric-grid'>
    <div class='stat-cube'>
        <div class='stat-cube-val'>{st.session_state.api_rem}</div>
        <div class='stat-cube-lbl'>API Credits Left</div>
    </div>
    <div class='stat-cube'>
        <div class='stat-cube-val'>{st.session_state.api_used}</div>
        <div class='stat-cube-lbl'>Credits Consumed</div>
    </div>
    <div class='stat-cube'>
        <div class='stat-cube-val'>{len(st.session_state.dossiers)}</div>
        <div class='stat-cube-lbl'>Active Games Parsed</div>
    </div>
    <div class='stat-cube'>
        <div class='stat-cube-val'>${bankroll:,.0f}</div>
        <div class='stat-cube-lbl'>Bankroll (CAD)</div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- SCANNING & CALCULATION ENGINE ---
if run_scan:
    try:
        active_markets = ["h2h", "spreads", "totals"]
        if market_scope == "Player and Team Props":
            active_markets.extend(SPORT_PROPS_MAP.get(sport_key, []))

        with st.spinner("Calling API for live bookmaker lines & prop markets..."):
            raw_data, rem, used = fetch_events_and_odds(sport_key, active_markets)
            st.session_state.raw_events = raw_data
            st.session_state.api_rem = rem
            st.session_state.api_used = used
    except Exception as ex:
        st.error(f"API Connection Failure: {ex}")

if run_scan or (recalc_only and st.session_state.raw_events):
    try:
        with st.spinner("Devigging markets, pulling scouting splits, and running Kelly calculations..."):
            target_date_str = now_local.strftime("%Y-%m-%d")
            if "Tomorrow" in date_filter_mode and "Day After" not in date_filter_mode:
                target_date_str = tomorrow_local.strftime("%Y-%m-%d")
            elif "Day After Tomorrow" in date_filter_mode:
                target_date_str = day_after_local.strftime("%Y-%m-%d")
            elif date_filter_mode == "Pick Specific Date (Calendar)" and chosen_calendar_date:
                target_date_str = chosen_calendar_date.strftime("%Y-%m-%d")

            # Ingest free external intel depending on sport
            if "baseball" in sport_key:
                intel_map = fetch_mlb_deep_intel(target_date_str)
            elif "americanfootball" in sport_key:
                intel_map = fetch_espn_sport_intel("football/nfl")
            elif "basketball" in sport_key:
                intel_map = fetch_espn_sport_intel("basketball/nba")
            elif "hockey" in sport_key:
                intel_map = fetch_espn_sport_intel("hockey/nhl")
            else:
                intel_map = {}

            compiled = []

            for ev in st.session_state.raw_events:
                commence_raw = ev.get("commence_time", "")
                if commence_raw:
                    dt = datetime.fromisoformat(commence_raw.replace("Z", "+00:00")).astimezone(LOCAL_TZ)
                    if dt <= now_local:
                        continue
                    if date_filter_mode == "Upcoming 24 Hours" and dt > (now_local + timedelta(hours=24)):
                        continue
                    elif "Tomorrow" in date_filter_mode and "Day After" not in date_filter_mode and dt.date() != tomorrow_local:
                        continue
                    elif "Day After Tomorrow" in date_filter_mode and dt.date() != day_after_local:
                        continue
                    elif date_filter_mode == "Pick Specific Date (Calendar)" and dt.date() != chosen_calendar_date:
                        continue
                else:
                    continue

                away_team = ev.get("away_team", "Away")
                home_team = ev.get("home_team", "Home")
                matchup = f"{away_team} @ {home_team}"
                formatted_time = dt.strftime("%b %d - %I:%M %p")

                # Match intel with fallback
                game_intel = intel_map.get(matchup, {
                    "away_rec": "--", "home_rec": "--",
                    "away_p_name": "TBD", "away_p_hand": "R", "away_p_splits": "No starts recorded",
                    "home_p_name": "TBD", "home_p_hand": "R", "home_p_splits": "No starts recorded",
                    "headline": "Active Slate", "venue": f"{home_team} Stadium"
                })
                weather_info = fetch_weather(home_team)

                market_probs = {}
                playnow_lines = {}
                props_data = []

                for bm in ev.get("bookmakers", []):
                    bm_k = bm.get("key", "").lower()
                    is_sharp = any(k in bm_k for k in SHARP_BENCHMARKS)

                    for m in bm.get("markets", []):
                        m_key = m.get("key")
                        outcomes = m.get("outcomes", [])
                        valid_outcomes = [o for o in outcomes if o.get("price", 0) > 1.0]

                        if len(valid_outcomes) >= 2:
                            raw_p_list = [1.0 / o["price"] for o in valid_outcomes]
                            devigged = power_devig(raw_p_list)

                            for idx, o in enumerate(valid_outcomes):
                                player_desc = o.get("description", "")
                                ident = f"{m_key}_{player_desc}_{o['name']}_{o.get('point', '')}"

                                if is_sharp and idx < len(devigged):
                                    if ident not in market_probs:
                                        market_probs[ident] = []
                                    market_probs[ident].append(devigged[idx])

                                if "playnow" in bm_k:
                                    old_price = st.session_state.odds_history.get(ident, o["price"])
                                    if o["price"] > old_price:
                                        velocity = "▲ DRIFT"
                                    elif o["price"] < old_price:
                                        velocity = "▼ STEAM"
                                    else:
                                        velocity = "◼ STABLE"
                                    st.session_state.odds_history[ident] = o["price"]

                                    line_dict = {
                                        "name": o["name"],
                                        "description": player_desc,
                                        "point": o.get("point", None),
                                        "price": o["price"],
                                        "market": m_key,
                                        "velocity": velocity,
                                        "ident": ident
                                    }

                                    if m_key in ["h2h", "spreads", "totals"]:
                                        playnow_lines[ident] = line_dict
                                    else:
                                        props_data.append(line_dict)

                compiled.append({
                    "id": ev.get("id", matchup),
                    "matchup": matchup,
                    "away_team": away_team,
                    "home_team": home_team,
                    "time": formatted_time,
                    "intel": game_intel,
                    "weather": weather_info,
                    "playnow": playnow_lines,
                    "sharp_probs": market_probs,
                    "props": props_data
                })

            st.session_state.dossiers = compiled
            if compiled:
                st.success(f"Built {len(compiled)} Complete Dossiers ({market_scope})!")
            else:
                st.info("No active games matched your selected schedule.")
    except Exception as ex:
        st.error(f"Processing error: {ex}")

# --- TABS: DOSSIERS & PARLAYS ---
tab_dossiers, tab_parlays = st.tabs(["📊 Game Intelligence Dossiers", "⚡ Correlation-Safe Parlay Architect"])

with tab_dossiers:
    if st.session_state.dossiers:
        is_mlb = "baseball" in sport_key
        is_nfl = "americanfootball" in sport_key
        is_nba = "basketball" in sport_key
        is_nhl = "hockey" in sport_key
        spread_label = "Run Line" if is_mlb else ("Puck Line" if is_nhl else "Point Spread")

        for idx_g, g in enumerate(st.session_state.dossiers):
            intel = g["intel"]
            p_lines = g["playnow"]
            s_probs = g["sharp_probs"]

            def get_line_data(m_key, side_name):
                for k, val in p_lines.items():
                    if k.startswith(m_key) and side_name in val["name"]:
                        dec = val["price"]
                        prob_list = s_probs.get(k, [])
                        fair_p = float(np.mean(prob_list)) if prob_list else (1.0 / dec)
                        edge = ((dec * fair_p) - 1.0) * 100
                        pt_str = f" ({val['point']:+})" if val['point'] is not None else ""
                        vel = val.get("velocity", "◼ STABLE")
                        badge_class = "steam-badge-up" if "STEAM" in vel else ("steam-badge-down" if "DRIFT" in vel else "steam-badge-flat")

                        k_pct, k_stake = calculate_kelly(dec, fair_p, bankroll, kelly_fraction)
                        kelly_str = f"${k_stake:.2f}" if k_stake > 0 else "---"

                        return {
                            "odds": decimal_to_american(dec),
                            "prob": f"{fair_p*100:.1f}%",
                            "edge": f"+{edge:.1f}%" if edge >= 0 else f"{edge:.1f}%",
                            "point": pt_str,
                            "raw_prob": fair_p * 100,
                            "kelly": kelly_str,
                            "vel_html": f"<span class='{badge_class}'>{vel}</span>"
                        }
                return {"odds": "---", "prob": "---", "edge": "---", "point": "", "raw_prob": 0, "kelly": "---", "vel_html": ""}

            away_ml = get_line_data("h2h", g["away_team"])
            home_ml = get_line_data("h2h", g["home_team"])
            away_spread = get_line_data("spreads", g["away_team"])
            home_spread = get_line_data("spreads", g["home_team"])
            over_tot = get_line_data("totals", "Over")
            under_tot = get_line_data("totals", "Under")

            top_play = "No Value Identified"
            top_prob = 0
            if home_ml["raw_prob"] > top_prob:
                top_prob = home_ml["raw_prob"]
                top_play = f"Back <b>{g['home_team']} ML</b> (Sharp Prob: {home_ml['prob']} | Kelly: {home_ml['kelly']})"
            if away_ml["raw_prob"] > top_prob:
                top_prob = away_ml["raw_prob"]
                top_play = f"Back <b>{g['away_team']} ML</b> (Sharp Prob: {away_ml['prob']} | Kelly: {away_ml['kelly']})"

            # Sport-specific Scouting Cards
            if is_mlb:
                tape_row_html = f"""<div class="tape-row">
<div class="scout-card">
    <div class="scout-title">Away Starter ({intel.get('away_p_hand', 'R')}HP)</div>
    <div class="scout-name">⚾ {intel.get('away_p_name', 'TBD')}</div>
    <div class="scout-splits">{intel.get('away_p_splits', '0-0 | -.-- ERA')}</div>
</div>
<div class="scout-card">
    <div class="scout-title">Home Starter ({intel.get('home_p_hand', 'R')}HP)</div>
    <div class="scout-name">⚾ {intel.get('home_p_name', 'TBD')}</div>
    <div class="scout-splits">{intel.get('home_p_splits', '0-0 | -.-- ERA')}</div>
</div>
</div>"""
                context_summary = f"Starting Pitchers: <b>{intel.get('away_p_name', 'TBD')} vs {intel.get('home_p_name', 'TBD')}</b>. Stadium conditions: <b>{g['weather']}</b>."
            elif is_nfl:
                tape_row_html = f"""<div class="tape-row">
<div class="scout-card">
    <div class="scout-title">Away Team ({intel.get('away_rec', '--')})</div>
    <div class="scout-name">🏈 {g['away_team']}</div>
    <div class="scout-splits">Trench Matchup • {intel.get('headline', 'Standard Slate')}</div>
</div>
<div class="scout-card">
    <div class="scout-title">Home Team ({intel.get('home_rec', '--')})</div>
    <div class="scout-name">🏈 {g['home_team']}</div>
    <div class="scout-splits">Stadium Weather • {g['weather']}</div>
</div>
</div>"""
                context_summary = f"Matchup notes: <b>{intel.get('headline', 'NFL Game')}</b>. Venue: <b>{intel.get('venue', 'Stadium')}</b>."
            elif is_nba:
                tape_row_html = f"""<div class="tape-row">
<div class="scout-card">
    <div class="scout-title">Away Team ({intel.get('away_rec', '--')})</div>
    <div class="scout-name">🏀 {g['away_team']}</div>
    <div class="scout-splits">Pace / Transition Matchup</div>
</div>
<div class="scout-card">
    <div class="scout-title">Home Team ({intel.get('home_rec', '--')})</div>
    <div class="scout-name">🏀 {g['home_team']}</div>
    <div class="scout-splits">{intel.get('headline', 'Regular Season')}</div>
</div>
</div>"""
                context_summary = f"Venue: <b>{intel.get('venue', 'Arena')}</b>."
            elif is_nhl:
                tape_row_html = f"""<div class="tape-row">
<div class="scout-card">
    <div class="scout-title">Away Team ({intel.get('away_rec', '--')})</div>
    <div class="scout-name">🏒 {g['away_team']}</div>
    <div class="scout-splits">5v5 xGF% & Special Teams Duel</div>
</div>
<div class="scout-card">
    <div class="scout-title">Home Team ({intel.get('home_rec', '--')})</div>
    <div class="scout-name">🏒 {g['home_team']}</div>
    <div class="scout-splits">{intel.get('headline', 'Regular Season')}</div>
</div>
</div>"""
                context_summary = f"Matchup hosted at <b>{intel.get('venue', 'Arena')}</b>."
            else:
                tape_row_html = ""
                context_summary = f"Venue: <b>{intel.get('venue', 'Arena')}</b>."

            # Dossier Card Markup
            dossier_html = f"""<div class="game-dossier">
<div class="dossier-header">
<div>
<div class="matchup-headline">{g['matchup']}</div>
<div class="matchup-records">{g['away_team']} ({intel.get('away_rec', '--')}) vs {g['home_team']} ({intel.get('home_rec', '--')}) • 🏟️ {intel.get('venue', 'Stadium')}</div>
</div>
<div class="weather-badge">🌤️ {g['weather']}</div>
</div>
{tape_row_html}
<table class="market-table">
<thead>
<tr>
<th>Team / Side</th>
<th>Moneyline (PlayNow / Fair)</th>
<th>{spread_label}</th>
<th>Total (O/U)</th>
<th>Kelly Sizing ({kelly_fraction_label.split(' ')[0]})</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align:left; font-weight:700;">{g['away_team']}</td>
<td><span class="highlight-edge">{away_ml['odds']}</span> ({away_ml['prob']}) {away_ml['vel_html']}</td>
<td>{away_spread['point']} {away_spread['odds']}</td>
<td>Over {over_tot['point']} {over_tot['odds']}</td>
<td><span class="highlight-kelly">{away_ml['kelly']}</span></td>
</tr>
<tr>
<td style="text-align:left; font-weight:700;">{g['home_team']}</td>
<td><span class="highlight-edge">{home_ml['odds']}</span> ({home_ml['prob']}) {home_ml['vel_html']}</td>
<td>{home_spread['point']} {home_spread['odds']}</td>
<td>Under {under_tot['point']} {under_tot['odds']}</td>
<td><span class="highlight-kelly">{home_ml['kelly']}</span></td>
</tr>
</tbody>
</table>"""

            # Optional Player Props Table
            if market_scope == "Player and Team Props" and g["props"]:
                prop_rows_html = ""
                for p in g["props"][:8]:
                    p_dec = p["price"]
                    p_ident = p["ident"]
                    p_probs = s_probs.get(p_ident, [])
                    p_fair = float(np.mean(p_probs)) if p_probs else (1.0 / p_dec)
                    p_edge = ((p_dec * p_fair) - 1.0) * 100
                    k_pct, k_stake = calculate_kelly(p_dec, p_fair, bankroll, kelly_fraction)
                    k_str = f"${k_stake:.2f}" if k_stake > 0 else "---"
                    pt_lbl = f"{p['point']}" if p['point'] is not None else ""

                    prop_rows_html += f"""<tr>
<td style="text-align:left;"><b>{p['description']}</b> - {p['market'].replace('_', ' ').title()}</td>
<td>{p['name']} {pt_lbl}</td>
<td><span class="highlight-edge">{decimal_to_american(p_dec)}</span></td>
<td>{p_fair*100:.1f}%</td>
<td style="color:{'#10b981' if p_edge > 0 else '#94a3b8'}; font-weight:700;">{p_edge:+.1f}%</td>
<td><span class="highlight-kelly">{k_str}</span></td>
</tr>"""

                dossier_html += f"""<h5 style="color:#38bdf8; margin: 14px 0 8px 0;">🎯 Top Player Prop Markets</h5>
<table class="market-table">
<thead>
<tr>
<th>Player & Market</th>
<th>Side / Line</th>
<th>PlayNow Odds</th>
<th>Fair Prob</th>
<th>Edge %</th>
<th>Kelly Sizing</th>
</tr>
</thead>
<tbody>{prop_rows_html}</tbody>
</table>"""

            dossier_html += f"""<div class="intel-box">
💡 <b>System Intelligence:</b> Starts at <b>{g['time']} SK</b>. {context_summary} Primary Sharp Metric: {top_play}.
</div>
</div>"""
            st.markdown(dossier_html, unsafe_allow_html=True)

        # Quick Log Form to Google Sheets
        st.markdown("---")
        st.markdown("### 📝 Quick-Log Pick to Google Sheet")
        with st.form("dossier_logger_form", clear_on_submit=False):
            match_names = [f"{d['matchup']} ({d['time']} SK)" for d in st.session_state.dossiers]
            chosen_match_idx = st.selectbox("Select Matchup", range(len(match_names)), format_func=lambda x: match_names[x], key="logger_match_idx")
            active_match = st.session_state.dossiers[chosen_match_idx]

            c1, c2, c3 = st.columns(3)
            pick_selection = c1.text_input("Your Pick", value=f"{active_match['home_team']} ML", key="logger_pick_val")
            wager_odds = c2.text_input("Odds Taken", value="-110", key="logger_odds_val")
            bet_amount = c3.number_input("Wager ($ CAD)", min_value=1.0, value=10.0, step=5.0, key="logger_stake_val")

            record_dossier_btn = st.form_submit_button("Record Pick to Google Sheets", type="primary")

            if record_dossier_btn:
                try:
                    sheet = conn.read(spreadsheet=GOOGLE_SHEET_URL, worksheet="Sheet1", ttl=0)
                    new_row = pd.DataFrame([{
                        "Date": datetime.now(LOCAL_TZ).strftime("%Y-%m-%d %I:%M %p"),
                        "Matchup": active_match["matchup"],
                        "Pick": pick_selection,
                        "Sportsbook": "PlayNow SK",
                        "Odds": wager_odds,
                        "Stake": bet_amount,
                        "EV_Percent": "Dossier Log",
                        "Status": "Open",
                        "Notes": f"Kelly Sized | Weather: {active_match['weather']}"
                    }])
                    updated = pd.concat([sheet, new_row], ignore_index=True) if not sheet.empty else new_row
                    conn.update(spreadsheet=GOOGLE_SHEET_URL, worksheet="Sheet1", data=updated)
                    st.success("Successfully logged pick to Google Sheets!")
                except Exception as e:
                    st.error(f"Sheet error: {e}. Check Google Sheet sharing permissions.")
    else:
        st.info("Click '⚡ Scan Board' in the sidebar to populate active game dossiers.")

# --- PARLAY ARCHITECT TAB ---
with tab_parlays:
    st.markdown("### ⚡ Correlation-Safe Parlay Architect")
    st.caption("Cross-game parlay builder with Kelly bankroll allocation.")

    candidate_legs = []
    if st.session_state.dossiers:
        for g in st.session_state.dossiers:
            # Mainlines
            for k, val in g["playnow"].items():
                if 1.05 < val["price"] < 3.50:
                    prob_list = g["sharp_probs"].get(k, [])
                    if prob_list:
                        fair_p = float(np.mean(prob_list))
                        if fair_p >= 0.45:
                            candidate_legs.append({
                                "game_id": g["id"],
                                "matchup": g["matchup"],
                                "pick": f"{g['matchup']} ➔ {val['name']} ({decimal_to_american(val['price'])})",
                                "dec": val["price"],
                                "prob": fair_p
                            })
            # Player Props
            for p in g.get("props", []):
                if 1.40 < p["price"] < 2.50:
                    prob_list = g["sharp_probs"].get(p["ident"], [])
                    if prob_list:
                        fair_p = float(np.mean(prob_list))
                        if fair_p >= 0.50:
                            candidate_legs.append({
                                "game_id": g["id"],
                                "matchup": g["matchup"],
                                "pick": f"{p['description']} ➔ {p['name']} {p.get('point', '')} ({decimal_to_american(p['price'])})",
                                "dec": p["price"],
                                "prob": fair_p
                            })

    if len(candidate_legs) >= 2:
        leg_labels = [c["pick"] for c in candidate_legs]
        selected_picks = st.multiselect("Select 2 to 4 Distinct Legs", options=leg_labels, default=leg_labels[:2], key="parlay_multiselect")

        if len(selected_picks) >= 2:
            chosen = [candidate_legs[leg_labels.index(p)] for p in selected_picks]
            game_ids = [c["game_id"] for c in chosen]
            is_correlated = len(game_ids) != len(set(game_ids))

            if is_correlated:
                st.warning("⚠️ Same-Game Correlation Warning: Detected multiple legs from the same event. PlayNow applies custom SGP correlations.")

            total_dec = 1.0
            joint_prob = 1.0
            for c in chosen:
                total_dec *= c["dec"]
                joint_prob *= c["prob"]

            parlay_us = decimal_to_american(total_dec)
            k_pct, parlay_kelly = calculate_kelly(total_dec, joint_prob, bankroll, kelly_fraction)

            st.markdown(f"""<div class="game-dossier" style="border: 2px solid #38bdf8;">
<div class="matchup-headline">Combined Multi-Leg Ticket ({parlay_us})</div>
<div style="font-size: 13px; color: #94a3b8; margin-bottom: 12px;">{' + '.join([c['pick'] for c in chosen])}</div>
<div class="tape-row">
<div class="scout-card">
    <div class="scout-title">Combined Odds & Pricing</div>
    <div style="font-size: 16px; font-weight: 800; color: #ffffff;">{parlay_us} ({total_dec:.2f} Dec)</div>
    <div style="font-size: 12px; font-family: 'JetBrains Mono', monospace; color: #38bdf8; margin-top: 2px;">Independent Win Prob: {round(joint_prob * 100, 1)}%</div>
</div>
<div class="scout-card">
    <div class="scout-title">Suggested Kelly Stake ({kelly_fraction_label.split(' ')[0]})</div>
    <div style="font-size: 16px; font-weight: 800; color: #38bdf8;">${parlay_kelly:.2f} CAD</div>
    <div style="font-size: 12px; font-family: 'JetBrains Mono', monospace; color: #10b981; margin-top: 2px;">Est. Payout: ${round(parlay_kelly * total_dec, 2) if parlay_kelly > 0 else round(10 * total_dec, 2)} CAD</div>
</div>
</div>
</div>""", unsafe_allow_html=True)

            with st.form("parlay_logger_form", clear_on_submit=False):
                p_stake = st.number_input("Wager Amount ($ CAD)", min_value=1.0, value=float(parlay_kelly) if parlay_kelly > 0 else 10.0, step=5.0, key="parlay_stake_input")
                p_status = st.selectbox("Ticket Status", ["Open", "Won", "Lost", "Push"], key="parlay_status_select")
                p_submit = st.form_submit_button("Record Parlay to Sheet", type="primary")

                if p_submit:
                    try:
                        sheet = conn.read(spreadsheet=GOOGLE_SHEET_URL, worksheet="Sheet1", ttl=0)
                        new_row = pd.DataFrame([{
                            "Date": datetime.now(LOCAL_TZ).strftime("%Y-%m-%d %I:%M %p"),
                            "Matchup": f"{len(chosen)}-Leg Parlay",
                            "Pick": " + ".join([c["pick"] for c in chosen]),
                            "Sportsbook": "PlayNow SK",
                            "Odds": parlay_us,
                            "Stake": p_stake,
                            "EV_Percent": "Parlay Ticket",
                            "Status": p_status,
                            "Notes": f"Joint Win Prob: {round(joint_prob*100, 1)}% | Kelly Rec: ${parlay_kelly:.2f}"
                        }])
                        updated = pd.concat([sheet, new_row], ignore_index=True) if not sheet.empty else new_row
                        conn.update(spreadsheet=GOOGLE_SHEET_URL, worksheet="Sheet1", data=updated)
                        st.success("Parlay recorded to Google Sheets!")
                    except Exception as e:
                        st.error(f"Sheet error: {e}")
    else:
        st.info("Scan the board to generate candidate legs.")

# --- GOOGLE SHEET VIEWER & CLV AUDITOR ---
st.markdown("---")
with st.expander("📊 View Betting_Tracker Google Sheet & Run CLV Review"):
    c_btn1, c_btn2 = st.columns([1, 2])
    if c_btn1.button("🔄 Refresh Sheet History", key="refresh_sheet_btn"):
        st.cache_data.clear()

    run_clv = c_btn2.button("🎯 Audit Closing Line Value (CLV)", key="audit_clv_btn")

    try:
        tracker_data = conn.read(spreadsheet=GOOGLE_SHEET_URL, worksheet="Sheet1", ttl=0)
        if not tracker_data.empty:
            if run_clv:
                with st.spinner("Auditing bets against benchmark closing prices..."):
                    updated_rows = 0
                    for idx, row in tracker_data.iterrows():
                        notes = str(row.get("Notes", ""))
                        if "CLV:" not in notes:
                            taken_odds = str(row.get("Odds", ""))
                            dec_taken = american_to_decimal(taken_odds)
                            if dec_taken > 1.0:
                                clv_val = round(((dec_taken / 1.952) - 1.0) * 100, 1)
                                clv_tag = f"CLV: {clv_val:+}% (vs -105 Standard)"
                            else:
                                clv_tag = "CLV: Unverified"

                            tracker_data.at[idx, "Notes"] = f"{notes} | {clv_tag}".strip(" |")
                            updated_rows += 1

                    if updated_rows > 0:
                        conn.update(spreadsheet=GOOGLE_SHEET_URL, worksheet="Sheet1", data=tracker_data)
                        st.success(f"Audited {updated_rows} entries in your Google Sheet!")
                    else:
                        st.info("All records already audited.")

            st.dataframe(tracker_data, use_container_width=True)
        else:
            st.info("Your Google Sheet is currently empty.")
    except Exception as e:
        st.warning(f"Could not load tracker log: {e}. Confirm service account permissions on the sheet.")
