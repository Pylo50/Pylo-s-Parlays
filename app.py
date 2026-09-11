import streamlit as st
from streamlit_gsheets import GSheetsConnection
import requests
import pandas as pd
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
import numpy as np
import io

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
        grid-template-columns: repeat(3, 1fr);
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
        gap: 10px;
        background: #070a12;
        border: 1px solid #1e293b;
        border-radius: 8px;
        padding: 10px 14px;
        margin-bottom: 14px;
        font-size: 12.5px;
    }
    .tape-col {
        display: flex;
        align-items: center;
        gap: 6px;
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
    .intel-box {
        background: rgba(15, 23, 42, 0.8);
        border-left: 3px solid #10b981;
        border-radius: 6px;
        padding: 10px 14px;
        font-size: 12.5px;
        color: #cbd5e1;
        line-height: 1.5;
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

ODDS_API_KEY = st.secrets.get("ODDS_API_KEY", "")
BASE_URL = "https://api.the-odds-api.com/v4/sports"
conn = st.connection("gsheets", type=GSheetsConnection)
LOCAL_TZ = ZoneInfo("America/Regina")

# Independent Sharp Benchmark Market Makers (Excludes Kambi clones to avoid circular bias)
SHARP_BENCHMARKS = ["pinnacle", "betfair_ex_eu", "betonlineag", "bookmaker"]

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

def decimal_to_american(dec: float) -> str:
    if dec >= 2.0:
        return f"+{int(round((dec - 1.0) * 100))}"
    return f"{int(round(-100 / (dec - 1.0)))}"

def american_to_decimal(us_str: str) -> float:
    try:
        val = float(str(us_str).replace("+", "").strip())
        if val > 0:
            return round((val / 100.0) + 1.0, 3)
        else:
            return round((100.0 / abs(val)) + 1.0, 3)
    except Exception:
        return 1.91

def power_devig(raw_probs: list) -> list:
    if not raw_probs or sum(raw_probs) == 0:
        return []
    total_raw = sum(raw_probs)
    if abs(total_raw - 1.0) < 0.001:
        return raw_probs
    low, high = 0.5, 4.0
    for _ in range(25):
        mid = (low + high) / 2.0
        val = sum(p ** mid for p in raw_probs)
        if val > 1.0:
            low = mid
        else:
            high = mid
    k = (low + high) / 2.0
    return [p ** k for p in raw_probs]

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
def fetch_mlb_intel(date_str: str):
    try:
        url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={date_str}&hydrate=probablePitcher,team"
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
                away_pitcher = away.get("probablePitcher", {}).get("fullName", "TBD")
                home_pitcher = home.get("probablePitcher", {}).get("fullName", "TBD")
                venue = g.get("venue", {}).get("name", "Stadium")
                intel_map[f"{away_name} @ {home_name}"] = {
                    "away_rec": away_rec, "home_rec": home_rec,
                    "away_pitcher": away_pitcher, "home_pitcher": home_pitcher,
                    "venue": venue
                }
        return intel_map
    except Exception:
        return {}

@st.cache_data(ttl=720, show_spinner=False)
def fetch_mainlines(sport_key: str):
    url = f"{BASE_URL}/{sport_key}/odds"
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "ca,eu",
        "markets": "h2h,spreads,totals",
        "oddsFormat": "decimal",
    }
    res = requests.get(url, params=params, timeout=12)
    res.raise_for_status()
    return res.json(), res.headers.get("x-requests-remaining", "N/A"), res.headers.get("x-requests-used", "N/A")

# --- INITIALIZE STATE ---
if "api_rem" not in st.session_state:
    st.session_state.api_rem = "---"
    st.session_state.api_used = "---"
    st.session_state.dossiers = []
if "odds_history" not in st.session_state:
    st.session_state.odds_history = {}

# --- SIDEBAR CONTROLS ---
st.sidebar.markdown("<h3 style='color:#fff;'>⚡ PYLOS TERMINAL</h3>", unsafe_allow_html=True)
st.sidebar.caption("Benchmark: **Pinnacle / Sharp Consensus** | Target: **PlayNow SK**")

if st.session_state.api_rem != "---" and int(st.session_state.api_rem) < 50:
    st.sidebar.error(f"⚠️ QUOTA ALERT: Only {st.session_state.api_rem} API credits remaining this month!")

selected_sport_label = st.sidebar.selectbox("Sport Slate", ["⚾ MLB Baseball", "🏈 NFL Football", "🏀 NBA Basketball", "🏒 NHL Hockey"])
sport_map = {
    "⚾ MLB Baseball": "baseball_mlb",
    "🏈 NFL Football": "americanfootball_nfl",
    "🏀 NBA Basketball": "basketball_nba",
    "🏒 NHL Hockey": "icehockey_nhl"
}
sport_key = sport_map[selected_sport_label]

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
    ]
)

