import streamlit as st
from streamlit_gsheets import GSheetsConnection
import requests
import pandas as pd
from datetime import datetime

st.set_page_config(
    page_title="Pylos Parlays | Morning Scanner",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom High-End Cyber UI
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@500;700;800&family=Plus+Jakarta+Sans:wght@500;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    .stApp {
        background-color: #080c14;
        color: #e2e8f0;
    }
    .metric-card {
        background: linear-gradient(180deg, #111827 0%, #0b0f19 100%);
        border: 1px solid #1f2937;
        border-radius: 12px;
        padding: 12px 16px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.4);
    }
    .metric-num {
        font-family: 'JetBrains Mono', monospace;
        font-size: 24px;
        font-weight: 800;
        color: #38bdf8;
    }
    .metric-tag {
        font-size: 11px;
        letter-spacing: 1px;
        color: #64748b;
        text-transform: uppercase;
    }
    .prop-card {
        background: #0f172a;
        border: 1px solid #10b981;
        border-radius: 12px;
        padding: 14px 18px;
        margin-bottom: 12px;
        box-shadow: 0 0 12px rgba(16, 185, 129, 0.15);
    }
    .prop-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
    }
    .player-name {
        font-size: 17px;
        font-weight: 800;
        color: #f8fafc;
    }
    .badge-playnow {
        background: #059669;
        color: #ffffff;
        padding: 3px 9px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 800;
    }
    .badge-edge {
        background: rgba(56, 189, 248, 0.15);
        color: #38bdf8;
        border: 1px solid #38bdf8;
        padding: 3px 8px;
        border-radius: 6px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 12px;
        font-weight: 700;
    }
    .odds-matrix {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 6px;
        background: #090d16;
        border: 1px solid #1e293b;
        padding: 8px;
        border-radius: 8px;
        margin-top: 10px;
        text-align: center;
    }
    .matrix-title {
        font-size: 10px;
        color: #64748b;
        text-transform: uppercase;
    }
    .matrix-val {
        font-family: 'JetBrains Mono', monospace;
        font-size: 13px;
        font-weight: 700;
        color: #f1f5f9;
    }
