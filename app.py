import streamlit as st
from streamlit_gsheets import GSheetsConnection
import requests
import pandas as pd
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
import numpy as np

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Pylos Parlays | Sharp SK Terminal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- BESPOKE RETRO-CYBER DARK UI ---
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
    .wager-card {
        background: linear-gradient(145deg, rgba(15, 23, 42, 0.9) 0%, rgba(11, 15, 25, 0.95) 100%);
        border: 1px solid #10b981;
        border-radius: 14px;
        padding: 18px;
        margin-bottom: 14px;
        box-shadow: 0 0 18px rgba(16, 185, 129, 0.15);
    }
    .card-top {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
    }
    .source-tag {
        background-color: #10b981;
        color: #041f13;
        font-family: 'JetBrains Mono', monospace;
        font-weight: 800;
        font-size: 11px;
        padding: 3px 8px;
        border-radius: 4px;
    }
    .edge-badge {
        font-family: 'JetBrains Mono', monospace;
        font-weight: 800;
        font-size: 13px;
        padding: 4px 10px;
        border-radius: 6px;
    }
    .match-label {
        font-size: 14px;
        color: #94a3b8;
    }
    .selection-label {
        font-size: 19px;
        font-weight: 800;
        color: #ffffff;
        margin-bottom: 12px;
    }
    .odds-terminal {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 8px;
        background: #070a12;
        border: 1px solid #1e293b;
        border-radius: 8px;
        padding: 10px;
        text-align: center;
    }
    .terminal-lbl {
        font-size: 10px;
        text-transform: uppercase;
        color: #64748b;
    }
    .terminal-data {
        font-family: 'JetBrains Mono', monospace;
        font-size: 14px;
        font-weight: 700;
        margin-top: 3px;
    }