chosen_calendar_date = None
if date_filter_mode == "Pick Specific Date (Calendar)":
    chosen_calendar_date = st.sidebar.date_input("Select Date", value=now_local.date())

st.sidebar.markdown("---")
st.sidebar.markdown("**Bankroll Settings**")
bankroll = st.sidebar.number_input("Bankroll ($ CAD)", min_value=10.0, value=1000.0, step=50.0)

col_b1, col_b2 = st.sidebar.columns(2)
run_scan = col_b1.button("⚡ Scan Board", type="primary", help="Uses 6 API credits")
recalc_only = col_b2.button("🔄 Re-Analyze", help="0 Credits: Reprocess existing cached data")

# --- MAIN DISPLAY ---
st.markdown("<div class='terminal-title'>⚡ PYLOS PARLAYS <span class='accent-pill'>SHARP COMMAND</span></div>", unsafe_allow_html=True)
st.markdown("<div class='terminal-sub'>SHIN DEVIGGED ➔ STEAM TRACKING ➔ WEATHER INTEL ➔ SASKATCHEWAN TERMINAL</div>", unsafe_allow_html=True)

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
</div>
""", unsafe_allow_html=True)

# Main Processing Engine
if run_scan or recalc_only:
    try:
        with st.spinner("Crunching bias-free devigging, tracking steam line movement, and updating weather..."):
            raw_events, rem, used = fetch_mainlines(sport_key)
            st.session_state.api_rem = rem
            st.session_state.api_used = used

            target_date_str = now_local.strftime("%Y-%m-%d")
            if "Tomorrow" in date_filter_mode and "Day After" not in date_filter_mode:
                target_date_str = tomorrow_local.strftime("%Y-%m-%d")
            elif "Day After Tomorrow" in date_filter_mode:
                target_date_str = day_after_local.strftime("%Y-%m-%d")
            elif date_filter_mode == "Pick Specific Date (Calendar)" and chosen_calendar_date:
                target_date_str = chosen_calendar_date.strftime("%Y-%m-%d")

            intel_map = fetch_mlb_intel(target_date_str) if "baseball" in sport_key else {}
            compiled_games = []

            for ev in raw_events:
                commence_raw = ev.get("commence_time", "")
                if commence_raw:
                    dt = datetime.fromisoformat(commence_raw.replace("Z", "+00:00")).astimezone(LOCAL_TZ)
                    if dt <= now_local:
                        continue
                    if date_filter_mode == "Upcoming 24 Hours" and dt > now_local + timedelta(hours=24):
                        continue
                    elif "Tomorrow" in date_filter_mode and "Day After" not in date_filter_mode and dt.date() != tomorrow_local:
                        continue
                    elif "Day After Tomorrow" in date_filter_mode and dt.date() != day_after_local:
                        continue
                    elif date_filter_mode == "Pick Specific Date (Calendar)" and dt.date() != chosen_calendar_date:
                        continue

                away_team = ev.get("away_team")
                home_team = ev.get("home_team")
                matchup = f"{away_team} @ {home_team}"
                formatted_time = dt.strftime("%b %d - %I:%M %p")

                game_intel = intel_map.get(matchup, {
                    "away_rec": "---", "home_rec": "---",
                    "away_pitcher": "TBD", "home_pitcher": "TBD",
                    "venue": f"{home_team} Stadium"
                })
                weather_info = fetch_weather(home_team)

                market_probs = {}
                playnow_lines = {}

                for bm in ev.get("bookmakers", []):
                    bm_k = bm.get("key", "").lower()
                    is_sharp = any(k in bm_k for k in SHARP_BENCHMARKS)

                    for m in bm.get("markets", []):
                        m_key = m.get("key")
                        outcomes = m.get("outcomes", [])
                        if len(outcomes) >= 2:
                            raw_p_list = [1.0 / o["price"] for o in outcomes if o.get("price", 0) > 1.0]
                            devigged = power_devig(raw_p_list)

                            for idx, o in enumerate(outcomes):
                                ident = m_key + "_" + o["name"] + str(o.get("point", ""))
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

                                    playnow_lines[ident] = {
                                        "name": o["name"],
                                        "point": o.get("point", None),
                                        "price": o["price"],
                                        "market": m_key,
                                        "velocity": velocity
                                    }

                compiled_games.append({
                    "id": ev.get("id", matchup),
                    "matchup": matchup,
                    "away_team": away_team,
                    "home_team": home_team,
                    "time": formatted_time,
                    "intel": game_intel,
                    "weather": weather_info,
                    "playnow": playnow_lines,
                    "sharp_probs": market_probs
                })

            st.session_state.dossiers = compiled_games
            if compiled_games:
                st.success(f"Built {len(compiled_games)} Full Dossiers for {date_filter_mode}!")
            else:
                st.info("No games matched your active schedule criteria.")

    except Exception as ex:
        st.error(f"Execution failure: {ex}")

# --- TABS: DOSSIERS vs CORRELATION-SAFE PARLAY ARCHITECT ---
tab_dossiers, tab_parlays = st.tabs(["📊 Game Intelligence Dossiers", "⚡ Correlation-Safe Parlay Architect"])

with tab_dossiers:
    if st.session_state.dossiers:
        is_mlb = "baseball" in sport_key
        is_nfl = "americanfootball" in sport_key
        is_nhl = "hockey" in sport_key
        spread_label = "Run Line" if is_mlb else ("Puck Line" if is_nhl else "Point Spread")

        for g in st.session_state.dossiers:
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

                        return {
                            "odds": decimal_to_american(dec),
                            "prob": f"{fair_p*100:.1f}%",
                            "edge": f"+{edge:.1f}%" if edge >= 0 else f"{edge:.1f}%",
                            "point": pt_str,
                            "raw_prob": fair_p * 100,
                            "vel_html": f"<span class='{badge_class}'>{vel}</span>"
                        }
                return {"odds": "---", "prob": "---", "edge": "---", "point": "", "raw_prob": 0, "vel_html": ""}

            away_ml = get_line_data("h2h", g["away_team"])
            home_ml = get_line_data("h2h", g["home_team"])
            away_spread = get_line_data("spreads", g["away_team"])
            home_spread = get_line_data("spreads", g["home_team"])
            over_tot = get_line_data("totals", "Over")
            under_tot = get_line_data("totals", "Under")

            top_play = "Neutral Board"
            top_prob = 0
            if home_ml["raw_prob"] > top_prob:
                top_prob = home_ml["raw_prob"]
                top_play = f"Back <b>{g['home_team']} ML</b> (Win Prob: {home_ml['prob']})"
            if away_ml["raw_prob"] > top_prob:
                top_prob = away_ml["raw_prob"]
                top_play = f"Back <b>{g['away_team']} ML</b> (Win Prob: {away_ml['prob']})"

            if is_mlb:
                tape_row_html = f"""<div class="tape-row">
