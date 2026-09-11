import streamlit as st
from streamlit_gsheets import GSheetsConnection
import requests
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Pylos Parlays +EV Dashboard", layout="wide")

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

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_pinnacle_and_playnow(sport_key: str, market_key: str):
    url = f"{BASE_URL}/{sport_key}/odds"
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "ca,eu",
        "markets": market_key,
        "oddsFormat": "decimal",
    }
    response = requests.get(url, params=params, timeout=12)
    response.raise_for_status()
    remaining = response.headers.get("x-requests-remaining", "Unknown")
    used = response.headers.get("x-requests-used", "Unknown")
    return response.json(), remaining, used

# --- SIDEBAR CONTROLS ---

st.sidebar.title("Pylos Parlays Scanner")
st.sidebar.caption("Benchmark: **Pinnacle** | Target: **PlayNow SK**")

sport_options = {
    "MLB": "baseball_mlb",
    "NFL": "americanfootball_nfl",
    "NCAAF": "americanfootball_ncaaf",
    "NBA": "basketball_nba",
    "NHL": "icehockey_nhl",
    "EPL": "soccer_epl",
    "UFC / MMA": "mma_mixed_martial_arts",
}
selected_sport_label = st.sidebar.selectbox("Sport", list(sport_options.keys()))
sport_key = sport_options[selected_sport_label]

market_options = {
    "Moneyline (H2H)": "h2h",
    "Spreads": "spreads",
    "Totals (Over/Under)": "totals",
}
selected_market_label = st.sidebar.selectbox("Market", list(market_options.keys()))
market_key = market_options[selected_market_label]

st.sidebar.markdown("---")
st.sidebar.subheader("Bankroll & Thresholds")
total_bankroll = st.sidebar.number_input("Total Bankroll ($ CAD)", min_value=10.0, value=1000.0, step=50.0)
kelly_fraction = st.sidebar.slider("Kelly Fraction", min_value=0.05, max_value=1.0, value=0.25, step=0.05, help="0.25 = Quarter Kelly")
min_ev = st.sidebar.slider("Minimum +EV %", min_value=0.0, max_value=15.0, value=0.5, step=0.25)

scan_clicked = st.sidebar.button("Scan Odds (Cost: 2 Credits)", type="primary")

# --- MAIN WORKSPACE ---

st.title("Pylos Parlays +EV Scanner")

if "events_data" not in st.session_state:
    st.session_state.events_data = None
    st.session_state.api_remaining = "N/A"
    st.session_state.api_used = "N/A"