</style>
""", unsafe_allow_html=True)

ODDS_API_KEY = st.secrets.get("ODDS_API_KEY", "")
BASE_URL = "https://api.the-odds-api.com/v4/sports"
conn = st.connection("gsheets", type=GSheetsConnection)

def decimal_to_american(dec: float) -> str:
    if dec >= 2.0:
        return f"+{int(round((dec - 1.0) * 100))}"
    return f"{int(round(-100 / (dec - 1.0)))}"

def calculate_kelly(fair_p: float, dec: float, fraction: float = 0.25) -> float:
    b = dec - 1.0
    q = 1.0 - fair_p
    return max(0.0, ((b * fair_p - q) / b) * fraction)

# Zero Credit Cost fixture fetcher
@st.cache_data(ttl=3600, show_spinner=False)
def get_upcoming_events(sport_key: str):
    url = f"{BASE_URL}/{sport_key}/events"
    res = requests.get(url, params={"apiKey": ODDS_API_KEY}, timeout=10)
    res.raise_for_status()
    return res.json()

# Cache 45 mins to preserve quota
@st.cache_data(ttl=2700, show_spinner=False)
def fetch_mainline_slate(sport_key: str, market_str: str):
    url = f"{BASE_URL}/{sport_key}/odds"
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "ca,eu",
        "markets": market_str,
        "oddsFormat": "decimal",
    }
    res = requests.get(url, params=params, timeout=12)
    res.raise_for_status()
    return res.json(), res.headers.get("x-requests-remaining", "N/A"), res.headers.get("x-requests-used", "N/A")

@st.cache_data(ttl=2700, show_spinner=False)
def fetch_props_for_game(sport_key: str, event_id: str, markets_csv: str):
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

# --- USER'S HARDCODED PROP CONFIGURATION ---
SPORTS_CFG = {
    "🏈 NFL Football": {
        "key": "americanfootball_nfl",
        "props": [
            "player_pass_yds", "player_pass_completions", "player_pass_attempts", 
            "player_rush_yds", "player_receptions", "player_reception_yds", "player_anytime_td"
        ]
    },
    "🏈 NCAAF Football": {
        "key": "americanfootball_ncaaf",
        "props": ["player_pass_yds", "player_rush_yds", "player_reception_yds", "player_anytime_td"]
    },
    "⚾ MLB Baseball": {
        "key": "baseball_mlb",
        "props": ["pitcher_strikeouts", "batter_hits", "batter_total_bases", "batter_home_runs", "batter_rbis"]
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

st.sidebar.markdown("### ⚡ Pylos Parlays")
selected_sport = st.sidebar.selectbox("Sport", list(SPORTS_CFG.keys()))
sport_info = SPORTS_CFG[selected_sport]
sport_key = sport_info["key"]

mode = st.sidebar.radio(
    "Morning Mode", 
    ["📊 All Games (Mainlines)", "🎯 Game Prop Sniper (Token Safe)"]
)

target_event_id = None
target_game_lbl = ""
markets_to_request = ""
calc_cost = 2

if mode == "📊 All Games (Mainlines)":
    m_choice = st.sidebar.multiselect("Mainline Markets", ["h2h (Moneyline)", "spreads", "totals"], default=["h2h (Moneyline)", "spreads", "totals"])
    if not m_choice:
        st.stop()
    clean_keys = [m.split(" ")[0] for m in m_choice]
    markets_to_request = ",".join(clean_keys)
    calc_cost = len(clean_keys) * 2
else:
    try:
        events = get_upcoming_events(sport_key)
        if events:
            ev_map = {f"{e['away_team']} @ {e['home_team']}": e['id'] for e in events}
            target_game_lbl = st.sidebar.selectbox("Select Matchup", list(ev_map.keys()))
            target_event_id = ev_map[target_game_lbl]
            
            # Pre-select user's entire prop wishlist
            chosen_props = st.sidebar.multiselect(
                "Props for This Matchup", 
                options=sport_info["props"], 
                default=sport_info["props"][:3],
                help="Add or remove prop types to tune credit cost."
            )
            if not chosen_props:
                st.sidebar.warning("Select at least 1 prop type.")
                st.stop()
            markets_to_request = ",".join(chosen_props)
            calc_cost = len(chosen_props) * 2
        else:
            st.sidebar.info("No games listed currently.")
    except Exception as err:
        st.sidebar.error(f"Event fetch error: {err}")

st.sidebar.markdown("---")
bankroll = st.sidebar.number_input("Bankroll ($ CAD)", min_value=10.0, value=1000.0, step=50.0)
kelly_fraction = st.sidebar.slider("Kelly Fraction", 0.05, 0.50, 0.25, step=0.05)
min_ev_threshold = st.sidebar.slider("Min Edge (+EV %)", 0.0, 10.0, 0.5, step=0.25)

scan_btn = st.sidebar.button(f"⚡ Scan Odds (~{calc_cost} Credits)", type="primary")

# --- HEADER SECTION ---
st.markdown("<h2 style='font-weight: 800; letter-spacing: -0.5px;'>⚡ PYLOS PARLAYS <span style='color:#10b981;'>SK</span></h2>", unsafe_allow_html=True)
st.markdown("<p style='color: #94a3b8; font-size: 13px; margin-top: -10px;'>Pinnacle Fair Price Devig Engine ➔ PlayNow SK Value Scanner</p>", unsafe_allow_html=True)

if "api_rem" not in st.session_state:
    st.session_state.api_rem = "---"
    st.session_state.api_used = "---"
    st.session_state.opp_cards = []

c1, c2 = st.columns(2)
with c1:
    st.markdown(f"""<div class='metric-card'><div class='metric-tag'>Calls Remaining</div><div class='metric-num'>{st.session_state.api_rem}</div></div>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""<div class='metric-card'><div class='metric-tag'>Calls Consumed</div><div class='metric-num'>{st.session_state.api_used}</div></div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Main Processing Loop
if scan_btn:
    st.session_state.opp_cards = []
    try:
        with st.spinner("Processing lines..."):
            if mode == "📊 All Games (Mainlines)":
                raw_data, rem, used = fetch_mainline_slate(sport_key, markets_to_request)
                events_to_process = raw_data
            else:
                raw_data, rem, used = fetch_props_for_game(sport_key, target_event_id, markets_to_request)
                events_to_process = [raw_data]

            st.session_state.api_rem = rem
            st.session_state.api_used = used
            extracted = []

            for event in events_to_process:
                matchup_str = f"{event.get('away_team')} @ {event.get('home_team')}"
                commence = event.get("commence_time", "")
                bookmakers = event.get("bookmakers", [])

                pinnacle_fair = {}
                playnow_lines = []

                for bm in bookmakers:
                    b_key = bm.get("key", "").lower()

                    # Pinnacle Math
                    if "pinnacle" in b_key:
                        for m in bm.get("markets", []):
                            outs = m.get("outcomes", [])
                            if len(outs) >= 2:
                                raw_p = {o.get("description", "") + o["name"] + str(o.get("point", "")): 1.0 / o["price"] for o in outs if o.get("price", 0) > 1.0}
                                total_v = sum(raw_p.values())
                                if total_v > 0:
                                    for o in outs:
                                        desc = o.get("description", "")
                                        pt = o.get("point", None)
                                        ident = desc + o["name"] + str(pt if pt is not None else "")
                                        pinnacle_fair[ident] = raw_p[ident] / total_v

                    # PlayNow Target
                    elif "playnow" in b_key:
                        for m in bm.get("markets", []):
                            for o in m.get("outcomes", []):
                                p_name = o.get("description", "")
                                pt = o.get("point", None)
                                side = o.get("name")
                                label = f"{p_name} {side} {pt}" if p_name else f"{side} {f'({pt})' if pt is not None else ''}"
                                ident = p_name + side + str(pt if pt is not None else "")

                                playnow_lines.append({
                                    "ident": ident,
                                    "display": label,
                                    "player": p_name if p_name else matchup_str,
                                    "price": o["price"],
                                    "matchup": matchup_str,
                                    "time": commence
                                })

                # Comparison
                for pick in playnow_lines:
                    id_key = pick["ident"]
                    if id_key not in pinnacle_fair:
                        continue

                    fair_p = pinnacle_fair[id_key]
                    dec = pick["price"]
                    ev = ((dec * fair_p) - 1.0) * 100.0

                    if ev >= min_ev_threshold:
                        stake_pct = calculate_kelly(fair_p, dec, fraction=kelly_fraction)
                        extracted.append({
                            "player": pick["player"],
                            "pick_text": pick["display"],
                            "matchup": pick["matchup"],
                            "playnow_odds": decimal_to_american(dec),
                            "pinnacle_fair": decimal_to_american(1.0 / fair_p),
                            "fair_prob": f"{round(fair_p * 100, 1)}%",
                            "ev": round(ev, 2),
                            "rec_stake": round(stake_pct * bankroll, 2),
                            "time": pick["time"][:16].replace("T", " ")
                        })

            st.session_state.opp_cards = extracted
            if extracted:
                st.success(f"Found {len(extracted)} +EV plays on PlayNow SK!")
            else:
                st.info("No PlayNow lines currently meet the +EV threshold for this scan.")
    except Exception as ex:
        st.error(f"Scan error: {ex}")