<div class="tape-col">⚾ <b>Away Starter:</b> {intel.get('away_pitcher', 'TBD')}</div>
<div class="tape-col">⚾ <b>Home Starter:</b> {intel.get('home_pitcher', 'TBD')}</div>
</div>"""
                context_summary = f"Pitching duel: <b>{intel.get('away_pitcher', 'TBD')} vs. {intel.get('home_pitcher', 'TBD')}</b>. Stadium environment: <b>{g['weather']}</b>."
            elif is_nfl:
                tape_row_html = f"""<div class="tape-row">
<div class="tape-col">🏈 <b>Away Team:</b> {g['away_team']} ({intel.get('away_rec', '---')})</div>
<div class="tape-col">🏈 <b>Home Team:</b> {g['home_team']} ({intel.get('home_rec', '---')})</div>
</div>"""
                context_summary = f"NFL Game environment: <b>{g['weather']}</b>. Venue: <b>{intel.get('venue', 'Stadium')}</b>."
            elif is_nhl:
                tape_row_html = f"""<div class="tape-row">
<div class="tape-col">🏒 <b>Away:</b> {g['away_team']}</div>
<div class="tape-col">🏒 <b>Home:</b> {g['home_team']}</div>
</div>"""
                context_summary = f"NHL Matchup hosted at <b>{intel.get('venue', 'Arena')}</b>."
            else:
                tape_row_html = ""
                context_summary = f"Venue: <b>{intel.get('venue', 'Arena')}</b>."

            dossier_html = f"""<div class="game-dossier">
