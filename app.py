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
        font-size: 26px;
        letter-spacing: -0.5px;
        color: #ffffff;
    }
    .accent-pill {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: #ffffff;
        font-size: 12px;
        font-weight: 800;
        padding: 2px 8px;
        border-radius: 6px;
        display: inline-block;
        box-shadow: 0 0 10px rgba(16, 185, 129, 0.35);
        vertical-align: middle;
        margin-left: 6px;
    }
    .terminal-sub {
        color: #94a3b8;
        font-size: 12px;
        font-family: 'JetBrains Mono', monospace;
        margin-top: 4px;
        margin-bottom: 16px;
    }
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 10px;
        margin-bottom: 18px;
    }
    .stat-cube {
        background: rgba(15, 23, 42, 0.7);
        border: 1px solid #1e293b;
        border-radius: 10px;
        padding: 10px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
        backdrop-filter: blur(10px);
    }
    .stat-cube-val {
        font-family: 'JetBrains Mono', monospace;
        font-size: 20px;
        font-weight: 800;
        color: #38bdf8;
    }
    .stat-cube-lbl {
        font-size: 10px;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        color: #64748b;
        margin-top: 2px;
    }
    .game-dossier {
        border-radius: 14px;
        padding: 16px;
        margin-bottom: 18px;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.5);
    }
    .dossier-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid #1e293b;
        padding-bottom: 10px;
        margin-bottom: 12px;
    }
    .matchup-headline {
        font-size: 18px;
        font-weight: 800;
        color: #ffffff;
        letter-spacing: -0.3px;
    }
    .matchup-records {
        font-size: 12px;
        color: #94a3b8;
        font-family: 'JetBrains Mono', monospace;
    }
    .weather-badge {
        background: rgba(56, 189, 248, 0.12);
        color: #38bdf8;
        border: 1px solid rgba(56, 189, 248, 0.3);
        border-radius: 6px;
        font-size: 11px;
        font-family: 'JetBrains Mono', monospace;
        padding: 3px 8px;
        text-align: right;
    }
    .tape-row {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 10px;
        margin-bottom: 12px;
    }
    .scout-card {
        background: #070a12;
        border: 1px solid #1e293b;
        border-radius: 8px;
        padding: 10px;
        min-height: 82px;
    }
    .scout-title {
        font-size: 10px;
        text-transform: uppercase;
        color: #64748b;
        letter-spacing: 0.6px;
        font-weight: 700;
        margin-bottom: 3px;
    }
    .scout-name {
        font-size: 14px;
        font-weight: 800;
        color: #ffffff;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .scout-stat-line {
        font-size: 11px;
        font-family: 'JetBrains Mono', monospace;
        color: #38bdf8;
        line-height: 1.35;
        margin-top: 3px;
    }
    .scout-stat-sub {
        font-size: 10.5px;
        font-family: 'JetBrains Mono', monospace;
        color: #94a3b8;
        line-height: 1.3;
    }
    .market-table {
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 12px;
        font-family: 'JetBrains Mono', monospace;
    }
    .market-table th {
        background: rgba(30, 41, 59, 0.6);
        color: #94a3b8;
        font-size: 10px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        padding: 6px 4px;
        text-align: center;
        border: 1px solid #1e293b;
    }
    .market-table td {
        padding: 6px 4px;
        border: 1px solid #1e293b;
        font-size: 12px;
        text-align: center;
    }
    .color-good {
        color: #10b981 !important;
        font-weight: 800;
    }
    .color-bad {
        color: #f87171 !important;
        font-weight: 700;
    }
    .color-unknown {
        color: #94a3b8 !important;
        font-weight: 700;
    }
    .badge-verdict-good {
        background: rgba(16, 185, 129, 0.2);
        color: #10b981;
        border: 1px solid #10b981;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 800;
        font-size: 11px;
        display: inline-block;
    }
    .badge-verdict-pass {
        background: rgba(239, 68, 68, 0.15);
        color: #f87171;
        border: 1px solid #ef4444;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 800;
        font-size: 11px;
        display: inline-block;
    }
    .badge-verdict-unpriced {
        background: rgba(148, 163, 184, 0.15);
        color: #94a3b8;
        border: 1px solid #475569;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 800;
        font-size: 11px;
        display: inline-block;
    }
    .hold-badge {
        font-size: 9.5px;
        color: #f59e0b;
        font-weight: 700;
        display: block;
    }
    .last-5-badge {
        display: inline-block;
        font-size: 10px;
        font-family: 'JetBrains Mono', monospace;
        font-weight: 700;
        padding: 1px 6px;
        border-radius: 4px;
        background: rgba(30, 41, 59, 0.8);
        border: 1px solid #334155;
        color: #38bdf8;
        margin-top: 3px;
    }
    .intel-box {
        background: rgba(15, 23, 42, 0.8);
        border-left: 3px solid #38bdf8;
        border-radius: 6px;
        padding: 8px 12px;
        font-size: 11.5px;
        color: #cbd5e1;
        line-height: 1.45;
        margin-top: 8px;
        margin-bottom: 10px;
    }
    .steam-badge-up {
        background: rgba(16, 185, 129, 0.15);
        color: #10b981;
        font-size: 10px;
        font-weight: 700;
        padding: 1px 4px;
        border-radius: 3px;
        border: 1px solid #10b981;
        display: inline-block;
        margin-top: 2px;
    }
    .steam-badge-down {
        background: rgba(239, 68, 68, 0.15);
        color: #f87171;
        font-size: 10px;
        font-weight: 700;
        padding: 1px 4px;
        border-radius: 3px;
        border: 1px solid #ef4444;
        display: inline-block;
        margin-top: 2px;
    }
    .steam-badge-flat {
        background: rgba(148, 163, 184, 0.15);
        color: #94a3b8;
        font-size: 10px;
        font-weight: 700;
        padding: 1px 4px;
        border-radius: 3px;
        border: 1px solid #475569;
        display: inline-block;
        margin-top: 2px;
    }
    .top-pick-banner {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(15, 23, 42, 0.6) 100%);
        border: 1px solid #10b981;
        border-radius: 8px;
        padding: 8px 12px;
        margin: 6px 0 10px 0;
        font-size: 12px;
    }
    .legend-box {
        background: rgba(15, 23, 42, 0.85);
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 10px 12px;
        margin-bottom: 14px;
    }
    .legend-title {
        font-size: 11px;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        color: #38bdf8;
        margin-bottom: 6px;
    }
    .legend-row {
        margin-bottom: 6px;
        line-height: 1.35;
    }
    .legend-term {
        font-size: 11.5px;
        font-weight: 800;
        color: #ffffff;
        font-family: 'JetBrains Mono', monospace;
    }
    .legend-def {
        font-size: 11px;
        color: #94a3b8;
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
# Relative sharpness weighting used when averaging devigged sharp probabilities.
# Pinnacle is widely regarded as the sharpest liquid book; weight it higher than
# secondary sharp/offshore books when they disagree.
SHARP_WEIGHTS = {
    "pinnacle": 3.0,
    "betfair_ex_eu": 2.0,
    "bookmaker": 1.0,
    "betonlineag": 1.0,
}

SPORT_PROPS_MAP = {
    "baseball_mlb": ["pitcher_strikeouts", "batter_home_runs", "batter_hits"],
    "americanfootball_nfl": ["player_pass_yds", "player_rush_yds", "player_reception_yds", "player_receptions", "player_anytime_td"],
    "basketball_nba": ["player_points", "player_rebounds", "player_assists"],
    "icehockey_nhl": ["player_points", "player_shots_on_goal"]
}

# Accurate Sport-Specific Category Groupings
SPORT_SPECIFIC_CATEGORIES = {
    "americanfootball_nfl": {
        "🏈 Passing Yards & TDs": ["pass_yds", "pass_tds"],
        "🏃 Rushing Yards": ["rush_yds"],
        "🎯 Receiving Yards & Catches": ["reception_yds", "receptions"],
        "⚡ Anytime Touchdown": ["anytime_td"]
    },
    "baseball_mlb": {
        "⚾ Pitcher Strikeouts": ["strikeouts"],
        "🏏 Hits & Total Bases": ["batter_hits"],
        "🚀 Home Runs": ["home_runs"]
    },
    "basketball_nba": {
        "🏀 Points": ["points"],
        "📊 Rebounds": ["rebounds"],
        "🎁 Assists": ["assists"]
    },
    "icehockey_nhl": {
        "🏒 Goals & Points": ["points"],
        "🎯 Shots on Goal": ["shots_on_goal"]
    }
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
    "Minnesota Vikings": (44.973, -93.257), "Green Bay Packers": (44.501, -88.062),
    "Pittsburgh Steelers": (40.446, -80.015), "Pittsburgh Pirates": (40.446, -80.005),
    "Philadelphia Eagles": (39.901, -75.167), "Washington Commanders": (38.907, -76.864)
}

# --- MOCK / SAMPLE DATA (for testing the UI without burning API credits) ---
MOCK_TEAM_POOL = {
    "baseball_mlb": [("New York Yankees", "Boston Red Sox"), ("Los Angeles Dodgers", "San Francisco Giants")],
    "americanfootball_nfl": [("Kansas City Chiefs", "Buffalo Bills"), ("Dallas Cowboys", "Philadelphia Eagles")],
    "basketball_nba": [("Boston Celtics", "Miami Heat"), ("Golden State Warriors", "Los Angeles Lakers")],
    "icehockey_nhl": [("Toronto Maple Leafs", "Montreal Canadiens"), ("Edmonton Oilers", "Calgary Flames")],
}

MOCK_PLAYER_POOL = {
    "baseball_mlb": {
        "pitcher_strikeouts": [("Gerrit Cole", 6.5), ("Zack Wheeler", 5.5)],
        "batter_hits": [("Aaron Judge", 1.5), ("Mookie Betts", 1.5)],
        "batter_home_runs": [("Aaron Judge", 0.5), ("Shohei Ohtani", 0.5)],
    },
    "americanfootball_nfl": {
        "player_pass_yds": [("Patrick Mahomes", 275.5), ("Josh Allen", 260.5)],
        "player_rush_yds": [("Christian McCaffrey", 85.5), ("Saquon Barkley", 78.5)],
        "player_reception_yds": [("Travis Kelce", 65.5), ("Tyreek Hill", 90.5)],
        "player_receptions": [("Travis Kelce", 5.5), ("Tyreek Hill", 6.5)],
    },
    "basketball_nba": {
        "player_points": [("Jayson Tatum", 27.5), ("Jimmy Butler", 22.5)],
        "player_rebounds": [("Jayson Tatum", 8.5), ("Bam Adebayo", 9.5)],
        "player_assists": [("Jayson Tatum", 4.5), ("Jimmy Butler", 5.5)],
    },
    "icehockey_nhl": {
        "player_points": [("Auston Matthews", 1.5), ("Nick Suzuki", 0.5)],
        "player_shots_on_goal": [("Auston Matthews", 3.5), ("Nick Suzuki", 2.5)],
    },
}

def _mock_price(fair_dec: float, vig: float) -> float:
    """
    Applies a vig adjustment to a fair decimal price to simulate a real
    bookmaker line. Positive vig = juiced (worse) price. Negative vig =
    deliberately soft/mispriced line, used to simulate a +EV test case.
    """
    fair_prob = 1.0 / fair_dec
    juiced_prob = min(0.97, max(0.03, fair_prob * (1 + vig)))
    return round(1.0 / juiced_prob, 3)

def generate_mock_mainlines(sport_key: str, now_local: datetime):
    """Builds a fake but realistically-shaped Odds API response, including
    one deliberately soft PlayNow price (game 0) so the +EV path can be
    tested, and one normally-juiced game (PASS path)."""
    pairs = MOCK_TEAM_POOL.get(sport_key, [("Sample Home", "Sample Away")])
    offsets_hours = [4, 22, 46]
    events = []
    for i, (home, away) in enumerate(pairs):
        offset = offsets_hours[i % len(offsets_hours)]
        commence = (now_local + timedelta(hours=offset)).astimezone(timezone.utc)
        event_id = f"mock_{sport_key}_{i}"

        home_fair_p = 0.55 if i % 2 == 0 else 0.48
        away_fair_p = 1.0 - home_fair_p
        home_fair_dec = round(1.0 / home_fair_p, 3)
        away_fair_dec = round(1.0 / away_fair_p, 3)
        playnow_vig = -0.04 if i == 0 else 0.05  # game 0 = soft/+EV, rest = normally juiced

        bookmakers = [
            {
                "key": "pinnacle", "title": "Pinnacle",
                "markets": [
                    {"key": "h2h", "outcomes": [
                        {"name": home, "price": home_fair_dec},
                        {"name": away, "price": away_fair_dec},
                    ]},
                    {"key": "spreads", "outcomes": [
                        {"name": home, "price": 1.95, "point": -1.5},
                        {"name": away, "price": 1.95, "point": 1.5},
                    ]},
                    {"key": "totals", "outcomes": [
                        {"name": "Over", "price": 1.95, "point": 8.5},
                        {"name": "Under", "price": 1.95, "point": 8.5},
                    ]},
                ]
            },
            {
                "key": "betonlineag", "title": "BookMaker",
                "markets": [
                    {"key": "h2h", "outcomes": [
                        {"name": home, "price": _mock_price(home_fair_dec, 0.02)},
                        {"name": away, "price": _mock_price(away_fair_dec, 0.02)},
                    ]},
                ]
            },
            {
                "key": "playnow", "title": "PlayNow SK",
                "markets": [
                    {"key": "h2h", "outcomes": [
                        {"name": home, "price": _mock_price(home_fair_dec, playnow_vig)},
                        {"name": away, "price": _mock_price(away_fair_dec, 0.05)},
                    ]},
                    {"key": "spreads", "outcomes": [
                        {"name": home, "price": _mock_price(1.95, 0.05), "point": -1.5},
                        {"name": away, "price": _mock_price(1.95, 0.05), "point": 1.5},
                    ]},
                    {"key": "totals", "outcomes": [
                        {"name": "Over", "price": _mock_price(1.95, 0.05), "point": 8.5},
                        {"name": "Under", "price": _mock_price(1.95, 0.05), "point": 8.5},
                    ]},
                ]
            },
        ]

        events.append({
            "id": event_id,
            "commence_time": commence.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "home_team": home,
            "away_team": away,
            "bookmakers": bookmakers
        })
    return events

def generate_mock_props(sport_key: str, event_id: str):
    """Fake per-event player prop bookmakers, shaped like the real API."""
    prop_defs = MOCK_PLAYER_POOL.get(sport_key, {})
    pinnacle_markets, playnow_markets = [], []
    for market_key, players in prop_defs.items():
        p_out, pn_out = [], []
        for player_name, line in players:
            fair_dec = 1.91
            p_out.append({"name": "Over", "description": player_name, "price": fair_dec, "point": line})
            p_out.append({"name": "Under", "description": player_name, "price": fair_dec, "point": line})
            pn_out.append({"name": "Over", "description": player_name, "price": _mock_price(fair_dec, 0.05), "point": line})
            pn_out.append({"name": "Under", "description": player_name, "price": _mock_price(fair_dec, 0.05), "point": line})
        pinnacle_markets.append({"key": market_key, "outcomes": p_out})
        playnow_markets.append({"key": market_key, "outcomes": pn_out})
    return [
        {"key": "pinnacle", "title": "Pinnacle", "markets": pinnacle_markets},
        {"key": "playnow", "title": "PlayNow SK", "markets": playnow_markets},
    ]

MOCK_OPPONENTS = {
    "baseball_mlb": ["BOS", "TB", "TOR", "BAL", "NYY"],
    "americanfootball_nfl": ["SEA", "LAR", "ARI", "SF", "NO"],
    "basketball_nba": ["MIA", "NYK", "PHI", "MIL", "CLE"],
    "icehockey_nhl": ["MTL", "OTT", "BOS", "TB", "NYR"],
}

def generate_mock_last5(player_name: str, prop_market: str, line_point, sport_key: str) -> str:
    """Deterministic sample last-5 numbers (clearly marked Sample) for UI
    testing — a realistic spread of per-game numbers around the given line,
    each tagged with a fake opponent, in the same format real data uses."""
    stat_label = _stat_label_for_market(prop_market)
    opponents = MOCK_OPPONENTS.get(sport_key, ["OPP"])
    seed = sum(ord(c) for c in (player_name + prop_market))
    base = float(line_point) if line_point else 5.0
    parts = []
    for i in range(5):
        wiggle = ((seed + i * 7) % 9) - 4  # deterministic swing, roughly +/-4
        val = max(0, round(base + wiggle, 1))
        val_str = f"{val:g}"
        parts.append(f"{val_str} vs {opponents[i % len(opponents)]}")
    return f"Last 5 {stat_label} (Sample): " + ", ".join(parts)

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

def calculate_market_hold(decimal_odds_list: list[float]) -> float:
    valid_dec = [d for d in decimal_odds_list if d and d > 1.0]
    if len(valid_dec) < 2:
        return 0.0
    total_implied = sum(1.0 / d for d in valid_dec)
    hold = (1.0 - (1.0 / total_implied)) * 100.0
    return round(hold, 1)

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

def weighted_sharp_average(prob_entries: list) -> float:
    """
    prob_entries: list of (book_key, devigged_prob) tuples.
    Weights Pinnacle/Betfair Exchange higher than secondary sharp books
    instead of a flat np.mean, since not all 'sharp' books are equally sharp.
    """
    if not prob_entries:
        return None
    total_w = 0.0
    total_wp = 0.0
    for book_key, prob in prob_entries:
        w = 1.0
        for k, ww in SHARP_WEIGHTS.items():
            if k in book_key:
                w = ww
                break
        total_w += w
        total_wp += w * prob
    return total_wp / total_w if total_w > 0 else None

def compute_fair_and_edge(dec_price: float, prob_entries: list):
    """
    Central, honest edge calculator.
    Returns (fair_p, edge_val, is_priced).
    is_priced=False means NO sharp book has quoted this market — we genuinely
    do not know the fair price, and the caller must NOT render this as a
    negative-edge / 'pass' result. It must be rendered as 'Unpriced'.
    """
    if not prob_entries:
        return None, None, False
    fair_p = weighted_sharp_average(prob_entries)
    if fair_p is None or fair_p <= 0:
        return None, None, False
    edge_val = ((dec_price * fair_p) - 1.0) * 100
    return fair_p, edge_val, True

# --- LOGGING HELPER ---
def log_quick_bet(matchup: str, pick: str, odds: str, stake: float, notes: str):
    try:
        sheet = conn.read(spreadsheet=GOOGLE_SHEET_URL, worksheet="Sheet1", ttl=0)
        new_row = pd.DataFrame([{
            "Date": datetime.now(LOCAL_TZ).strftime("%Y-%m-%d %I:%M %p"),
            "Matchup": matchup,
            "Pick": pick,
            "Sportsbook": "PlayNow SK",
            "Odds": odds,
            "Stake": stake,
            "EV_Percent": "Quick-Click Log",
            "Status": "Open",
            "Notes": notes
        }])
        updated = pd.concat([sheet, new_row], ignore_index=True) if not sheet.empty else new_row
        conn.update(spreadsheet=GOOGLE_SHEET_URL, worksheet="Sheet1", data=updated)
        st.toast(f"Logged {pick} ({odds}) for ${stake:.2f} CAD!", icon="⚡")
    except Exception as e:
        st.error(f"Sheet write failure: {e}")

# --- SECURE ODDS API DISPATCHERS ---
def fetch_mainlines(sport_key: str):
    url = f"{BASE_URL}/{sport_key}/odds"
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "ca,eu",
        "markets": "h2h,spreads,totals",
        "oddsFormat": "decimal",
    }
    try:
        res = requests.get(url, params=params, timeout=12)
        res.raise_for_status()
        return res.json(), res.headers.get("x-requests-remaining", "N/A"), res.headers.get("x-requests-used", "N/A")
    except requests.exceptions.RequestException as e:
        clean_msg = str(e).split("?")[0] if "?" in str(e) else str(e)
        raise RuntimeError(f"Mainline API error: {clean_msg}")