</style>
""", unsafe_allow_html=True)

ODDS_API_KEY = st.secrets.get("ODDS_API_KEY", "")
BASE_URL = "https://api.the-odds-api.com/v4/sports"
conn = st.connection("gsheets", type=GSheetsConnection)
LOCAL_TZ = ZoneInfo("America/Regina")

def decimal_to_american(dec: float) -> str:
    if dec >= 2.0:
        return f"+{int(round((dec - 1.0) * 100))}"
    return f"{int(round(-100 / (dec - 1.0)))}"

def calculate_kelly(fair_p: float, dec: float, fraction: float = 0.25) -> float:
    b = dec - 1.0
    q = 1.0 - fair_p
    return max(0.0, ((b * fair_p - q) / b) * fraction)

# Zero Credit Cost: events list endpoint is free
@st.cache_data(ttl=3600, show_spinner=False)
def get_upcoming_events(sport_key: str):
    url = f"{BASE_URL}/{sport_key}/events"
    res = requests.get(url, params={"apiKey": ODDS_API_KEY}, timeout=10)
    res.raise_for_status()
    return res.json()

# 45 min cache to safeguard quota
@st.cache_data(ttl=2700, show_spinner=False)
def fetch_mainlines(sport_key: str, markets_str: str):
    url = f"{BASE_URL}/{sport_key}/odds"
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "ca,eu",
        "markets": markets_str,
        "oddsFormat": "decimal",
    }
    res = requests.get(url, params=params, timeout=12)
    res.raise_for_status()
    return res.json(), res.headers.get("x-requests-remaining", "N/A"), res.headers.get("x-requests-used", "N/A")

@st.cache_data(ttl=2700, show_spinner=False)
def fetch_game_props(sport_key: str, event_id: str, markets_csv: str):
    url = f"{BASE_URL}/{sport_key}/events/{event_id}/odds"
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "ca,eu",
        "markets": markets_csv,
        "oddsFormat": "decimal",
    }
    res = requests.get(url, params=params, timeout=12)
    res.raise_for_status()
    return res.json(), res.headers.get("x-requests-remaining", "N/A"), res.headers.get("x-requests-used", "N/A")

SPORTS_PRESETS = {
    "⚾ MLB Baseball": {
        "key": "baseball_mlb",
        "props": ["pitcher_strikeouts", "batter_hits", "batter_total_bases", "batter_home_runs", "batter_rbis"]
    },
    "🏈 NFL Football": {
        "key": "americanfootball_nfl",
        "props": ["player_pass_yds", "player_pass_completions", "player_rush_yds", "player_reception_yds", "player_anytime_td"]
    },
    "🏀 NBA Basketball": {
        "key": "basketball_nba",
        "props": ["player_points", "player_rebounds", "player_assists", "player_threes", "player_blocks"]
    },
    "🏒 NHL Hockey": {
        "key": "icehockey_nhl",
        "props": ["player_points", "player_goals", "player_assists", "player_shots_on_goal"]
    }
}

# --- SIDEBAR CONTROLS ---
st.sidebar.markdown("<h3 style='color:#fff;'>⚡ PYLOS TERMINAL</h3>", unsafe_allow_html=True)
st.sidebar.caption("Benchmark: **Sharp Consensus** | Target: **PlayNow SK**")

selected_sport_label = st.sidebar.selectbox("Sport Slate", list(SPORTS_PRESETS.keys()))
sport_info = SPORTS_PRESETS[selected_sport_label]
sport_key = sport_info["key"]

# Timeframe Filter in Local SK Time
time_window = st.sidebar.selectbox(
    "Game Timeframe",
    ["Upcoming 12 Hours", "Upcoming 24 Hours", "Upcoming 48 Hours", "All Available Games"],
    index=1
)

scan_mode = st.sidebar.radio("Scan Mode", ["📊 All Games (Mainlines)", "🎯 Prop Sniper (Token Safe)"])

target_event_id = None
queried_markets = ""
credit_cost = 2

now_local = datetime.now(LOCAL_TZ)

if scan_mode == "📊 All Games (Mainlines)":
    main_selection = st.sidebar.multiselect("Markets", ["h2h (Moneyline)", "spreads", "totals"], default=["h2h (Moneyline)", "spreads", "totals"])
    if not main_selection:
        st.stop()
    clean_keys = [m.split(" ")[0] for m in main_selection]
    queried_markets = ",".join(clean_keys)
    credit_cost = len(clean_keys) * 2
else:
    try:
        events = get_upcoming_events(sport_key)
        if events:
            filtered_events = []
            for e in events:
                commence_raw = e.get("commence_time", "")
                if commence_raw:
                    dt = datetime.fromisoformat(commence_raw.replace("Z", "+00:00")).astimezone(LOCAL_TZ)
                    if dt > now_local:
                        filtered_events.append((dt, e))

            if filtered_events:
                ev_options = {f"{e['away_team']} @ {e['home_team']} ({dt.strftime('%b %d - %I:%M %p')})": e['id'] for dt, e in filtered_events}
                target_game_name = st.sidebar.selectbox("Select Matchup", list(ev_options.keys()))
                target_event_id = ev_options[target_game_name]

                selected_props = st.sidebar.multiselect(
                    "Prop Markets",
                    options=sport_info["props"],
                    default=sport_info["props"][:3]
                )
                if not selected_props:
                    st.sidebar.warning("Choose at least 1 prop.")
                    st.stop()
                queried_markets = ",".join(selected_props)
                credit_cost = len(selected_props) * 2
            else:
                st.sidebar.info("No upcoming games found for this sport.")
        else:
            st.sidebar.info("No games listed.")
    except Exception as e:
        st.sidebar.error(f"Event error: {e}")

st.sidebar.markdown("---")
st.sidebar.markdown("**Filters & Thresholds**")
bankroll = st.sidebar.number_input("Bankroll ($ CAD)", min_value=10.0, value=1000.0, step=50.0)

# Edge slider allowing negative margins to reveal best-priced favorites and coin-flips
min_edge = st.sidebar.slider(
    "Min Edge (% EV)", 
    min_value=-6.0, 
    max_value=10.0, 
    value=-3.5, 
    step=0.25,
    help="Set around -3.5% to capture standard-vig PlayNow favorites and high-confidence picks."
)

min_win_prob = st.sidebar.slider(
    "Min Win Probability %", 
    min_value=30, 
    max_value=85, 
    value=45, 
    step=5,
    help="Set to 50%+ for favorites and coin-flips; 60%+ for heavy favorites."
)

sort_by = st.sidebar.selectbox(
    "Sort Results By", 
    ["Highest Win Probability (Best Bets)", "Highest +EV Edge"]
)
kelly_fraction = st.sidebar.slider("Kelly Fraction", 0.05, 0.50, 0.25, step=0.05)

run_scan = st.sidebar.button(f"⚡ Scan Board (~{credit_cost} Credits)", type="primary")

# --- MAIN DISPLAY ---
st.markdown("<div class='terminal-title'>⚡ PYLOS PARLAYS <span class='accent-pill'>PLAYNOW SK</span></div>", unsafe_allow_html=True)
st.markdown("<div class='terminal-sub'>SHARP MARKET CONSENSUS ➔ PLAYNOW VALUE & PROBABILITY TERMINAL</div>", unsafe_allow_html=True)

if "api_rem" not in st.session_state:
    st.session_state.api_rem = "---"
    st.session_state.api_used = "---"
    st.session_state.opps = []

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

# Main Processing Engine
if run_scan:
    st.session_state.opps = []
    try:
        with st.spinner("Analyzing market consensus across sharp books..."):
            if scan_mode == "📊 All Games (Mainlines)":
                raw_events, rem, used = fetch_mainlines(sport_key, queried_markets)
            else:
                if not target_event_id:
                    st.error("No game selected.")
                    st.stop()
                raw_data, rem, used = fetch_game_props(sport_key, target_event_id, queried_markets)
                raw_events = [raw_data]

            st.session_state.api_rem = rem
            st.session_state.api_used = used
            now_local = datetime.now(LOCAL_TZ)

            # Determine maximum cutoff window
            window_hours = 9999
            if time_window == "Upcoming 12 Hours":
                window_hours = 12
            elif time_window == "Upcoming 24 Hours":
                window_hours = 24
            elif time_window == "Upcoming 48 Hours":
                window_hours = 48
            cutoff_dt = now_local + timedelta(hours=window_hours)

            found_plays = []
            SHARP_KEYS = ["pinnacle", "betfair_ex_eu", "betonlineag", "coolbet", "unibet_eu", "betvictor"]

            total_games_checked = 0
            playnow_lines_found = 0

            for ev in raw_events:
                commence_raw = ev.get("commence_time", "")
                if commence_raw:
                    dt = datetime.fromisoformat(commence_raw.replace("Z", "+00:00")).astimezone(LOCAL_TZ)
                    # Filter out games already started or outside the chosen window
                    if dt <= now_local or dt > cutoff_dt:
                        continue

                total_games_checked += 1
                matchup = f"{ev.get('away_team')} @ {ev.get('home_team')}"
                formatted_time = dt.strftime("%b %d - %I:%M %p")
                bookmakers = ev.get("bookmakers", [])

                market_probs = {}
                playnow_wagers = []

                for bm in bookmakers:
                    bm_key = bm.get("key", "").lower()
                    is_sharp = any(k in bm_key for k in SHARP_KEYS)

                    if is_sharp:
                        for m in bm.get("markets", []):
                            outcomes = m.get("outcomes", [])
                            if len(outcomes) >= 2:
                                raw_p = {o.get("description", "") + o["name"] + str(o.get("point", "")): 1.0 / o["price"] for o in outcomes if o.get("price", 0) > 1.0}
                                total_vig = sum(raw_p.values())
                                if total_vig > 0:
                                    for o in outcomes:
                                        desc = o.get("description", "")
                                        pt = o.get("point", None)
                                        ident = desc + o["name"] + str(pt if pt is not None else "")
                                        norm_p = raw_p[ident] / total_vig
                                        if ident not in market_probs:
                                            market_probs[ident] = []
                                        market_probs[ident].append(norm_p)

                    if "playnow" in bm_key:
                        for m in bm.get("markets", []):
                            for o in m.get("outcomes", []):
                                playnow_lines_found += 1
                                p_desc = o.get("description", "")
                                side = o.get("name")
                                pt = o.get("point", None)
                                label = f"{p_desc} {side} {pt}" if p_desc else f"{side} {f'({pt})' if pt is not None else ''}"
                                ident = p_desc + side + str(pt if pt is not None else "")

                                playnow_wagers.append({
                                    "ident": ident,
                                    "display": label,
                                    "price": o["price"],
                                    "matchup": matchup,
                                    "time": formatted_time
                                })

                for wager in playnow_wagers:
                    id_k = wager["ident"]
                    if id_k not in market_probs or len(market_probs[id_k]) == 0:
                        continue

                    fair_p = float(np.mean(market_probs[id_k]))
                    win_prob_pct = fair_p * 100.0

                    # 1. Win Probability Floor
                    if win_prob_pct < min_win_prob:
                        continue

                    dec_odds = wager["price"]
                    ev_pct = ((dec_odds * fair_p) - 1.0) * 100.0

                    # 2. Edge / Hold Threshold
                    if ev_pct >= min_edge:
                        rec_stake = calculate_kelly(fair_p, dec_odds, fraction=kelly_fraction)
                        suggested_cash = round(rec_stake * bankroll, 2) if ev_pct >= 0 else round(0.01 * bankroll, 2)

                        found_plays.append({
                            "pick": wager["display"],
                            "matchup": wager["matchup"],
                            "playnow_us": decimal_to_american(dec_odds),
                            "fair_us": decimal_to_american(1.0 / fair_p),
                            "fair_prob_num": win_prob_pct,
                            "fair_prob": f"{round(win_prob_pct, 1)}%",
                            "ev": round(ev_pct, 2),
                            "stake": suggested_cash,
                            "time": wager["time"]
                        })

            if sort_by == "Highest Win Probability (Best Bets)":
                found_plays = sorted(found_plays, key=lambda x: x["fair_prob_num"], reverse=True)
            else:
                found_plays = sorted(found_plays, key=lambda x: x["ev"], reverse=True)

            st.session_state.opps = found_plays

            st.caption(f"Diagnostics: Scanned {total_games_checked} games in timeframe | Found {playnow_lines_found} total PlayNow lines.")
            if found_plays:
                st.success(f"Loaded {len(found_plays)} qualified bets matching your criteria!")
            else:
                st.info(f"0 bets matched. Try sliding 'Min Edge' to -4.5% or lowering 'Min Win Probability' to 40%.")

    except Exception as ex:
        st.error(f"Scan failed: {ex}")

# Render Wager Cards
if st.session_state.opps:
    st.markdown("### 🟢 Qualified Bets on PlayNow SK")
    for row in st.session_state.opps:
        badge_style = "background: rgba(16, 185, 129, 0.15); color: #10b981; border: 1px solid #10b981;" if row['ev'] >= 0 else "background: rgba(56, 189, 248, 0.15); color: #38bdf8; border: 1px solid #0284c7;"
        badge_text = f"+{row['ev']}% EDGE" if row['ev'] >= 0 else f"{row['ev']}% HOLD"

        st.markdown(f"""
        <div class="wager-card">
            <div class="card-top">
                <div>
                    <span class="source-tag">PLAYNOW SK</span>
                    <span style="font-size: 11px; color: #64748b; margin-left: 8px; font-family: 'JetBrains Mono';">{row['time']} SK</span>
                </div>
                <div class="edge-badge" style="{badge_style}">{badge_text}</div>
            </div>
            <div class="match-label">{row['matchup']}</div>
            <div class="selection-label">{row['pick']}</div>
            <div class="odds-terminal">
                <div>
                    <div class="terminal-lbl">PlayNow Odds</div>
                    <div class="terminal-data" style="color:#10b981;">{row['playnow_us']}</div>
                </div>
                <div>
                    <div class="terminal-lbl">Sharp Fair</div>
                    <div class="terminal-data">{row['fair_us']}</div>
                </div>
                <div>
                    <div class="terminal-lbl">Win Prob</div>
                    <div class="terminal-data" style="color:#38bdf8;">{row['fair_prob']}</div>
                </div>
                <div>
                    <div class="terminal-lbl">Suggested Bet</div>
                    <div class="terminal-data" style="color:#f59e0b;">${row['stake']}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # 1-Tap Google Sheets Logger
    st.markdown("---")
    st.markdown("### 📝 Quick-Log Wager to Google Sheet")
    with st.form("quick_log_form"):
        play_labels = [f"{o['matchup']} ➔ {o['pick']} ({o['playnow_us']}) | Prob: {o['fair_prob']}" for o in st.session_state.opps]
        selected_idx = st.selectbox("Select Wager to Record", range(len(play_labels)), format_func=lambda x: play_labels[x])
        active = st.session_state.opps[selected_idx]

        c1, c2 = st.columns(2)
        final_stake = c1.number_input("Actual Stake ($ CAD)", min_value=1.0, value=float(max(1.0, active["stake"])))
        bet_status = c2.selectbox("Result", ["Open", "Won", "Lost", "Push"])

        record_btn = st.form_submit_button("Record to Betting_Tracker Sheet", type="primary")

        if record_btn:
            try:
                sheet = conn.read(worksheet="Sheet1", ttl=0)
                new_row = pd.DataFrame([{
                    "Date": datetime.now(LOCAL_TZ).strftime("%Y-%m-%d %I:%M %p"),
                    "Matchup": active["matchup"],
                    "Pick": active["pick"],
                    "Sportsbook": "PlayNow SK",
                    "Odds": active["playnow_us"],
                    "Stake": final_stake,
                    "EV_Percent": active["ev"],
                    "Status": bet_status,
                    "Notes": f"Fair: {active['fair_us']} ({active['fair_prob']})"
                }])
                updated = pd.concat([sheet, new_row], ignore_index=True) if not sheet.empty else new_row
                conn.update(worksheet="Sheet1", data=updated)
                st.success("Successfully logged to Google Sheet!")
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