if scan_clicked:
    try:
        with st.spinner(f"Pulling lines for {selected_sport_label}..."):
            data, rem, used = fetch_pinnacle_and_playnow(sport_key, market_key)
            st.session_state.events_data = data
            st.session_state.api_remaining = rem
            st.session_state.api_used = used
            st.success("Lines updated!")
    except requests.exceptions.HTTPError as e:
        st.error(f"API Error: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        st.error(f"Failed to fetch lines: {e}")

col1, col2 = st.columns(2)
col1.metric("API Calls Remaining", st.session_state.api_remaining)
col2.metric("API Calls Used", st.session_state.api_used)

if st.session_state.events_data:
    opportunities = []

    for event in st.session_state.events_data:
        event_name = f"{event.get('away_team')} @ {event.get('home_team')}"
        commence_time = event.get("commence_time", "")
        bookmakers = event.get("bookmakers", [])
        if not bookmakers:
            continue

        pinnacle_odds = {}
        playnow_offers = []

        for bm in bookmakers:
            b_key = bm.get("key", "").lower()
            
            # Identify Pinnacle
            if "pinnacle" in b_key:
                for market in bm.get("markets", []):
                    if market.get("key") == market_key:
                        outcomes = market.get("outcomes", [])
                        if len(outcomes) >= 2:
                            raw_p = {o["name"]: 1.0 / o["price"] for o in outcomes if o.get("price", 0) > 1.0}
                            vig = sum(raw_p.values())
                            if vig > 0:
                                for o in outcomes:
                                    pt = o.get("point", None)
                                    lbl = o["name"] + (f" ({'+' if pt > 0 else ''}{pt})" if pt is not None else "")
                                    pinnacle_odds[lbl] = raw_p[o["name"]] / vig

            # Identify PlayNow
            elif "playnow" in b_key:
                for market in bm.get("markets", []):
                    if market.get("key") == market_key:
                        for o in market.get("outcomes", []):
                            pt = o.get("point", None)
                            lbl = o["name"] + (f" ({'+' if pt > 0 else ''}{pt})" if pt is not None else "")
                            playnow_offers.append({
                                "bet": lbl,
                                "price": o["price"],
                                "event": event_name,
                                "time": commence_time
                            })

        # Compare PlayNow lines against devigged Pinnacle true probability
        for offer in playnow_offers:
            bet_name = offer["bet"]
            if bet_name not in pinnacle_odds:
                continue

            fair_prob = pinnacle_odds[bet_name]
            offered_dec = offer["price"]
            ev_pct = ((offered_dec * fair_prob) - 1.0) * 100.0

            if ev_pct >= min_ev:
                rec_stake_pct = calculate_kelly(fair_prob, offered_dec, fraction=kelly_fraction)
                rec_stake_dollars = round(rec_stake_pct * total_bankroll, 2)
                fair_break_even_dec = 1.0 / fair_prob

                opportunities.append({
                    "Time": offer["time"][:16].replace("T", " "),
                    "Matchup": offer["event"],
                    "Pick": bet_name,
                    "PlayNow Odds (US)": decimal_to_american(offered_dec),
                    "PlayNow (Dec)": round(offered_dec, 2),
                    "Pinnacle Fair Odds": decimal_to_american(fair_break_even_dec),
                    "Fair Prob": f"{round(fair_prob * 100, 1)}%",
                    "+EV %": round(ev_pct, 2),
                    "Rec Stake ($)": rec_stake_dollars,
                })

    if opportunities:
        df_opps = pd.DataFrame(opportunities).sort_values(by="+EV %", ascending=False)
        st.subheader(f"Found {len(df_opps)} PlayNow +EV Opportunities")
        st.dataframe(df_opps, use_container_width=True)

        st.markdown("---")
        st.subheader("Log Bet to Betting Tracker Sheet")

        with st.form("bet_logger_form"):
            c1, c2 = st.columns(2)
            selected_match = c1.selectbox("Matchup", df_opps["Matchup"].unique())
            subset = df_opps[df_opps["Matchup"] == selected_match]
            selected_pick = c2.selectbox("Pick", subset["Pick"].unique())
            row_data = subset[subset["Pick"] == selected_pick].iloc[0]

            c3, c4, c5 = st.columns(3)
            logged_odds = c3.text_input("Odds Taken", value=str(row_data["PlayNow Odds (US)"]))
            logged_stake = c4.number_input("Actual Bet ($ CAD)", min_value=1.0, value=float(max(1.0, row_data["Rec Stake ($)"])))
            bet_status = c5.selectbox("Status", ["Open", "Won", "Lost", "Push"])

            notes = st.text_input("Notes", value=f"+EV: {row_data['+EV %']}% vs Pinnacle Fair: {row_data['Pinnacle Fair Odds']}")
            submit_bet = st.form_submit_button("Record to Google Sheets")

            if submit_bet:
                try:
                    current_sheet = conn.read(worksheet="Sheet1", ttl=0)
                    new_entry = pd.DataFrame([{
                        "Date": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
                        "Matchup": selected_match,
                        "Pick": selected_pick,
                        "Sportsbook": "PlayNow SK",
                        "Odds": logged_odds,
                        "Stake": logged_stake,
                        "EV_Percent": row_data["+EV %"],
                        "Status": bet_status,
                        "Notes": notes
                    }])
                    
                    updated_sheet = pd.concat([current_sheet, new_entry], ignore_index=True) if not current_sheet.empty else new_entry
                    conn.update(worksheet="Sheet1", data=updated_sheet)
                    st.success("Saved directly to Betting_Tracker Google Sheet!")
                except Exception as e:
                    st.error(f"Error logging to Google Sheets: {e}")
    else:
        st.info("No PlayNow lines currently meet the +EV threshold against Pinnacle. Adjust the slider or scan another sport/market.")
else:
    st.info("Select your sport and market in the sidebar, then click 'Scan Odds'.")

st.markdown("---")
with st.expander("View Betting_Tracker Google Sheet Log"):
    if st.button("Refresh Sheet"):
        st.cache_data.clear()
    try:
        sheet_data = conn.read(worksheet="Sheet1", ttl=0)
        st.dataframe(sheet_data, use_container_width=True)
    except Exception as e:
        st.warning(f"Could not load sheet log: {e}")