@st.cache_data(ttl=600, show_spinner=False)
def fetch_event_props(sport_key: str, event_id: str, prop_markets: tuple):
    if not prop_markets or not event_id:
        return []
    url = f"{BASE_URL}/{sport_key}/events/{event_id}/odds"
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "ca,us,eu",
        "markets": ",".join(prop_markets),
        "oddsFormat": "decimal",
    }
    try:
        res = requests.get(url, params=params, timeout=10)
        if res.status_code == 200:
            return res.json().get("bookmakers", [])
        return []
    except Exception:
        return []

# --- HISTORICAL LAST 5 HIT TRACKER ENGINE (REAL GAME LOGS) ---
_PROP_STAT_MAP = {
    # market substring -> (mlb stat group, mlb stat field, espn stat key)
    "strikeouts": ("pitching", "strikeOuts", "strikeouts"),
    "batter_home_runs": ("hitting", "homeRuns", None),
    "batter_hits": ("hitting", "hits", None),
    "pass_yds": (None, None, "passingYards"),
    "rush_yds": (None, None, "rushingYards"),
    "reception_yds": (None, None, "receivingYards"),
    "receptions": (None, None, "receptions"),
    "anytime_td": (None, None, "totalTouchdowns"),
    "player_points": (None, None, "points"),
    "rebounds": (None, None, "rebounds"),
    "assists": (None, None, "assists"),
    "shots_on_goal": (None, None, "shotsOnGoal"),
}

