import streamlit as st
from streamlit_gsheets import GSheetsConnection
import requests
import pandas as pd
from datetime import datetime

st.set_page_config(
    page_title="Pylos Parlays | Sharp +EV",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom High-End Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700;800&family=Inter:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background: radial-gradient(circle at 10% 20%, #0d1117 0%, #05070a 90%);
        color: #e6edf3;
    }

    /* Metric Cards */
    .metric-box {
        background: rgba(22, 27, 34, 0.7);
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 14px 18px;
        text-align: center;
        backdrop-filter: blur(8px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    .metric-val {
        font-family: 'JetBrains Mono', monospace;
        font-size: 26px;
        font-weight: 800;
        color: #58a6ff;
    }
    .metric-lbl {
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #8b949e;
    }

    /* Opportunity Cards */
    .opp-card {
        background: linear-gradient(135deg, rgba(22, 27, 34, 0.85), rgba(13, 17, 23, 0.95));
        border: 1px solid #238636;
        border-radius: 14px;
        padding: 16px;
        margin-bottom: 14px;
        box-shadow: 0 0 15px rgba(35, 134, 54, 0.2);
    }
    .opp-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
    }
    .opp-title {
        font-size: 16px;
        font-weight: 700;
        color: #f0f6fc;
    }
    .playnow-pill {
        background-color: #238636;
        color: white;
        padding: 4px 10px;
        border-radius: 20px;
        font-weight: 800;
        font-size: 12px;
        letter-spacing: 0.5px;
        display: inline-block;
    }
    .ev-badge {
        background: rgba(88, 166, 255, 0.15);
        color: #58a6ff;
        border: 1px solid #58a6ff;
        padding: 3px 8px;
        border-radius: 8px;
        font-family: 'JetBrains Mono', monospace;
        font-weight: 700;
        font-size: 13px;
    }
    .stats-row {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 8px;
        margin-top: 10px;
        text-align: center;
        background: rgba(13, 17, 23, 0.6);
        padding: 8px;
        border-radius: 8px;
    }
    .stat-item-lbl {
        font-size: 10px;
        color: #8b949e;
        text-transform: uppercase;
    }
    .stat-item-val {
        font-family: 'JetBrains Mono', monospace;
        font-size: 14px;
        font-weight: 700;
        color: #f0f6fc;
    }
</style>
""", unsafe_allow_html=True)

ODDS_API_KEY = st.secrets.get("ODDS_API_KEY", "")
BASE_URL = "https://api.the-odds-api.com/v4/sports"
conn = st.connection("gsheets", type=GSheetsConnection)

def decimal_to_american(decimal_odds: float) -> str:
    if decimal_odds >= 2.0:
        val = int(round((decimal_odds - 1.0) * 100))
        return f"+{val}"
    val = int(round(-100 / (decimal_odds - 1.0)))
    return f"{val}"

def calculate_kelly(fair_prob: float, offered_dec_odds: float, fraction: float = 0.25) -> float:
    b = offered_dec_odds - 1.0
    q = 1.0 - fair_prob
    kelly_full = (b * fair_prob - q) / b
    return max(0.0, kelly_full * fraction)

# Cache for 20 mins to conserve quota
@st.cache_data(ttl=1200, show_spinner=False)
def fetch_mainline_lines(sport_key: str, market_key: str):
    url = f"{BASE_URL}/{sport_key}/odds"
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "ca,eu",
        "markets": market_key,
        "oddsFormat": "decimal",
    }
    res = requests.get(url, params=params, timeout=12)
    res.raise_for_status()
    return res.json(), res.headers.get("x-requests-remaining", "N/A"), res.headers.get("x-requests-used", "N/A")

@st.cache_data(ttl=1200, show_spinner=False)
def fetch_events_list(sport_key: str):
    url = f"{BASE_URL}/{sport_key}/events"
    params = {"apiKey": ODDS_API_KEY}
    res = requests.get(url, params=params, timeout=10)
    res.raise_for_status()
    return res.json()

@st.cache_data(ttl=1200, show_spinner=False)
def fetch_single_game_props(sport_key: str, event_id: str, prop_market: str):
    url = f"{BASE_URL}/{sport_key}/events/{event_id}/odds"
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "ca,eu",
        "markets": prop_market,
        "oddsFormat": "decimal",
    }
    res = requests.get(url, params=params, timeout=12)
    res.raise_for_status()
    return res.json(), res.headers.get("x-requests-remaining", "N/A"), res.headers.get("x-requests-used", "N/A")

# --- SIDEBAR CONFIG ---
st.sidebar.markdown("### ⚡ Pylos Parlays")
st.sidebar.caption("Exclusive Saskatchewan Engine")

sport_map = {
    "🏈 NFL": ("americanfootball_nfl", ["player_pass_yds", "player_pass_tds", "player_rush_yds", "player_reception_yds"]),
    "⚾ MLB": ("baseball_mlb", ["batter_home_runs", "batter_hits", "pitcher_strikeouts"]),
    "🏀 NBA": ("basketball_nba", ["player_points", "player_rebounds", "player_assists"]),
    "🏒 NHL": ("icehockey_nhl", ["player_points", "player_goals", "player_shots_on_goal"]),
}

selected_sport_name = st.sidebar.selectbox("Sport", list(sport_map.keys()))
sport_key, prop_market_list = sport_map[selected_sport_name]

bet_type = st.sidebar.radio("Bet Category", ["Standard Game Lines", "Player Props (Token Saver)"])

main_market_key = "h2h"
selected_prop_market = None
selected_game_id = None

if bet_type == "Standard Game Lines":
    market_map = {"Moneyline": "h2h", "Spreads": "spreads", "Totals": "totals"}
    main_market_key = market_map[st.sidebar.selectbox("Market", list(market_map.keys()))]
else:
    selected_prop_market = st.sidebar.selectbox("Prop Market", prop_market_list)
    try:
        event_list = fetch_events_list(sport_key)
        game_options = {f"{e['away_team']} @ {e['home_team']}": e['id'] for e in event_list}
        if game_options:
            selected_matchup_lbl = st.sidebar.selectbox("Target Game", list(game_options.keys()))
            selected_game_id = game_options[selected_matchup_lbl]
        else:
            st.sidebar.warning("No upcoming games found.")
    except Exception as err:
        st.sidebar.error(f"Event load error: {err}")

st.sidebar.markdown("---")
st.sidebar.markdown("**Bankroll Settings**")
total_bankroll = st.sidebar.number_input("Bankroll ($ CAD)", min_value=10.0, value=1000.0, step=50.0)
kelly_fraction = st.sidebar.slider("Kelly Sizing", 0.05, 0.50, 0.25, step=0.05)
min_ev = st.sidebar.slider("Min Edge (+EV %)", 0.0, 10.0, 0.5, step=0.25)

scan_cost = 1 if bet_type == "Player Props" else 2
scan_btn = st.sidebar.button(f"⚡ Scan Lines (Cost: {scan_cost})", type="primary")

# --- HEADER SECTION ---
st.markdown("<h2 style='text-align: center; font-weight: 800; letter-spacing: -0.5px;'>⚡ PYLOS PARLAYS <span style='color:#238636;'>SK</span></h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #8b949e; font-size: 13px; margin-top: -10px;'>Pinnacle Sharp Math Devig ➔ PlayNow SK Value Engine</p>", unsafe_allow_html=True)

if "api_remaining" not in st.session_state:
    st.session_state.api_remaining = "---"
    st.session_state.api_used = "---"
    st.session_state.opps = []

# Status Metrics
m1, m2 = st.columns(2)
with m1:
    st.markdown(f"""<div class='metric-box'><div class='metric-lbl'>API Calls Remaining</div><div class='metric-val'>{st.session_state.api_remaining}</div></div>""", unsafe_allow_html=True)
with m2:
    st.markdown(f"""<div class='metric-box'><div class='metric-lbl'>Calls Consumed</div><div class='metric-val'>{st.session_state.api_used}</div></div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Scan Execution
if scan_btn:
    st.session_state.opps = []
    try:
        with st.spinner("Crunching sharp consensus against PlayNow..."):
            if bet_type == "Standard Game Lines":
                raw_events, rem, used = fetch_mainline_lines(sport_key, main_market_key)
                target_mkey = main_market_key
            else:
                if not selected_game_id:
                    st.error("No game selected.")
                    st.stop()
                single_game_data, rem, used = fetch_single_game_props(sport_key, selected_game_id, selected_prop_market)
                raw_events = [single_game_data]
                target_mkey = selected_prop_market

            st.session_state.api_remaining = rem
            st.session_state.api_used = used

            extracted_opps = []

            for event in raw_events:
                event_name = f"{event.get('away_team')} @ {event.get('home_team')}"
                commence = event.get("commence_time", "")
                bookmakers = event.get("bookmakers", [])

                pinnacle_odds = {}
                playnow_offers = []

                for bm in bookmakers:
                    b_key = bm.get("key", "").lower()
                    
                    # Sharp Benchmark: Pinnacle
                    if "pinnacle" in b_key:
                        for m in bm.get("markets", []):
                            if m.get("key") == target_mkey:
                                outcomes = m.get("outcomes", [])
                                if len(outcomes) >= 2:
                                    raw_p = {o["name"]: 1.0 / o["price"] for o in outcomes if o.get("price", 0) > 1.0}
                                    vig = sum(raw_p.values())
                                    if vig > 0:
                                        for o in outcomes:
                                            pt = o.get("point", None)
                                            lbl = o["name"] + (f" ({pt})" if pt is not None else "")
                                            pinnacle_odds[lbl] = raw_p[o["name"]] / vig

                    # Target Book: PlayNow SK
                    elif "playnow" in b_key:
                        for m in bm.get("markets", []):
                            if m.get("key") == target_mkey:
                                for o in m.get("outcomes", []):
                                    pt = o.get("point", None)
                                    desc = o.get("description", "") # Used for player prop names
                                    lbl = (f"{desc} " if desc else "") + o["name"] + (f" ({pt})" if pt is not None else "")
                                    playnow_offers.append({
                                        "bet": lbl,
                                        "price": o["price"],
                                        "event": event_name,
                                        "time": commence
                                    })

                # Mathematical Comparison
                for offer in playnow_offers:
                    bet_name = offer["bet"]
                    if bet_name not in pinnacle_odds:
                        continue

                    fair_p = pinnacle_odds[bet_name]
                    dec = offer["price"]
                    ev = ((dec * fair_p) - 1.0) * 100.0

                    if ev >= min_ev:
                        stake_pct = calculate_kelly(fair_p, dec, fraction=kelly_fraction)
                        dollars = round(stake_pct * total_bankroll, 2)
                        fair_dec = 1.0 / fair_p

                        extracted_opps.append({
                            "matchup": offer["event"],
                            "pick": bet_name,
                            "playnow_us": decimal_to_american(dec),
                            "playnow_dec": round(dec, 2),
                            "fair_us": decimal_to_american(fair_dec),
                            "fair_prob": f"{round(fair_p * 100, 1)}%",
                            "ev": round(ev, 2),
                            "rec_stake": dollars,
                            "time": offer["time"][:16].replace("T", " ")
                        })

            st.session_state.opps = extracted_opps
            if extracted_opps:
                st.success(f"Discovered {len(extracted_opps)} mispriced lines on PlayNow SK!")
            else:
                st.info("No PlayNow lines currently meet the +EV cutoff. Adjust threshold or try another sport.")

    except Exception as e:
        st.error(f"Scan failed: {e}")

# Display Opportunities as Mobile Cards
if st.session_state.opps:
    st.markdown("### 🟢 Active +EV Plays on PlayNow SK")
    for idx, row in enumerate(st.session_state.opps):
        st.markdown(f"""
        <div class="opp-card">
            <div class="opp-header">
                <div>
                    <span class="playnow-pill">PLAYNOW SK</span>
                    <span style="font-size: 12px; color: #8b949e; margin-left: 8px;">{row['time']}</span>
                </div>
                <div class="ev-badge">+{row['ev']}% EDGE</div>
            </div>
            <div class="opp-title">{row['matchup']}</div>
            <div style="font-size: 15px; font-weight: 700; color: #58a6ff; margin-top: 4px;">{row['pick']}</div>
            <div class="stats-row">
                <div>
                    <div class="stat-item-lbl">PlayNow Odds</div>
                    <div class="stat-item-val" style="color:#238636;">{row['playnow_us']} ({row['playnow_dec']})</div>
                </div>
                <div>
                    <div class="stat-item-lbl">Sharp Fair Price</div>
                    <div class="stat-item-val">{row['fair_us']}</div>
                </div>
                <div>
                    <div class="stat-item-lbl">Kelly Stake</div>
                    <div class="stat-item-val" style="color:#f0883e;">${row['rec_stake']}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # 1-Tap Google Sheets Logger
    st.markdown("---")
    st.markdown("### 📝 Quick-Log Bet to Google Sheet")
    with st.form("quick_log_form"):
        play_labels = [f"{o['matchup']} ➔ {o['pick']} ({o['playnow_us']})" for o in st.session_state.opps]
        selected_idx = st.selectbox("Select Play to Record", range(len(play_labels)), format_func=lambda x: play_labels[x])
        active_play = st.session_state.opps[selected_idx]

        c1, c2 = st.columns(2)
        final_stake = c1.number_input("Logged Amount ($ CAD)", min_value=1.0, value=float(max(1.0, active_play["rec_stake"])))
        status = c2.selectbox("Status", ["Open", "Won", "Lost", "Push"])

        log_submit = st.form_submit_button("Record to Betting_Tracker Sheet", type="primary")

        if log_submit:
            try:
                sheet = conn.read(worksheet="Sheet1", ttl=0)
                new_row = pd.DataFrame([{
                    "Date": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
                    "Matchup": active_play["matchup"],
                    "Pick": active_play["pick"],
                    "Sportsbook": "PlayNow SK",
                    "Odds": active_play["playnow_us"],
                    "Stake": final_stake,
                    "EV_Percent": active_play["ev"],
                    "Status": status,
                    "Notes": f"Fair: {active_play['fair_us']} ({active_play['fair_prob']})"
                }])
                updated = pd.concat([sheet, new_row], ignore_index=True) if not sheet.empty else new_row
                conn.update(worksheet="Sheet1", data=updated)
                st.success("Wager successfully logged to Google Sheet!")
            except Exception as e:
                st.error(f"Failed to append to Google Sheets: {e}")

# Live Sheets Viewer
st.markdown("---")
with st.expander("📊 View Betting_Tracker Google Sheet"):
    if st.button("Refresh History"):
        st.cache_data.clear()
    try:
        records = conn.read(worksheet="Sheet1", ttl=0)
        st.dataframe(records, use_container_width=True)
    except Exception as e:
        st.warning(f"Could not load tracker data: {e}")