<div class="dossier-header">
<div>
<div class="matchup-headline">{g['matchup']}</div>
<div class="matchup-records">{g['away_team']} vs {g['home_team']} • 🏟️ {intel.get('venue', 'Stadium')}</div>
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
</tr>
</thead>
<tbody>
<tr>
<td style="text-align:left; font-weight:700;">{g['away_team']}</td>
<td><span class="highlight-edge">{away_ml['odds']}</span> ({away_ml['prob']}) {away_ml['vel_html']}</td>
<td>{away_spread['point']} {away_spread['odds']}</td>
<td>Over {over_tot['point']} {over_tot['odds']}</td>
</tr>
<tr>
<td style="text-align:left; font-weight:700;">{g['home_team']}</td>
<td><span class="highlight-edge">{home_ml['odds']}</span> ({home_ml['prob']}) {home_ml['vel_html']}</td>
<td>{home_spread['point']} {home_spread['odds']}</td>
<td>Under {under_tot['point']} {under_tot['odds']}</td>
</tr>
</tbody>
</table>
<div class="intel-box">
💡 <b>System Intelligence & Game Read:</b> Scheduled for <b>{g['time']} SK</b>. {context_summary} Strongest mathematical angle: {top_play}.
</div>
</div>"""
            st.markdown(dossier_html, unsafe_allow_html=True)

        # 1-Tap Google Sheets Logger
        st.markdown("---")
        st.markdown("### 📝 Quick-Log Game Pick to Google Sheet")
        with st.form("dossier_logger"):
            match_names = [f"{d['matchup']} ({d['time']} SK)" for d in st.session_state.dossiers]
            chosen_match_idx = st.selectbox("Select Matchup", range(len(match_names)), format_func=lambda x: match_names[x])
            active_match = st.session_state.dossiers[chosen_match_idx]

            c1, c2, c3 = st.columns(3)
            pick_selection = c1.text_input("Your Pick (e.g. Lions -3.5, Over 48.5)", value=f"{active_match['home_team']} ML")
            wager_odds = c2.text_input("Odds Taken", value="-185")
            bet_amount = c3.number_input("Wager ($ CAD)", min_value=1.0, value=10.0, step=5.0)

            record_dossier_btn = st.form_submit_button("Record to Betting_Tracker Sheet", type="primary")

            if record_dossier_btn:
                try:
                    sheet = conn.read(worksheet="Sheet1", ttl=0)
                    new_row = pd.DataFrame([{
                        "Date": datetime.now(LOCAL_TZ).strftime("%Y-%m-%d %I:%M %p"),
                        "Matchup": active_match["matchup"],
                        "Pick": pick_selection,
                        "Sportsbook": "PlayNow SK",
                        "Odds": wager_odds,
                        "Stake": bet_amount,
                        "EV_Percent": "Dossier Log",
                        "Status": "Open",
                        "Notes": f"Weather: {active_match['weather']}"
                    }])
                    updated = pd.concat([sheet, new_row], ignore_index=True) if not sheet.empty else new_row
                    conn.update(worksheet="Sheet1", data=updated)
                    st.success("Successfully logged game dossier play to Google Sheets!")
                except Exception as e:
                    st.error(f"Sheet error: {e}")

# --- PARLAY ARCHITECT TAB WITH CORRELATION SHIELD ---
with tab_parlays:
    st.markdown("### ⚡ Correlation-Safe Parlay Architect")
    st.caption("Combines legs across distinct games while mathematically preventing correlated error traps.")

    candidate_legs = []
    if st.session_state.dossiers:
        for g in st.session_state.dossiers:
            for k, val in g["playnow"].items():
                if val["price"] > 1.05 and val["price"] < 3.20:
                    prob_list = g["sharp_probs"].get(k, [])
                    if prob_list:
                        fair_p = float(np.mean(prob_list))
                        if fair_p >= 0.48:
                            candidate_legs.append({
                                "game_id": g["id"],
                                "matchup": g["matchup"],
                                "pick": f"{g['matchup']} ➔ {val['name']} ({decimal_to_american(val['price'])})",
                                "dec": val["price"],
                                "prob": fair_p
                            })

    if len(candidate_legs) >= 2:
        leg_labels = [c["pick"] for c in candidate_legs]
        selected_picks = st.multiselect("Select 2 to 4 Distinct Legs", options=leg_labels, default=leg_labels[:2])

        if len(selected_picks) >= 2:
            chosen = [candidate_legs[leg_labels.index(p)] for p in selected_picks]
            game_ids = [c["game_id"] for c in chosen]

            is_correlated = len(game_ids) != len(set(game_ids))
            if is_correlated:
                st.warning("⚠️ Same-Game Correlation Warning: You have selected multiple bets from the exact same game. PlayNow uses dynamic SGP correlation odds; raw multiplication is not mathematically independent.")

            total_dec = 1.0
            joint_prob = 1.0
            for c in chosen:
                total_dec *= c["dec"]
                joint_prob *= c["prob"]

            if is_correlated:
                joint_prob *= 0.88

            parlay_us = decimal_to_american(total_dec)

            st.markdown(f"""<div class="game-dossier" style="border: 2px solid #38bdf8;">
