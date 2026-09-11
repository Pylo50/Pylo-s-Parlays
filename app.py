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

# --- BESPOKE RETRO-CYBER TERMINAL UI ---
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

    /* Metric Grid */
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
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

    /* 1-Stop Game Dossier Card */
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

    /* Tale of the Tape Sub-row */
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

    /* Markets Table Grid */
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
    .highlight-hold {
        color: #94a3b8;
    }

    /* Intel / Facts Box */
    .intel-box {
        background: rgba(15, 23, 42, 0.8);
        border-left: 3px solid #10b981;
        border-radius: 6px;
        padding: 10px 14px;
        font-size: 12.5px;
        color: #cbd5e1;
        line-height: 1.5;
    }
</style>
""", unsafe_allow_html=True)

ODDS_API_KEY = st.secrets.get("ODDS_API_KEY", "")
BASE_URL = "https://api.the-odds-api.com/v4/sports"
conn = st.connection("gsheets", type=GSheetsConnection)
LOCAL_TZ = ZoneInfo("America/Regina")

# Major Stadium Coordinates for Instant Free Weather
STADIUM_COORDS = {
    "Miami Marlins": (25.778, -80.220),
    "Chicago Cubs": (41.948, -87.655),
    "Los Angeles Dodgers": (34.073, -118.240),
    "Arizona Diamondbacks": (33.445, -112.066),
    "New York Yankees": (40.829, -73.926),
    "Boston Red Sox": (42.346, -71.097),
    "Toronto Blue Jays": (43.641, -79.389),
    "Detroit Tigers": (42.339, -83.048),
    "Houston Astros": (29.757, -95.355),
    "New York Mets": (40.757, -73.845),
    "Philadelphia Phillies": (39.906, -75.166),
    "Atlanta Braves": (33.890, -84.468),
    "Seattle Mariners": (47.591, -122.332),
    "Detroit Lions": (42.340, -83.045),
    "New Orleans Saints": (29.951, -90.081),
    "Kansas City Chiefs": (39.048, -94.483)
}

def decimal_to_american(dec: float) -> str:
    if dec >= 2.0:
        return f"+{int(round((dec - 1.0) * 100))}"
    return f"{int(round(-100 / (dec - 1.0)))}"

# Zero Cost: Free Open-Meteo Weather
@st.cache_data(ttl=7200, show_spinner=False)
def fetch_weather(home_team: str):
    coords = STADIUM_COORDS.get(home_team, (41.878, -87.629))
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={coords[0]}&longitude={coords[1]}&current_weather=true"
        r = requests.get(url, timeout=5).json()
        cw = r.get("current_weather", {})
        temp_c = cw.get("temperature", 20)
        wind_kmh = cw.get("windspeed", 10)
        wind_dir = cw.get("winddirection", 0)
        
        # Wind arrow interpretation
        dirs = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        wind_str = dirs[int((wind_dir + 22.5) % 360 / 45)]
        return f"{temp_c:.0f}°C | 💨 {wind_kmh:.0f} km/h {wind_str}"
    except Exception:
        return "Weather: Dome / Controlled"

# Zero Cost: Free MLB Stats API (Records & Pitchers)
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_mlb_intel(date_str: str):
    try:
        url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={date_str}&hydrate=probablePitcher,team,linescore"
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
                
                matchup_k = f"{away_name} @ {home_name}"
                intel_map[matchup_k] = {
                    "away_rec": away_rec,
                    "home_rec": home_rec,
                    "away_pitcher": away_pitcher,
                    "home_pitcher": home_pitcher,
                    "venue": venue
                }
        return intel_map
    except Exception:
        return {}

@st.cache_data(ttl=2700, show_spinner=False)
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

# --- SIDEBAR CONTROLS ---
st.sidebar.markdown("<h3 style='color:#fff;'>⚡ PYLOS TERMINAL</h3>", unsafe_allow_html=True)
st.sidebar.caption("Benchmark: **Sharp Consensus** | Target: **PlayNow SK**")

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
min_win_prob = st.sidebar.slider("Highlight Bets with Prob ≥ %", min_value=40, max_value=80, value=50, step=5)

run_scan = st.sidebar.button("⚡ Generate Complete Dossiers (~6 Credits)", type="primary")

# --- MAIN DISPLAY ---
st.markdown("<div class='terminal-title'>⚡ PYLOS PARLAYS <span class='accent-pill'>1-STOP COMMAND</span></div>", unsafe_allow_html=True)
st.markdown("<div class='terminal-sub'>FULL MARKET MATRIX ➔ WEATHER ➔ TALE OF THE TAPE ➔ SHARP SASKATCHEWAN INTEL</div>", unsafe_allow_html=True)

if "api_rem" not in st.session_state:
    st.session_state.api_rem = "---"
    st.session_state.api_used = "---"
    st.session_state.dossiers = []

st.markdown(f"""
<div class='metric-grid'>
    <div class='stat-cube'>
        <div class='stat-cube-val'>{st.session_state.api_rem}</div>
        <div class='stat-cube-lbl'>API Calls Remaining</div>
    </div>
    <div class='stat-cube'>
        <div class='stat-cube-val'>{st.session_state.api_used}</div>
        <div class='stat-cube-lbl'>Calls Consumed</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Build Master Game Dossiers