STAT_DISPLAY_LABEL = {
    "strikeouts": "K",
    "batter_home_runs": "HR",
    "batter_hits": "Hits",
    "pass_yds": "Pass Yds",
    "rush_yds": "Rush Yds",
    "reception_yds": "Rec Yds",
    "receptions": "Rec",
    "player_points": "Pts",
    "rebounds": "Reb",
    "assists": "Ast",
    "shots_on_goal": "SOG",
}

def _stat_label_for_market(prop_market: str) -> str:
    key = prop_market.lower()
    for frag, label in STAT_DISPLAY_LABEL.items():
        if frag in key:
            return label
    return "Stat"

def _resolve_prop_stat(prop_market: str):
    key = prop_market.lower()
    for frag, mapping in _PROP_STAT_MAP.items():
        if frag in key:
            return mapping
    return (None, None, None)

@st.cache_data(ttl=21600, show_spinner=False)
def _mlb_player_id(player_name: str):
    try:
        url = "https://statsapi.mlb.com/api/v1/people/search"
        r = requests.get(url, params={"names": player_name}, timeout=6).json()
        people = r.get("people", [])
        if people:
            return people[0].get("id")
    except Exception:
        pass
    return None

@st.cache_data(ttl=21600, show_spinner=False)
def _mlb_last5_gamelog(player_id: int, stat_group: str, season: int):
    try:
        url = f"https://statsapi.mlb.com/api/v1/people/{player_id}/stats"
        params = {"stats": "gameLog", "group": stat_group, "season": season}
        r = requests.get(url, params=params, timeout=8).json()
        splits = r.get("stats", [{}])[0].get("splits", [])
        return splits[-5:] if splits else []
    except Exception:
        return []

@st.cache_data(ttl=21600, show_spinner=False)
def _espn_athlete_id(player_name: str, sport_slug: str):
    try:
        url = f"https://site.api.espn.com/apis/site/v2/sports/{sport_slug}/athletes"
        r = requests.get(url, params={"limit": 2000}, timeout=8).json()
        for a in r.get("athletes", []):
            if a.get("displayName", "").lower() == player_name.lower():
                return a.get("id")
        # fallback: loose contains match
        for a in r.get("athletes", []):
            if player_name.lower() in a.get("displayName", "").lower():
                return a.get("id")
    except Exception:
        pass
    return None

@st.cache_data(ttl=21600, show_spinner=False)
def _espn_last5_gamelog(athlete_id: str, sport_slug: str):
    try:
        url = f"https://site.web.api.espn.com/apis/common/v3/sports/{sport_slug}/athletes/{athlete_id}/gamelog"
        r = requests.get(url, timeout=8).json()
        events = r.get("events", {})
        # ESPN gamelog structure varies; pull the most recent up-to-5 entries generically.
        game_stats = []
        for season_block in r.get("seasonTypes", []):
            for cat in season_block.get("categories", []):
                for ev in cat.get("events", []):
                    game_stats.append(ev)
        return game_stats[-5:] if game_stats else []
    except Exception:
        return []

