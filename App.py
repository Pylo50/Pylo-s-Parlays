import streamlit as st
from streamlit_gsheets import GSheetsConnection
import requests
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="SharpOdds +EV Tracker", layout="wide")

ODDS_API_KEY = st.secrets.get("ODDS_API_KEY", "")
BASE_URL = "https://api.the-odds-api.com/v4/sports"

conn = st.connection("gsheets", type=GSheetsConnection)

def american_to_decimal(american: float) -> float:
    if american > 0:
        return (american / 100.0) + 1.0
    return (100.0 / abs(american)) + 1.0

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
def fetch_odds_cached(sport_key: str, market_key: str, regions: str = "us"):
    url = f"{BASE_URL}/{sport_key}/odds"
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": regions,
        "markets": market_key,
        "oddsFormat": "decimal",
    }
    response = requests.get(url, params=params, timeout=12)
    response.raise_for_status()
    remaining = response.headers.get("x-requests-remaining", "Unknown")
    used = response.headers.get("x-requests-used", "Unknown")
    return response.json(), remaining, used

st.sidebar.title("Odds Scanner")

sport_options = {
    "NFL": "americanfootball_nfl",
    "NCAAF": "americanfootball_ncaaf",
    "MLB": "baseball_mlb",
    "NBA": "basketball_nba",
    "WNBA": "basketball_wnba",
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
st.sidebar.subheader("Bankroll & Sizing")
total_bankroll = st.sidebar.number_input("Total Bankroll ($)", min_value=10.0, value=1000.0, step=50.0)
kelly_fraction = st.sidebar.slider("Kelly Fraction", min_value=0.05, max_value=1.0, value=0.25, step=0.05)
min_ev = st.sidebar.slider("Minimum +EV %", min_value=0.0, max_value=15.0, value=1.0, step=0.5)

scan_clicked = st.sidebar.button("Scan Odds (Cost: 1 Credit)", type="primary")

st.title("SharpOdds Live +EV Dashboard")

if "events_data" not in st.session_state:
    st.session_state.events_data = None
    st.session_state.api_remaining = "N/A"
    st.session_state.api_used = "N/A"

if scan_clicked:
    try:
        with st.spinner(f"Fetching fresh {selected_sport_label} lines..."):
            data, rem, used = fetch_odds_cached(sport_key, market_key)
            st.session_state.events_data = data
            st.session_state.api_remaining = rem
            st.session_state.api_used = used
            st.success("Lines updated!")
    except requests.exceptions.HTTPError as e:
        st.error(f"API Error: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        st.error(f"Failed to fetch lines: {str(e)}")

col_m1, col_m2 = st.columns(2)
col_m1.metric("API Calls Remaining", st.session_state.api_remaining)
col_m2.metric("API Calls Used", st.session_state.api_used)

if st.session_state.events_data:
    opportunities = []

    for event in st.session_state.events_data:
        event_name = f"{event.get('away_team')} @ {event.get('home_team')}"
        commence_time = event.get("commence_time")
        bookmakers = event.get("bookmakers", [])

        benchmark_books = [b for b in bookmakers if b["key"].lower() in ["pinnacle", "pinnaclesports"]]
        reference_book = benchmark_books[0] if benchmark_books else None

        for bm in bookmakers:
            book_title = bm.get("title")
            for market in bm.get("markets", []):
                if market.get("key") != market_key:
                    continue

                for outcome in market.get("outcomes", []):
                    target_name = outcome.get("name")
                    point = outcome.get("point", None)
                    offered_dec = outcome.get("price")

                    ref_dec = None
                    if reference_book:
                        for ref_market in reference_book.get("markets", []):
                            if ref_market.get("key") == market_key:
                                for ref_outcome in ref_market.get("outcomes", []):
                                    if ref_outcome.get("name") == target_name:
                                        if point is None or ref_outcome.get("point") == point:
                                            ref_dec = ref_outcome.get("price")

                    fair_prob = None
                    if ref_dec and ref_dec > 1.0:
                        fair_prob = (1.0 / ref_dec) * 1.025
                    elif offered_dec > 1.0:
                        continue

                    if fair_prob and 0.0 < fair_prob < 1.0:
                        ev_pct = ((offered_dec * fair_prob) - 1.0) * 100.0
                        if ev_pct >= min_ev:
                            rec_stake_pct = calculate_kelly(fair_prob, offered_dec, fraction=kelly_fraction)
                            rec_stake_dollars = round(rec_stake_pct * total_bankroll, 2)

                            target_label = target_name
                            if point is not None:
                                sign = "+" if point > 0 else ""
                                target_label += f" ({sign}{point})"

                            opportunities.append({
                                "Time": commence_time,
                                "Matchup": event_name,
                                "Bet": target_label,
                                "Sportsbook": book_title,
                                "Odds (Dec)": round(offered_dec, 3),
                                "Odds (US)": decimal_to_american(offered_dec),
                                "Fair Prob %": round(fair_prob * 100, 2),
                                "+EV %": round(ev_pct, 2),
                                "Rec Stake ($)": rec_stake_dollars,
                            })

    if opportunities:
        df_opps = pd.DataFrame(opportunities).sort_values(by="+EV %", ascending=False)
        st.subheader(f"Found {len(df_opps)} Opportunities Matching Criteria")
        st.dataframe(df_opps, use_container_width=True)

        st.markdown("---")
        st.subheader("Log a Bet to Tracker Sheet")

        with st.form("bet_logger_form"):
            c1, c2, c3 = st.columns(3)
            selected_match = c1.selectbox("Matchup", df_opps["Matchup"].unique())
            subset = df_opps[df_opps["Matchup"] == selected_match]
            selected_bet = c2.selectbox("Bet", subset["Bet"].unique())
            row_data = subset[subset["Bet"] == selected_bet].iloc[0]

            selected_book = c3.selectbox("Bookmaker", subset[subset["Bet"] == selected_bet]["Sportsbook"].unique())
            
            c4, c5, c6 = st.columns(3)
            logged_odds = c4.text_input("Odds Taken (US)", value=row_data["Odds (US)"])
            logged_stake = c5.number_input("Actual Stake ($)", min_value=1.0, value=float(row_data["Rec Stake ($)"]))
            bet_status = c6.selectbox("Status", ["Open", "Won", "Lost", "Push"])

            notes = st.text_input("Notes (optional)", value=f"+EV {row_data['+EV %']}% | Fair: {row_data['Fair Prob %']}%")
            submit_bet = st.form_submit_button("Record to Google Sheets")

            if submit_bet:
                try:
                    current_sheet = conn.read(worksheet="Sheet1", ttl=0)
                    new_entry = pd.DataFrame([{
                        "Date": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
                        "Matchup": selected_match,
                        "Pick": selected_bet,
                        "Sportsbook": selected_book,
                        "Odds": logged_odds,
                        "Stake": logged_stake,
                        "EV_Percent": row_data["+EV %"],
                        "Status": bet_status,
                        "Notes": notes
                    }])
                    
                    updated_sheet = pd.concat([current_sheet, new_entry], ignore_index=True) if not current_sheet.empty else new_entry
                    conn.update(worksheet="Sheet1", data=updated_sheet)
                    st.success("Bet saved directly to Google Sheets!")
                except Exception as e:
                    st.error(f"Error logging to Google Sheets: {e}")
    else:
        st.info("No bets currently meet the minimum +EV threshold. Adjust the slider or trigger a new sport/market scan.")
else:
    st.info("Select a sport and market in the sidebar, then click 'Scan Odds' to retrieve live lines.")

st.markdown("---")
with st.expander("View Betting_Tracker Google Sheet Log"):
    if st.button("Refresh Tracker Data"):
        st.cache_data.clear()
    try:
        sheet_data = conn.read(worksheet="Sheet1", ttl=0)
        st.dataframe(sheet_data, use_container_width=True)
    except Exception as e:
        st.warning(f"Could not load sheet log. Ensure 'Sheet1' exists and permissions are set to edit. Error: {e}")