if run_scan:
    st.session_state.dossiers = []
    try:
        with st.spinner("Compiling full game dossier matrix, weather forecasts, and pitching intel..."):
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

            intel_map = {}
            if "baseball" in sport_key:
                intel_map = fetch_mlb_intel(target_date_str)

            SHARP_KEYS = ["pinnacle", "betfair_ex_eu", "betonlineag", "coolbet", "unibet_eu", "betvictor"]
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

                # Fetch Tale of the Tape & Weather
                game_intel = intel_map.get(matchup, {
                    "away_rec": "---", "home_rec": "---",
                    "away_pitcher": "Starting Pitcher", "home_pitcher": "Starting Pitcher",
                    "venue": f"{home_team} Stadium"
                })
                weather_info = fetch_weather(home_team)

                # Devig consensus for all 3 markets
                market_probs = {}
                playnow_lines = {}

                for bm in ev.get("bookmakers", []):
                    bm_k = bm.get("key", "").lower()
                    is_sharp = any(k in bm_k for k in SHARP_KEYS)

                    for m in bm.get("markets", []):
                        m_key = m.get("key") # h2h, spreads, totals
                        outcomes = m.get("outcomes", [])
                        if len(outcomes) >= 2:
                            raw_p = {o["name"] + str(o.get("point", "")): 1.0 / o["price"] for o in outcomes if o.get("price", 0) > 1.0}
                            tot = sum(raw_p.values())
                            if tot > 0:
                                for o in outcomes:
                                    ident = m_key + "_" + o["name"] + str(o.get("point", ""))
                                    if is_sharp:
                                        if ident not in market_probs:
                                            market_probs[ident] = []
                                        market_probs[ident].append(raw_p[o["name"] + str(o.get("point", ""))] / tot)
                                    if "playnow" in bm_k:
                                        playnow_lines[ident] = {
                                            "name": o["name"],
                                            "point": o.get("point", None),
                                            "price": o["price"],
                                            "market": m_key
                                        }

                compiled_games.append({
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
                st.success(f"Built {len(compiled_games)} Full Game Dossiers for {date_filter_mode}!")
            else:
                st.info("No games matched your current schedule filters.")

    except Exception as ex:
        st.error(f"Failed to compile dossiers: {ex}")

# Render Full Game Dossiers
if st.session_state.dossiers:
    for g in st.session_state.dossiers:
        intel = g["intel"]
        p_lines = g["playnow"]
        s_probs = g["sharp_probs"]

        # Helper to extract market data
        def get_line_data(m_key, side_name):
            for k, val in p_lines.items():
                if k.startswith(m_key) and side_name in val["name"]:
                    dec = val["price"]
                    prob_list = s_probs.get(k, [])
                    fair_p = float(np.mean(prob_list)) if prob_list else 1.0 / dec
                    edge = ((dec * fair_p) - 1.0) * 100
                    pt_str = f" ({val['point']:+})" if val['point'] is not None else ""
                    return {
                        "odds": decimal_to_american(dec),
                        "prob": f"{fair_p*100:.1f}%",
                        "edge": f"+{edge:.1f}%" if edge >= 0 else f"{edge:.1f}%",
                        "point": pt_str,
                        "raw_prob": fair_p * 100
                    }
            return {"odds": "---", "prob": "---", "edge": "---", "point": "", "raw_prob": 0}

        away_ml = get_line_data("h2h", g["away_team"])
        home_ml = get_line_data("h2h", g["home_team"])
        away_spread = get_line_data("spreads", g["away_team"])
        home_spread = get_line_data("spreads", g["home_team"])
        over_tot = get_line_data("totals", "Over")
        under_tot = get_line_data("totals", "Under")

        # Synthesize System Read
        top_play = "Neutral Board"
        top_prob = 0
        if home_ml["raw_prob"] > top_prob:
            top_prob = home_ml["raw_prob"]
            top_play = f"Back **{g['home_team']} ML** (Win Prob: {home_ml['prob']})"
        if away_ml["raw_prob"] > top_prob:
            top_prob = away_ml["raw_prob"]
            top_play = f"Back **{g['away_team']} ML** (Win Prob: {away_ml['prob']})"

        # Strictly flush HTML block
        dossier_html = f"""<div class="game-dossier">
<div class="dossier-header">
<div>
<div class="matchup-headline">{g['matchup']}</div>
<div class="matchup-records">{g['away_team']} ({intel['away_rec']}) vs {g['home_team']} ({intel['home_rec']}) • 🏟️ {intel['venue']}</div>
</div>
<div class="weather-badge">🌤️ {g['weather']}</div>
</div>

<div class="tape-row">
<div class="tape-col">⚾ <b>Away Starter:</b> {intel['away_pitcher']}</div>
<div class="tape-col">⚾ <b>Home Starter:</b> {intel['home_pitcher']}</div>
</div>

<table class="market-table">
<thead>
<tr>
<th>Team / Market</th>
<th>Moneyline (PlayNow / Fair)</th>
<th>Spread / Run Line</th>
<th>Game Total (O/U)</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align:left; font-weight:700;">{g['away_team']}</td>
<td><span class="highlight-edge">{away_ml['odds']}</span> ({away_ml['prob']})</td>
<td>{away_spread['point']} {away_spread['odds']}</td>
<td>Over {over_tot['point']} {over_tot['odds']}</td>
</tr>
<tr>
<td style="text-align:left; font-weight:700;">{g['home_team']}</td>
<td><span class="highlight-edge">{home_ml['odds']}</span> ({home_ml['prob']})</td>
<td>{home_spread['point']} {home_spread['odds']}</td>
<td>Under {under_tot['point']} {under_tot['odds']}</td>
</tr>
</tbody>
</table>

<div class="intel-box">
💡 <b>System Intelligence & Game Read:</b> Scheduled for <b>{g['time']} SK</b>. Pitching duel features <b>{intel['away_pitcher']} vs. {intel['home_pitcher']}</b>. Weather conditions at first pitch stand at <b>{g['weather']}</b>. Strongest mathematical angle on the board: {top_play}.
</div>
</div>"""

        st.markdown(dossier_html, unsafe_allow_html=True)

    # 1-Tap Google Sheets Logger for any match
    st.markdown("---")
    st.markdown("### 📝 Quick-Log Game Pick to Google Sheet")
    with st.form("dossier_logger"):
        match_names = [f"{d['matchup']} ({d['time']} SK)" for d in st.session_state.dossiers]
        chosen_match_idx = st.selectbox("Select Matchup", range(len(match_names)), format_func=lambda x: match_names[x])
        active_match = st.session_state.dossiers[chosen_match_idx]

        c1, c2, c3 = st.columns(3)
        pick_selection = c1.text_input("Your Pick (e.g. Dodgers ML, Over 8.5)", value=f"{active_match['home_team']} ML")
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
                    "Notes": f"Weather: {active_match['weather']} | Pitchers: {active_match['intel']['away_pitcher']} vs {active_match['intel']['home_pitcher']}"
                }])
                updated = pd.concat([sheet, new_row], ignore_index=True) if not sheet.empty else new_row
                conn.update(worksheet="Sheet1", data=updated)
                st.success("Successfully logged game dossier play to Google Sheets!")
            except Exception as e:
                st.error(f"Sheet error: {e}")

st.markdown("---")
with st.expander("📊 View Betting_Tracker Google Sheet"):
    if st.button("Refresh History"):
        st.cache_data.clear()
    try:
        tracker_data = conn.read(worksheet="Sheet1", ttl=0)
        st.dataframe(tracker_data, use_container_width=True)
    except Exception as e:
        st.warning(f"Could not load tracker log: {e}")