def fetch_player_last_5(player_name: str, prop_market: str, line_point: float, sport: str = "americanfootball_nfl"):
    """
    Returns the player's ACTUAL last-5-game numbers for the relevant stat,
    each tagged with the opponent faced, e.g.:
    'Last 5 Rush Yds: 92 vs SEA, 61 vs LAR, 110 vs ARI, 45 vs SF, 78 vs NO'
    Never fabricates numbers — returns an explicit 'No verified data' string
    if the player or stat cannot be confirmed against a live source.
    """
    if not player_name:
        return "No verified data"

    stat_group, mlb_field, espn_field = _resolve_prop_stat(prop_market)
    stat_label = _stat_label_for_market(prop_market)

    try:
        if "baseball" in sport and mlb_field:
            pid = _mlb_player_id(player_name)
            if not pid:
                return "No verified data"
            season = datetime.now().year
            games = _mlb_last5_gamelog(pid, stat_group, season)
            if not games:
                # try previous season if current season has no logged games yet
                games = _mlb_last5_gamelog(pid, stat_group, season - 1)
            if not games:
                return "No verified data"
            parts = []
            for g in games:
                stat_val = g.get("stat", {}).get(mlb_field, None)
                if stat_val is None:
                    continue
                opp = g.get("opponent", {}).get("abbreviation") or g.get("opponent", {}).get("name", "")
                parts.append(f"{stat_val}{' vs ' + opp if opp else ''}")
            if not parts:
                return "No verified data"
            return f"Last 5 {stat_label}: " + ", ".join(parts)

        elif espn_field:
            slug_map = {
                "americanfootball_nfl": "football/nfl",
                "basketball_nba": "basketball/nba",
                "icehockey_nhl": "hockey/nhl",
            }
            sport_slug = slug_map.get(sport)
            if not sport_slug:
                return "No verified data"
            aid = _espn_athlete_id(player_name, sport_slug)
            if not aid:
                return "No verified data"
            games = _espn_last5_gamelog(aid, sport_slug)
            if not games:
                return "No verified data"
            parts = []
            for g in games:
                stats = g.get("stats", [])
                labels = g.get("labels", [])
                opp_obj = g.get("opponent", {})
                opp = opp_obj.get("abbreviation", "") if isinstance(opp_obj, dict) else ""
                val = None
                if espn_field in labels:
                    idx = labels.index(espn_field)
                    if idx < len(stats):
                        try:
                            val = float(stats[idx])
                        except (TypeError, ValueError):
                            val = None
                if val is not None:
                    val_str = f"{val:g}"
                    parts.append(f"{val_str}{' vs ' + opp if opp else ''}")
            if not parts:
                return "No verified data"
            return f"Last 5 {stat_label}: " + ", ".join(parts)

        return "No verified data"
    except Exception:
        return "No verified data"

# --- SCOUTING INTEL & WEATHER ENGINES ---
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

@st.cache_data(ttl=86400, show_spinner=False)
def fetch_pitcher_profile(person_id: int):
    if not person_id:
        return "RHP", "No verified stats", ""
    try:
        url = f"https://statsapi.mlb.com/api/v1/people/{person_id}?hydrate=stats(group=[pitching],type=[season])"
        r = requests.get(url, timeout=5).json()
        person = r.get("people", [{}])[0]
        hand_code = person.get("pitchHand", {}).get("code", "R")
        arm_label = f"{hand_code}HP"

        stats_list = person.get("stats", [])
        if stats_list:
            splits = stats_list[0].get("splits", [])
            if splits:
                s = splits[-1].get("stat", {})
                w = s.get("wins", 0)
                l = s.get("losses", 0)
                era = s.get("era", "-.--")
                whip = s.get("whip", "-.--")
                so = s.get("strikeOuts", 0)
                ip = s.get("inningsPitched", "0.0")
                line1 = f"({w}-{l}) • {era} ERA"
                line2 = f"{whip} WHIP • {so} K ({ip} IP)"
                return arm_label, line1, line2

        return arm_label, "0-0 • Spot Starter", "Active Roster"
    except Exception:
        return "RHP", "0-0 • Active Roster", ""

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_mlb_deep_intel(date_str: str):
    try:
        url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={date_str}&hydrate=probablePitcher,team(standings)"
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
                away_p_id = away_p.get("id")
                away_hand, away_l1, away_l2 = fetch_pitcher_profile(away_p_id) if away_p_id else ("RHP", "TBD", "")

                home_p = home.get("probablePitcher", {})
                home_p_name = home_p.get("fullName", "TBD")
                home_p_id = home_p.get("id")
                home_hand, home_l1, home_l2 = fetch_pitcher_profile(home_p_id) if home_p_id else ("RHP", "TBD", "")

                dossier_data = {
                    "away_rec": away_rec,
                    "home_rec": home_rec,
                    "away_p_name": away_p_name,
                    "away_p_hand": away_hand,
                    "away_p_l1": away_l1,
                    "away_p_l2": away_l2,
                    "home_p_name": home_p_name,
                    "home_p_hand": home_hand,
                    "home_p_l1": home_l1,
                    "home_p_l2": home_l2,
                    "venue": g.get("venue", {}).get("name", "Stadium")
                }
                intel_map[f"{away_name} @ {home_name}"] = dossier_data
                intel_map[f"{away_name.split()[-1]} @ {home_name.split()[-1]}"] = dossier_data
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
            headline_str = notes[0] if notes else "Regular Season"

            d_data = {
                "away_rec": a_rec,
                "home_rec": h_rec,
                "headline": headline_str,
                "venue": comp.get("venue", {}).get("fullName", "Stadium")
            }
            stats_map[f"{a_name} @ {h_name}"] = d_data
            stats_map[f"{a_name.split()[-1]} @ {h_name.split()[-1]}"] = d_data
        return stats_map
    except Exception:
        return {}

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

st.sidebar.markdown("""
<div class="legend-box">
<div class="legend-title">📖 Terms Legend</div>
<div class="legend-row"><span class="legend-term">Fair Probability</span><br><span class="legend-def">The sharp-book (Pinnacle-weighted) consensus win chance, with bookmaker vig removed. This is the "true" price.</span></div>
<div class="legend-row"><span class="legend-term">True Edge %</span><br><span class="legend-def">How much better (or worse) PlayNow's price is than Fair Probability implies. +2% means you're getting paid 2% more than the fair value — a real mathematical advantage. Negative means you're overpaying.</span></div>
<div class="legend-row"><span class="legend-term">Hold %</span><br><span class="legend-def">The bookmaker's built-in profit margin on a market. Higher hold = harder to find value there.</span></div>
<div class="legend-row"><span class="legend-term">Kelly Stake</span><br><span class="legend-def">Suggested wager size, scaled to your bankroll and edge, at your chosen Kelly risk tier.</span></div>
<div class="legend-row"><span class="legend-term">Unpriced</span><br><span class="legend-def">No sharp book has this market quoted yet. Edge is genuinely unknown — this is NOT the same as a bad bet.</span></div>
<div class="legend-row"><span class="legend-term">▲ Drift / ▼ Steam</span><br><span class="legend-def">Drift = price got worse since last scan. Steam = price got better (often follows sharp money).</span></div>
<div class="legend-row"><span class="legend-term">Last 5</span><br><span class="legend-def">The player's actual result in each of their last 5 games, with opponent — not a guess.</span></div>
</div>
""", unsafe_allow_html=True)

selected_sport_label = st.sidebar.selectbox("Sport Slate", ["🏈 NFL Football", "⚾ MLB Baseball", "🏀 NBA Basketball", "🏒 NHL Hockey"], key="sport_slate_select")
sport_map = {
    "🏈 NFL Football": "americanfootball_nfl",
    "⚾ MLB Baseball": "baseball_mlb",
    "🏀 NBA Basketball": "basketball_nba",
    "🏒 NHL Hockey": "icehockey_nhl"
}
sport_key = sport_map[selected_sport_label]

market_scope = st.sidebar.radio(
    "Market Scope",
    ["Team Markets Only", "Player and Team Props"],
    help="Team: Mainlines only. Player & Team: Adds sport-specific yardage, strikeouts, and scoring props.",
    key="market_scope_radio"
)