# Render Wager Cards
if st.session_state.opp_cards:
    st.markdown("### 🟢 Opportunities on PlayNow SK")
    for row in st.session_state.opp_cards:
        st.markdown(f"""
        <div class="prop-card">
            <div class="prop-header">
                <div>
                    <span class="badge-playnow">PLAYNOW SK</span>
                    <span style="font-size: 11px; color: #64748b; margin-left: 8px;">{row['time']}</span>
                </div>
                <div class="badge-edge">+{row['ev']}% EDGE</div>
            </div>
            <div class="player-name">{row['player']}</div>
            <div style="font-size: 14px; font-weight: 700; color: #38bdf8; margin-top: 2px;">{row['pick_text']}</div>
            <div class="odds-matrix">
                <div>
                    <div class="matrix-title">PlayNow Odds</div>
                    <div class="matrix-val" style="color:#10b981;">{row['playnow_odds']}</div>
                </div>
                <div>
                    <div class="matrix-title">Fair Line</div>
                    <div class="matrix-val">{row['pinnacle_fair']}</div>
                </div>
                <div>
                    <div class="matrix-title">Win Prob</div>
                    <div class="matrix-val">{row['fair_prob']}</div>
                </div>
                <div>
                    <div class="matrix-title">Kelly Stake</div>
                    <div class="matrix-val" style="color:#fbbf24;">${row['rec_stake']}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # 1-Tap Google Sheets Logger
    st.markdown("---")
    st.markdown("### 📝 Quick-Log Wager to Google Sheet")
    with st.form("bet_quick_logger"):
        item_labels = [f"{c['player']} ➔ {c['pick_text']} ({c['playnow_odds']})" for c in st.session_state.opp_cards]
        selected_index = st.selectbox("Select Play", range(len(item_labels)), format_func=lambda i: item_labels[i])
        active = st.session_state.opp_cards[selected_index]

        col_a, col_b = st.columns(2)
        logged_stake = col_a.number_input("Wagered ($ CAD)", min_value=1.0, value=float(max(1.0, active["rec_stake"])))
        bet_status = col_b.selectbox("Result", ["Open", "Won", "Lost", "Push"])

        submit_to_sheet = st.form_submit_button("Record Wager to Sheet", type="primary")

        if submit_to_sheet:
            try:
                sheet = conn.read(worksheet="Sheet1", ttl=0)
                new_entry = pd.DataFrame([{
                    "Date": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
                    "Matchup": active["matchup"],
                    "Pick": f"{active['player']} - {active['pick_text']}",
                    "Sportsbook": "PlayNow SK",
                    "Odds": active["playnow_odds"],
                    "Stake": logged_stake,
                    "EV_Percent": active["ev"],
                    "Status": bet_status,
                    "Notes": f"Fair: {active['pinnacle_fair']} ({active['fair_prob']})"
                }])
                combined = pd.concat([sheet, new_entry], ignore_index=True) if not sheet.empty else new_entry
                conn.update(worksheet="Sheet1", data=combined)
                st.success("Successfully logged to Betting_Tracker Sheet!")
            except Exception as err:
                st.error(f"Sheet error: {err}")

st.markdown("---")
with st.expander("📊 View Betting_Tracker Google Sheet Log"):
    if st.button("Refresh Table"):
        st.cache_data.clear()
    try:
        records = conn.read(worksheet="Sheet1", ttl=0)
        st.dataframe(records, use_container_width=True)
    except Exception as e:
        st.warning(f"Could not load tracker data: {e}")