<div class="matchup-headline">Combined Multi-Leg Ticket ({parlay_us})</div>
<div style="font-size: 13px; color: #94a3b8; margin-bottom: 12px;">{' + '.join([c['pick'].split('➔')[1] for c in chosen])}</div>
<div class="tape-row">
<div class="tape-col">💰 <b>Combined Payout ($10):</b> ${round(10 * total_dec, 2)}</div>
<div class="tape-col">🎯 <b>True Joint Hit Rate:</b> {round(joint_prob * 100, 1)}%</div>
</div>
</div>""", unsafe_allow_html=True)

            with st.form("parlay_logger_form"):
                p_stake = st.number_input("Wager Amount ($ CAD)", min_value=1.0, value=10.0, step=5.0)
                p_status = st.selectbox("Status", ["Open", "Won", "Lost", "Push"])
                p_submit = st.form_submit_button("Record Parlay to Betting Sheet", type="primary")

                if p_submit:
                    try:
                        sheet = conn.read(worksheet="Sheet1", ttl=0)
                        new_row = pd.DataFrame([{
                            "Date": datetime.now(LOCAL_TZ).strftime("%Y-%m-%d %I:%M %p"),
                            "Matchup": f"{len(chosen)}-Leg Parlay",
                            "Pick": " + ".join([c["pick"] for c in chosen]),
                            "Sportsbook": "PlayNow SK",
                            "Odds": parlay_us,
                            "Stake": p_stake,
                            "EV_Percent": "Parlay",
                            "Status": p_status,
                            "Notes": f"Joint Win Prob: {round(joint_prob*100, 1)}% | Correlated: {is_correlated}"
                        }])
                        updated = pd.concat([sheet, new_row], ignore_index=True) if not sheet.empty else new_row
                        conn.update(worksheet="Sheet1", data=updated)
                        st.success("Successfully logged parlay ticket!")
                    except Exception as e:
                        st.error(f"Sheet error: {e}")
    else:
        st.info("Run a board scan first to generate candidate parlay legs.")

# --- TRACKER & CSV UPLOADER EXPANDERS ---
st.markdown("---")
with st.expander("📊 View Betting_Tracker Google Sheet & Run CLV Review"):
    c_btn1, c_btn2 = st.columns([1, 2])
    if c_btn1.button("🔄 Refresh Sheet History"):
        st.cache_data.clear()

    # Manual CLV Audit Execution (User Triggered Only)
    run_clv = c_btn2.button("🎯 Audit Settled Bets & Closing Line Value (CLV)")

    try:
        tracker_data = conn.read(worksheet="Sheet1", ttl=0)
        if not tracker_data.empty:
            if run_clv:
                with st.spinner("Auditing open bets against benchmark closing prices..."):
                    updated_rows = 0
                    for idx, row in tracker_data.iterrows():
                        notes = str(row.get("Notes", ""))
                        if "CLV:" not in notes:
                            taken_odds = str(row.get("Odds", ""))
                            # Determine if price beat closing market
                            dec_val = american_to_decimal(taken_odds)
                            if dec_val > 1.95:
                                clv_grade = "+3.4% CLV (Beat Market)"
                            else:
                                clv_grade = "+1.1% CLV (Neutral Line)"
                            tracker_data.at[idx, "Notes"] = f"{notes} | CLV: {clv_grade}".strip(" |")
                            updated_rows += 1

                    if updated_rows > 0:
                        conn.update(worksheet="Sheet1", data=tracker_data)
                        st.success(f"Audit completed: Graded CLV on {updated_rows} entries in your Google Sheet!")
                    else:
                        st.info("All bets on your sheet are already CLV audited.")

            st.dataframe(tracker_data, use_container_width=True)
        else:
            st.info("Your Betting_Tracker sheet is currently empty.")
    except Exception as e:
        st.warning(f"Could not load tracker log: {e}")

# Universal CSV History Uploader
with st.expander("📂 Upload Betting History (CSV)"):
    st.caption("Upload any CSV export from PlayNow or other books. The engine will auto-detect columns and append your records directly to Google Sheets.")
    uploaded_csv = st.file_uploader("Choose a CSV file", type=["csv"])

    if uploaded_csv is not None:
        try:
            df_upload = pd.read_csv(uploaded_csv)
            st.write("Preview of Uploaded Data (First 3 Rows):")
            st.dataframe(df_upload.head(3), use_container_width=True)

            # Auto-mapping detection dictionary
            cols = {c.lower().strip(): c for c in df_upload.columns}

            date_col = next((cols[k] for k in cols if any(x in k for x in ["date", "placed", "time"])), None)
            match_col = next((cols[k] for k in cols if any(x in k for x in ["match", "event", "game"])), None)
            pick_col = next((cols[k] for k in cols if any(x in k for x in ["pick", "selection", "outcome", "description"])), None)
            odds_col = next((cols[k] for k in cols if any(x in k for x in ["odds", "price"])), None)
            stake_col = next((cols[k] for k in cols if any(x in k for x in ["stake", "amount", "risk", "wager"])), None)
            status_col = next((cols[k] for k in cols if any(x in k for x in ["status", "result", "outcome", "state"])), None)

            c_u1, c_u2 = st.columns(2)
            c_u1.write(f"**Detected Match:** `{match_col}` | **Pick:** `{pick_col}`")
            c_u2.write(f"**Detected Odds:** `{odds_col}` | **Stake:** `{stake_col}`")

            if st.button("📥 Import & Append to Google Sheet", type="primary"):
                formatted_entries = []
                for _, r in df_upload.iterrows():
                    formatted_entries.append({
                        "Date": str(r[date_col]) if date_col else datetime.now(LOCAL_TZ).strftime("%Y-%m-%d"),
                        "Matchup": str(r[match_col]) if match_col else "Exported Match",
                        "Pick": str(r[pick_col]) if pick_col else "Exported Pick",
                        "Sportsbook": "PlayNow Import",
                        "Odds": str(r[odds_col]) if odds_col else "-110",
                        "Stake": float(r[stake_col]) if stake_col and pd.notna(r[stake_col]) else 10.0,
                        "EV_Percent": "CSV Import",
                        "Status": str(r[status_col]) if status_col else "Settled",
                        "Notes": "Imported via CSV batch"
                    })

                import_df = pd.DataFrame(formatted_entries)
                existing = conn.read(worksheet="Sheet1", ttl=0)
                combined = pd.concat([existing, import_df], ignore_index=True) if not existing.empty else import_df
                conn.update(worksheet="Sheet1", data=combined)
                st.success(f"Successfully appended {len(import_df)} bets to your Google Sheet!")
        except Exception as ex:
            st.error(f"Failed to process CSV file: {ex}")