st.sidebar.markdown("---")
use_mock_data = st.sidebar.checkbox(
    "🧪 Use Sample Data (No API Calls)",
    value=False,
    help="Test the UI, edge math, and Kelly sizing with fake sample odds. Spends zero Odds API credits.",
    key="mock_mode_checkbox"
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
st.sidebar.markdown("**Bankroll & Flat Wager Sizing**")
bankroll = st.sidebar.number_input("Bankroll ($ CAD)", min_value=10.0, value=1000.0, step=50.0, key="bankroll_input")
flat_unit = st.sidebar.number_input("Option B Flat Wager ($ CAD)", min_value=1.0, value=10.0, step=5.0, help="Default stake when edge is negative/neutral", key="flat_unit_input")
kelly_fraction_label = st.sidebar.selectbox("Kelly Risk Tier", ["Quarter Kelly (0.25) - Sharp Std", "Half Kelly (0.50) - Aggressive", "Full Kelly (1.00) - Theoretical Max"], key="kelly_fraction_select")
kelly_fraction = 0.25 if "Quarter" in kelly_fraction_label else (0.50 if "Half" in kelly_fraction_label else 1.0)

col_b1, col_b2 = st.sidebar.columns(2)
run_scan = col_b1.button("⚡ Scan Board", type="primary", key="scan_btn")
recalc_only = col_b2.button("🔄 Re-Analyze", key="recalc_btn")

# --- STATS SUMMARY BAR ---
st.markdown("<div class='terminal-title'>⚡ PYLOS PARLAYS <span class='accent-pill'>SHARP COMMAND</span></div>", unsafe_allow_html=True)
st.markdown("<div class='terminal-sub'>COLOR-CODED SHARP VALUE ➔ GREEN: +EV | RED: -EV ➔ SASKATCHEWAN TERMINAL</div>", unsafe_allow_html=True)

if use_mock_data:
    st.warning("🧪 SAMPLE DATA MODE — no live Odds API calls are being made. All prices, players, and 'Last 5' values below are synthetic test fixtures, not real markets.")

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
        if use_mock_data:
            with st.spinner("Generating sample board (no API call made)..."):
                st.session_state.raw_events = generate_mock_mainlines(sport_key, now_local)
                st.session_state.api_rem = "MOCK"
                st.session_state.api_used = "MOCK"
        else:
            with st.spinner("Calling API for live mainline feeds..."):
                raw_data, rem, used = fetch_mainlines(sport_key)
                st.session_state.raw_events = raw_data
                st.session_state.api_rem = rem
                st.session_state.api_used = used
    except Exception as ex:
        st.error(f"API Connection Failure: {ex}")

if run_scan or (recalc_only and st.session_state.raw_events):
    try:
        with st.spinner("Devigging odds, requesting event props, and compiling scouting intel..."):
            target_date_str = now_local.strftime("%Y-%m-%d")
            if "Tomorrow" in date_filter_mode and "Day After" not in date_filter_mode:
                target_date_str = tomorrow_local.strftime("%Y-%m-%d")
            elif "Day After Tomorrow" in date_filter_mode:
                target_date_str = day_after_local.strftime("%Y-%m-%d")
            elif date_filter_mode == "Pick Specific Date (Calendar)" and chosen_calendar_date:
                target_date_str = chosen_calendar_date.strftime("%Y-%m-%d")

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
            selected_props = tuple(SPORT_PROPS_MAP.get(sport_key, []))

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

                event_id = ev.get("id")
                away_team = ev.get("away_team", "Away")
                home_team = ev.get("home_team", "Home")
                matchup = f"{away_team} @ {home_team}"
                formatted_time = dt.strftime("%b %d - %I:%M %p")

                game_intel = intel_map.get(
                    matchup,
                    intel_map.get(
                        f"{away_team.split()[-1]} @ {home_team.split()[-1]}",
                        {
                            "away_rec": "--", "home_rec": "--",
                            "away_p_name": "TBD", "away_p_hand": "RHP",
                            "away_p_l1": "No verified stats", "away_p_l2": "",
                            "home_p_name": "TBD", "home_p_hand": "RHP",
                            "home_p_l1": "No verified stats", "home_p_l2": "",
                            "headline": "Active Slate", "venue": f"{home_team} Stadium"
                        }
                    )
                )
                weather_info = fetch_weather(home_team)

                market_probs = {}
                playnow_lines = {}
                props_data = []

                bookmakers = list(ev.get("bookmakers", []))
                if market_scope == "Player and Team Props" and selected_props and event_id:
                    if use_mock_data:
                        prop_bms = generate_mock_props(sport_key, event_id)
                    else:
                        prop_bms = fetch_event_props(sport_key, event_id, selected_props)
                    bookmakers.extend(prop_bms)

                for bm in bookmakers:
                    bm_k = bm.get("key", "").lower()
                    is_sharp = any(k in bm_k for k in SHARP_BENCHMARKS)

                    for m in bm.get("markets", []):
                        m_key = m.get("key")
                        outcomes = m.get("outcomes", [])
                        valid_outcomes = [o for o in outcomes if o.get("price", 0) > 1.0]

                        # CRITICAL: player-prop markets pack every player's Over/Under
                        # into one flat outcomes list (e.g. McCaffrey Over, McCaffrey
                        # Under, Barkley Over, Barkley Under all under one "key"). If we
                        # devig that whole list together, the math forces all outcomes
                        # to sum to 100% as if they were one market — silently diluting
                        # each individual player's fair probability. We must only devig
                        # outcomes that belong to the SAME player + line together.
                        has_player_desc = any(o.get("description") for o in valid_outcomes)
                        if has_player_desc:
                            grouped = {}
                            for o in valid_outcomes:
                                gkey = (o.get("description", ""), o.get("point"))
                                grouped.setdefault(gkey, []).append(o)
                            outcome_groups = list(grouped.values())
                        else:
                            # Team markets (h2h/spreads/totals) already form one
                            # coherent market — devig as a whole (unchanged behavior).
                            outcome_groups = [valid_outcomes]

                        for group_outcomes in outcome_groups:
                            if len(group_outcomes) < 2:
                                continue
                            raw_p_list = [1.0 / o["price"] for o in group_outcomes]
                            devigged = power_devig(raw_p_list)

                            for idx, o in enumerate(group_outcomes):
                                player_desc = o.get("description", "")
                                point_val = o.get("point", None)
                                ident = f"{m_key}_{player_desc}_{o['name']}_{point_val}"

                                if is_sharp and idx < len(devigged):
                                    if ident not in market_probs:
                                        market_probs[ident] = []
                                    market_probs[ident].append((bm_k, devigged[idx]))

                                is_playnow = "playnow" in bm_k
                                is_prop_book = not is_sharp and m_key not in ["h2h", "spreads", "totals"]

                                if is_playnow or is_prop_book:
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
                                        "point": point_val,
                                        "price": o["price"],
                                        "market": m_key,
                                        "velocity": velocity,
                                        "ident": ident,
                                        "book": bm.get("title", "Market")
                                    }

                                    if m_key in ["h2h", "spreads", "totals"]:
                                        if is_playnow:
                                            playnow_lines[ident] = line_dict
                                    else:
                                        if not any(p["ident"] == ident for p in props_data):
                                            props_data.append(line_dict)

                compiled.append({
                    "id": event_id or matchup,
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
                st.success(f"Loaded {len(compiled)} Matchups with Full Visual Fidelity!")
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

        rendered_count = 0
        global_best_bets = {}  # category label -> list of priced bets, for the Top 20 board at the end
        for idx_g, g in enumerate(st.session_state.dossiers):
            intel = g["intel"]
            p_lines = g["playnow"]
            s_probs = g["sharp_probs"]

            def get_best_line(m_key, side_name):
                matching = [val for k, val in p_lines.items() if k.startswith(m_key) and side_name in val["name"]]
                if not matching:
                    return {"odds": "---", "prob": "---", "edge": "N/A", "point": "", "raw_prob": 0, "kelly": "---", "dec": 0, "edge_raw": None, "k_stake": 0, "color_cls": "color-unknown", "vel_html": ""}

                if is_mlb and m_key == "spreads":
                    standard = [m for m in matching if m["point"] is not None and abs(abs(m["point"]) - 1.5) < 0.01]
                    best_item = standard[0] if standard else matching[0]
                elif m_key == "totals":
                    best_item = min(matching, key=lambda x: abs(x["price"] - 1.91))
                else:
                    best_item = matching[0]

                dec = best_item["price"]
                k_ident = best_item["ident"]
                prob_entries = s_probs.get(k_ident, [])

                fair_p, edge_val, is_priced = compute_fair_and_edge(dec, prob_entries)

                pt_str = f" ({best_item['point']:+})" if best_item['point'] is not None else ""
                vel = best_item.get("velocity", "◼ STABLE")
                badge_class = "steam-badge-up" if "STEAM" in vel else ("steam-badge-down" if "DRIFT" in vel else "steam-badge-flat")

                if not is_priced:
                    # No sharp book has this market quoted. This is NOT a -EV result,
                    # it is genuinely unknown, and must be labeled as such.
                    return {
                        "odds": decimal_to_american(dec),
                        "prob": "N/A",
                        "edge": "Unpriced",
                        "point": pt_str,
                        "raw_prob": 0,
                        "kelly": f"${flat_unit:.2f} (Flat - Unpriced)",
                        "dec": dec,
                        "edge_raw": None,
                        "color_cls": "color-unknown",
                        "k_stake": flat_unit,
                        "vel_html": f"<span class='{badge_class}'>{vel}</span>"
                    }

                color_cls = "color-good" if edge_val > 0.5 else "color-bad"
                k_pct, k_stake = calculate_kelly(dec, fair_p, bankroll, kelly_fraction)
                kelly_str = f"${k_stake:.2f}" if k_stake > 0 else f"${flat_unit:.2f} (Flat)"

                return {
                    "odds": decimal_to_american(dec),
                    "prob": f"{fair_p*100:.1f}%",
                    "edge": f"+{edge_val:.1f}%" if edge_val >= 0 else f"{edge_val:.1f}%",
                    "point": pt_str,
                    "raw_prob": fair_p * 100,
                    "kelly": kelly_str,
                    "dec": dec,
                    "edge_raw": edge_val,
                    "color_cls": color_cls,
                    "k_stake": k_stake if k_stake > 0 else flat_unit,
                    "vel_html": f"<span class='{badge_class}'>{vel}</span>"
                }

            away_ml = get_best_line("h2h", g["away_team"])
            home_ml = get_best_line("h2h", g["home_team"])
            away_spread = get_best_line("spreads", g["away_team"])
            home_spread = get_best_line("spreads", g["home_team"])
            over_tot = get_best_line("totals", "Over")
            under_tot = get_best_line("totals", "Under")

            for line, cat, desc in [
                (away_ml, "Moneyline", f"{g['away_team']} ML"),
                (home_ml, "Moneyline", f"{g['home_team']} ML"),
                (away_spread, "Spread", f"{g['away_team']}{away_spread['point']}"),
                (home_spread, "Spread", f"{g['home_team']}{home_spread['point']}"),
                (over_tot, "Total", f"Over{over_tot['point']}"),
                (under_tot, "Total", f"Under{under_tot['point']}"),
            ]:
                if line["edge_raw"] is not None:
                    global_best_bets.setdefault(cat, []).append({
                        "matchup": g["matchup"],
                        "pick": desc,
                        "odds": line["odds"],
                        "fair": line["prob"],
                        "edge_raw": line["edge_raw"],
                        "edge_label": line["edge"],
                        "kelly": line["kelly"],
                    })

            all_lines = [away_ml, home_ml, away_spread, home_spread, over_tot, under_tot]
            priced_edges = [l["edge_raw"] for l in all_lines if l["edge_raw"] is not None]
            has_pos_ev = any(e > 0.5 for e in priced_edges)

            # Highlighting: Crisp 100% brightness always, with a distinct glowing border for positive edge
            if has_pos_ev:
                card_border = "2px solid #10b981"
                card_glow = "box-shadow: 0 0 20px rgba(16, 185, 129, 0.4);"
            else:
                card_border = "1px solid #334155"
                card_glow = "box-shadow: 0 8px 20px rgba(0, 0, 0, 0.5);"

            rendered_count += 1
            ml_hold = calculate_market_hold([away_ml["dec"], home_ml["dec"]])
            spread_hold = calculate_market_hold([away_spread["dec"], home_spread["dec"]])
            total_hold = calculate_market_hold([over_tot["dec"], under_tot["dec"]])

            best_edge = max(priced_edges) if priced_edges else None
            if best_edge is not None and best_edge >= 1.0:
                verdict_badge = "<span class='badge-verdict-good'>🎯 ACTIONABLE +EV VALUE PLAY</span>"
                if home_ml["edge_raw"] == best_edge:
                    top_play = f"Back <b class='color-good'>{g['home_team']} ML</b> (Edge: {home_ml['edge']} | Win Prob: {home_ml['prob']})"
                elif away_ml["edge_raw"] == best_edge:
                    top_play = f"Back <b class='color-good'>{g['away_team']} ML</b> (Edge: {away_ml['edge']} | Win Prob: {away_ml['prob']})"
                elif over_tot["edge_raw"] == best_edge:
                    top_play = f"Back <b class='color-good'>Over {over_tot['point']}</b> (Edge: {over_tot['edge']} | Win Prob: {over_tot['prob']})"
                elif under_tot["edge_raw"] == best_edge:
                    top_play = f"Back <b class='color-good'>Under {under_tot['point']}</b> (Edge: {under_tot['edge']} | Win Prob: {under_tot['prob']})"
                else:
                    top_play = f"Back Spread angle with edge: {best_edge:+.1f}%"
            elif not priced_edges:
                verdict_badge = "<span class='badge-verdict-unpriced'>❓ UNPRICED / NO SHARP CONSENSUS</span>"
                top_play = "No sharp benchmark book has quoted this market yet. Fair value cannot be verified — treat any PlayNow price here as unknown risk, not a pass."
            else:
                verdict_badge = "<span class='badge-verdict-pass'>🚫 PASS / NO MATHEMATICAL EDGE</span>"
                top_play = f"Market is fully juiced (Book holds: {ml_hold}% ML, {spread_hold}% Spread). No mathematical mispricing detected against sharp consensus."

            if is_mlb:
                tape_row_html = f"""<div class="tape-row">
<div class="scout-card">
    <div class="scout-title">Away Starter ({intel.get('away_p_hand', 'RHP')})</div>
    <div class="scout-name">⚾ {intel.get('away_p_name', 'TBD')}</div>
    <div class="scout-stat-line">{intel.get('away_p_l1', 'No verified stats')}</div>
    <div class="scout-stat-sub">{intel.get('away_p_l2', '')}</div>
</div>
<div class="scout-card">
    <div class="scout-title">Home Starter ({intel.get('home_p_hand', 'RHP')})</div>
    <div class="scout-name">⚾ {intel.get('home_p_name', 'TBD')}</div>
    <div class="scout-stat-line">{intel.get('home_p_l1', 'No verified stats')}</div>
    <div class="scout-stat-sub">{intel.get('home_p_l2', '')}</div>
</div>
</div>"""
                context_summary = f"Starting Pitchers: <b>{intel.get('away_p_name', 'TBD')} ({intel.get('away_p_hand', '')}) vs {intel.get('home_p_name', 'TBD')} ({intel.get('home_p_hand', '')})</b>. Weather: <b>{g['weather']}</b>."
            elif is_nfl:
                tape_row_html = f"""<div class="tape-row">
<div class="scout-card">
    <div class="scout-title">Away Team ({intel.get('away_rec', '--')})</div>
    <div class="scout-name">🏈 {g['away_team']}</div>
    <div class="scout-stat-line">{intel.get('headline', 'Trench & Injury Profile')}</div>
</div>
<div class="scout-card">
    <div class="scout-title">Home Team ({intel.get('home_rec', '--')})</div>
    <div class="scout-name">🏈 {g['home_team']}</div>
    <div class="scout-stat-line">Stadium Weather • {g['weather']}</div>
</div>
</div>"""
                context_summary = f"Matchup notes: <b>{intel.get('headline', 'NFL Game')}</b>. Venue: <b>{intel.get('venue', 'Stadium')}</b>."
            else:
                tape_row_html = ""
                context_summary = f"Venue: <b>{intel.get('venue', 'Arena')}</b>."

            # Dossier card with 100% full brightness and crisp contrast
            dossier_html = f"""<div class="game-dossier" style="background: linear-gradient(145deg, rgba(15, 23, 42, 0.95) 0%, rgba(11, 15, 25, 0.98) 100%); border: {card_border}; {card_glow}">
<div class="dossier-header">
<div>
<div class="matchup-headline">{g['matchup']} &nbsp;{verdict_badge}</div>
<div class="matchup-records">{g['away_team']} ({intel.get('away_rec', '--')}) vs {g['home_team']} ({intel.get('home_rec', '--')}) • 🏟️ {intel.get('venue', 'Stadium')}</div>
</div>
<div class="weather-badge">🌤️ {g['weather']}</div>
</div>
{tape_row_html}
<table class="market-table">
<thead>
<tr>
<th>Team / Side</th>
<th>Moneyline (Fair Prob) <span class="hold-badge">Hold: {ml_hold}%</span></th>
<th>{spread_label} <span class="hold-badge">Hold: {spread_hold}%</span></th>
<th>Total (O/U) <span class="hold-badge">Hold: {total_hold}%</span></th>
<th>Edge / Kelly Sizing</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align:left; font-weight:700;">{g['away_team']}</td>
<td><span class="{away_ml['color_cls']}">{away_ml['odds']}</span><br><span style="color:#94a3b8; font-size:10px;">({away_ml['prob']})</span><br>{away_ml['vel_html']}</td>
<td><span class="{away_spread['color_cls']}">{away_spread['point']} {away_spread['odds']}</span><br><span style="color:#94a3b8; font-size:10px;">({away_spread['prob']})</span></td>
<td><span class="{over_tot['color_cls']}">Over {over_tot['point']} {over_tot['odds']}</span><br><span style="color:#94a3b8; font-size:10px;">({over_tot['prob']})</span></td>
<td><span class="{away_ml['color_cls']}">{away_ml['edge']}</span><br><span class="highlight-kelly">{away_ml['kelly']}</span></td>
</tr>
<tr>
<td style="text-align:left; font-weight:700;">{g['home_team']}</td>
<td><span class="{home_ml['color_cls']}">{home_ml['odds']}</span><br><span style="color:#94a3b8; font-size:10px;">({home_ml['prob']})</span><br>{home_ml['vel_html']}</td>
<td><span class="{home_spread['color_cls']}">{home_spread['point']} {home_spread['odds']}</span><br><span style="color:#94a3b8; font-size:10px;">({home_spread['prob']})</span></td>
<td><span class="{under_tot['color_cls']}">Under {under_tot['point']} {under_tot['odds']}</span><br><span style="color:#94a3b8; font-size:10px;">({under_tot['prob']})</span></td>
<td><span class="{home_ml['color_cls']}">{home_ml['edge']}</span><br><span class="highlight-kelly">{home_ml['kelly']}</span></td>
</tr>
</tbody>
</table>"""

            # Render dossier container
            st.markdown(dossier_html, unsafe_allow_html=True)

            # Sport-Specific Categorized Props with Hit Tracker
            if market_scope == "Player and Team Props":
                if g["props"]:
                    st.markdown("<div style='font-size: 13px; font-weight: 800; color: #38bdf8; margin: 8px 0 6px 0;'>🎯 Categorized Player Prop Intelligence</div>", unsafe_allow_html=True)

                    active_sport_categories = SPORT_SPECIFIC_CATEGORIES.get(sport_key, {})
                    active_cats = {}
                    for cat_label, sub_keys in active_sport_categories.items():
                        c_props = [p for p in g["props"] if any(k in p["market"].lower() for k in sub_keys)]
                        if c_props:
                            active_cats[cat_label] = c_props

                    if active_cats:
                        prop_tabs = st.tabs(list(active_cats.keys()))
                        for idx_tab, (c_name, c_props_list) in enumerate(active_cats.items()):
                            with prop_tabs[idx_tab]:
                                evaluated_props = []
                                for p in c_props_list:
                                    p_dec = p["price"]
                                    p_ident = p["ident"]
                                    p_prob_entries = s_probs.get(p_ident, [])
                                    p_fair, p_edge, p_is_priced = compute_fair_and_edge(p_dec, p_prob_entries)

                                    # Pull REAL historical Last 5 performance trend
                                    # (sample-mode uses a clearly-labeled placeholder instead of real API calls)
                                    if use_mock_data:
                                        last_5_metric = generate_mock_last5(p["description"], p["market"], p.get("point"), sport_key)
                                    else:
                                        last_5_metric = fetch_player_last_5(p["description"], p["market"], p.get("point"), sport_key)

                                    if not p_is_priced:
                                        evaluated_props.append({
                                            **p,
                                            "fair": 0,
                                            "edge": None,
                                            "stake": flat_unit,
                                            "last_5": last_5_metric,
                                            "color_cls": "color-unknown",
                                            "edge_label": "Unpriced",
                                            "fair_label": "N/A"
                                        })
                                        continue

                                    k_pct, k_stake = calculate_kelly(p_dec, p_fair, bankroll, kelly_fraction)
                                    evaluated_props.append({
                                        **p,
                                        "fair": p_fair,
                                        "edge": p_edge,
                                        "stake": k_stake if k_stake > 0 else flat_unit,
                                        "last_5": last_5_metric,
                                        "color_cls": "color-good" if p_edge > 0.5 else "color-bad",
                                        "edge_label": f"{p_edge:+.1f}%",
                                        "fair_label": f"{p_fair*100:.1f}%"
                                    })
                                    global_best_bets.setdefault(c_name, []).append({
                                        "matchup": g["matchup"],
                                        "pick": f"{p['description']} {p['name']} {p.get('point', '')}",
                                        "odds": decimal_to_american(p_dec),
                                        "fair": f"{p_fair*100:.1f}%",
                                        "edge_raw": p_edge,
                                        "edge_label": f"{p_edge:+.1f}%",
                                        "kelly": f"${(k_stake if k_stake > 0 else flat_unit):.2f}",
                                    })

                                # Sort priced props by edge (desc); push unpriced to the bottom.
                                evaluated_props.sort(key=lambda x: (x["edge"] is None, -(x["edge"] or 0)))
                                top_priced = [p for p in evaluated_props if p["edge"] is not None]

                                if top_priced:
                                    top_p = top_priced[0]
                                    st.markdown(f"""
                                    <div class="top-pick-banner">
                                        ⭐ <b>Top Value in {c_name}:</b> {top_p['description']} <b>{top_p['name']} {top_p.get('point', '')}</b> ({decimal_to_american(top_p['price'])}) 
                                        • <span class="last-5-badge">{top_p['last_5']}</span> • Sharp Win Prob: <b>{top_p['fair_label']}</b> • True Edge: <b class="{top_p['color_cls']}">{top_p['edge_label']}</b>
                                    </div>
                                    """, unsafe_allow_html=True)
                                else:
                                    st.markdown("""
                                    <div class="top-pick-banner" style="border-color:#475569;">
                                        ❓ No props in this category have sharp-book coverage yet — value cannot be verified.
                                    </div>
                                    """, unsafe_allow_html=True)

                                p_table_rows = ""
                                for p in evaluated_props[:8]:
                                    pt_lbl = f"{p['point']}" if p['point'] is not None else ""
                                    p_table_rows += f"""<tr>
                                    <td style="text-align:left;"><b>{p['description']}</b><br><span class="last-5-badge">{p['last_5']}</span></td>
                                    <td>{p['name']} {pt_lbl}</td>
                                    <td><span class="{p['color_cls']}">{decimal_to_american(p['price'])}</span></td>
                                    <td>{p['fair_label']}</td>
                                    <td><span class="{p['color_cls']}">{p['edge_label']}</span></td>
                                    <td><span class="highlight-kelly">${p['stake']:.2f}</span></td>
                                    </tr>"""

                                st.markdown(f"""
                                <table class="market-table">
                                <thead>
                                <tr>
                                <th>Player / Last 5</th>
                                <th>Selection</th>
                                <th>Odds</th>
                                <th>Fair %</th>
                                <th>True Edge</th>
                                <th>Wager</th>
                                </tr>
                                </thead>
                                <tbody>{p_table_rows}</tbody>
                                </table>
                                """, unsafe_allow_html=True)
                    else:
                        st.caption("No active props found for this category.")
                else:
                    st.markdown("""<div style="background: rgba(15, 23, 42, 0.5); border: 1px dashed #334155; border-radius: 6px; padding: 8px 12px; margin: 8px 0; font-size: 11.5px; color: #94a3b8;">
                    🎯 <b>Player Props:</b> Awaiting oddsmaker posting for this slate.
                    </div>""", unsafe_allow_html=True)

            st.markdown(f"""<div class="intel-box">
            💡 <b>System Intelligence & Recommendation:</b> Game Time: <b>{g['time']} SK</b>. {context_summary} <b>Verdict:</b> {top_play}.
            </div></div>""", unsafe_allow_html=True)

            # 1-Click Action Bar
            st.caption(f"⚡ 1-Click Bet Router for {g['matchup']}")
            c_btn_a, c_btn_b, c_btn_c, c_btn_d = st.columns(4)

            if away_ml["dec"] > 1.0:
                btn_lbl = f"⚡ {g['away_team']} ML ({away_ml['odds']}) [${away_ml['k_stake']:.2f}]"
                if c_btn_a.button(btn_lbl, key=f"btn_away_ml_{idx_g}"):
                    log_quick_bet(g["matchup"], f"{g['away_team']} ML", away_ml["odds"], away_ml["k_stake"], f"Edge: {away_ml['edge']} | Hold: {ml_hold}%")

            if home_ml["dec"] > 1.0:
                btn_lbl = f"⚡ {g['home_team']} ML ({home_ml['odds']}) [${home_ml['k_stake']:.2f}]"
                if c_btn_b.button(btn_lbl, key=f"btn_home_ml_{idx_g}"):
                    log_quick_bet(g["matchup"], f"{g['home_team']} ML", home_ml["odds"], home_ml["k_stake"], f"Edge: {home_ml['edge']} | Hold: {ml_hold}%")

            if over_tot["dec"] > 1.0:
                btn_lbl = f"⚡ Over {over_tot['point']} ({over_tot['odds']}) [${over_tot['k_stake']:.2f}]"
                if c_btn_c.button(btn_lbl, key=f"btn_over_{idx_g}"):
                    log_quick_bet(g["matchup"], f"Over {over_tot['point']}", over_tot["odds"], over_tot["k_stake"], f"Edge: {over_tot['edge']} | Hold: {total_hold}%")

            if under_tot["dec"] > 1.0:
                btn_lbl = f"⚡ Under {under_tot['point']} ({under_tot['odds']}) [${under_tot['k_stake']:.2f}]"
                if c_btn_d.button(btn_lbl, key=f"btn_under_{idx_g}"):
                    log_quick_bet(g["matchup"], f"Under {under_tot['point']}", under_tot["odds"], under_tot["k_stake"], f"Edge: {under_tot['edge']} | Hold: {total_hold}%")

            st.markdown("---")

        # --- TOP 20 BEST BETS BY CATEGORY (aggregated across the whole scanned board) ---
        if global_best_bets:
            st.markdown("## 🏆 Top Value Board — Best Bets by Category")
            st.caption("Every priced bet across all scanned games, ranked by True Edge %. Unpriced markets are excluded (no verified fair value to rank them by).")
            for cat_name, bets in global_best_bets.items():
                bets_sorted = sorted(bets, key=lambda b: b["edge_raw"], reverse=True)[:20]
                with st.expander(f"{cat_name} — Top {len(bets_sorted)}", expanded=False):
                    rows = ""
                    for b in bets_sorted:
                        color = "color-good" if b["edge_raw"] > 0.5 else "color-bad"
                        rows += f"""<tr>
                        <td style="text-align:left;">{b['matchup']}</td>
                        <td style="text-align:left;"><b>{b['pick']}</b></td>
                        <td>{b['odds']}</td>
                        <td>{b['fair']}</td>
                        <td><span class="{color}">{b['edge_label']}</span></td>
                        <td><span class="highlight-kelly">{b['kelly']}</span></td>
                        </tr>"""
                    st.markdown(f"""
                    <table class="market-table">
                    <thead><tr><th>Matchup</th><th>Pick</th><th>Odds</th><th>Fair %</th><th>True Edge</th><th>Wager</th></tr></thead>
                    <tbody>{rows}</tbody>
                    </table>
                    """, unsafe_allow_html=True)

    else:
        st.info("Click '⚡ Scan Board' in the sidebar to populate active game dossiers.")

# --- PARLAY ARCHITECT TAB ---
with tab_parlays:
    st.markdown("### ⚡ Correlation-Safe Parlay Architect")
    st.caption("Cross-game parlay builder with Kelly and Alternate Line Floor Leg integration.")

    candidate_legs = []
    if st.session_state.dossiers:
        for g in st.session_state.dossiers:
            # Mainlines
            for k, val in g["playnow"].items():
                if 1.05 < val["price"] < 3.50:
                    prob_entries = g["sharp_probs"].get(k, [])
                    fair_p, edge_calc, is_priced = compute_fair_and_edge(val["price"], prob_entries)
                    if not is_priced:
                        # Unpriced legs are still eligible for parlays (implied prob is
                        # the best available estimate), but tagged as unverified.
                        fair_p = 1.0 / val["price"]
                        leg_tag = "Unverified Leg"
                    elif fair_p >= 0.45 or val["price"] <= 1.45:
                        leg_tag = "Floor Leg" if val["price"] <= 1.45 else "Standard Leg"
                    else:
                        continue
                    candidate_legs.append({
                        "game_id": g["id"],
                        "matchup": g["matchup"],
                        "pick": f"[{leg_tag}] {g['matchup']} ➔ {val['name']} ({decimal_to_american(val['price'])})",
                        "dec": val["price"],
                        "prob": fair_p,
                        "edge": edge_calc if is_priced else None
                    })
            # Player Props
            for p in g.get("props", []):
                if 1.25 < p["price"] < 3.00:
                    prob_entries = g["sharp_probs"].get(p["ident"], [])
                    fair_p, edge_calc, is_priced = compute_fair_and_edge(p["price"], prob_entries)
                    if not is_priced:
                        fair_p = 1.0 / p["price"]
                        leg_tag = "Unverified Prop"
                    else:
                        leg_tag = "Floor Prop" if p["price"] <= 1.50 else "Value Prop"
                    candidate_legs.append({
                        "game_id": g["id"],
                        "matchup": g["matchup"],
                        "pick": f"[{leg_tag}] {p['description']} ➔ {p['name']} {p.get('point', '')} ({decimal_to_american(p['price'])})",
                        "dec": p["price"],
                        "prob": fair_p,
                        "edge": edge_calc if is_priced else None
                    })

    if len(candidate_legs) >= 2:
        leg_labels = [c["pick"] for c in candidate_legs]
        selected_picks = st.multiselect("Select 2 to 4 Distinct Legs (Mix Floor Anchors & Value Legs)", options=leg_labels, default=leg_labels[:2], key="parlay_multiselect")

        if len(selected_picks) >= 2:
            chosen = [candidate_legs[leg_labels.index(p)] for p in selected_picks]
            game_ids = [c["game_id"] for c in chosen]
            is_correlated = len(game_ids) != len(set(game_ids))

            if is_correlated:
                st.warning("⚠️ Same-Game Correlation Warning: Multiple legs from the same game detected. PlayNow applies custom SGP covariance.")

            total_dec = 1.0
            joint_prob = 1.0
            for c in chosen:
                total_dec *= c["dec"]
                joint_prob *= c["prob"]

            parlay_us = decimal_to_american(total_dec)
            parlay_edge = ((total_dec * joint_prob) - 1.0) * 100
            k_pct, parlay_kelly = calculate_kelly(total_dec, joint_prob, bankroll, kelly_fraction)
            p_final_stake = parlay_kelly if parlay_kelly > 0 else flat_unit
            parlay_color = "#10b981" if parlay_edge >= 0 else "#f87171"

            any_unverified = any(c["edge"] is None for c in chosen)
            unverified_note = " ⚠️ Includes unverified (unpriced) legs — treat this parlay's edge as an estimate, not a confirmed number." if any_unverified else ""

            st.markdown(f"""<div class="game-dossier" style="background: rgba(15, 23, 42, 0.95); border: 2px solid {parlay_color};">
<div class="matchup-headline">Combined Multi-Leg Ticket ({parlay_us})</div>
<div style="font-size: 12px; color: #94a3b8; margin-bottom: 10px;">{' + '.join([c['pick'] for c in chosen])}</div>
<div class="tape-row">
<div class="scout-card">
    <div class="scout-title">Combined Odds & Edge</div>
    <div style="font-size: 15px; font-weight: 800; color: #ffffff;">{parlay_us} ({total_dec:.2f} Dec)</div>
    <div style="font-size: 11px; font-family: 'JetBrains Mono', monospace; color: {parlay_color}; margin-top: 2px;">Edge: {parlay_edge:+.1f}% • Compound Win Prob: {round(joint_prob * 100, 1)}%{unverified_note}</div>
</div>
<div class="scout-card">
    <div class="scout-title">Suggested Wager ({'Kelly' if parlay_kelly > 0 else 'Option B Flat'})</div>
    <div style="font-size: 15px; font-weight: 800; color: #38bdf8;">${p_final_stake:.2f} CAD</div>
    <div style="font-size: 11px; font-family: 'JetBrains Mono', monospace; color: #10b981; margin-top: 2px;">Est. Payout: ${round(p_final_stake * total_dec, 2)} CAD</div>
</div>
</div>
</div>""", unsafe_allow_html=True)

            if st.button(f"⚡ 1-Click Record Parlay Ticket (${p_final_stake:.2f})", type="primary", key="parlay_one_click_btn"):
                log_quick_bet(
                    f"{len(chosen)}-Leg Parlay",
                    " + ".join([c["pick"] for c in chosen]),
                    parlay_us,
                    p_final_stake,
                    f"Joint Prob: {round(joint_prob*100, 1)}% | Edge: {parlay_edge:+.1f}% | SGP Correlated: {is_correlated}"
                )
    else:
        st.info("Scan the board to generate candidate parlay legs.")

# --- GOOGLE SHEET VIEWER & CLV AUDITOR ---
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
