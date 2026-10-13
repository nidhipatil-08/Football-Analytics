# PitchIQ — Football Performance Intelligence

PitchIQ is an interactive football (soccer) player analytics dashboard built with Python, Pandas, NumPy, Streamlit and Plotly. It provides overview KPIs, player comparisons, team summaries, position analysis, sidebar filters, a searchable statistics table and filtered CSV downloads.

> **Important: Synthetic demo data.** `football_players.csv` is generated for demonstration and educational use. It does not represent real players, real clubs, or actual football results. Player names and statistics are synthetic.

## Features

- Four dashboard sections: Overview, Player Analysis, Team Analysis and Position Analysis
- KPI cards for unique players, goals, assists, minutes played and average rating
- Global season, team, position and player filters
- Goals-versus-assists and shots-versus-goals scatter plots
- Player comparison chart and summary
- Team-level goals, assists, unique player counts, minutes and average ratings
- Position-level summaries and rating distributions
- Searchable player-season statistics table
- CSV export of filtered records
- Validation for required columns, numeric values, impossible ranges and duplicate player-season rows
- Clear empty-result and data-loading messages
- Dark, football-inspired green UI

## Project files

```text
PitchIQ/
├── app.py
├── football_players.csv
├── requirements.txt
└── README.md
```

## Dataset schema

The CSV contains one row per player per season. It includes 144 unique synthetic players across eight synthetic teams and three seasons (432 player-season records).

| Column | Description |
|---|---|
| `player_id` | Stable player identifier |
| `player_name` | Synthetic player name |
| `team` | Synthetic team assignment |
| `season` | Season label |
| `position` | Goalkeeper, Defender, Midfielder or Forward |
| `age` | Player age |
| `matches_played` | Appearances in that season |
| `minutes_played` | Minutes played in that season |
| `goals` | Goals in that season |
| `assists` | Assists in that season |
| `shots` | Total shots attempted |
| `shots_on_target` | Shots on target |
| `passes_completed` | Completed passes |
| `tackles` | Tackles made |
| `clean_sheets` | Matches without conceding a goal |
| `rating` | Synthetic rating on a 1–10 scale; a few values are intentionally missing to demonstrate missing-value handling |

### KPI and metric definitions

- **Total players:** count of distinct `player_id` values in the filtered data.
- **Total goals / assists:** sum of goals / assists in filtered player-season records.
- **Total minutes played:** sum of `minutes_played` in filtered records.
- **Average rating:** mean rating, excluding missing values.
- **Goal contributions:** goals + assists.
- **Goals per 90 / assists per 90:** goals or assists divided by minutes played, multiplied by 90.
- **Shot conversion:** goals divided by shots, multiplied by 100. Records with zero shots have no conversion value.
- **Average minutes per appearance:** minutes divided by matches played. Records with zero appearances have no rate.

Because records are per player-season, selecting multiple seasons aggregates across those seasons. The player KPI counts unique players rather than rows. Team totals are aggregates of synthetic player records, not official team results.

## Requirements

- Python 3.10 or newer recommended
- pip
- Internet access for the initial package installation (the app itself makes no API calls)

## Run locally

### 1. Download or clone the project

If you have the project in a Git repository:

```bash
git clone <your-repository-url>
cd PitchIQ
```

Alternatively, download the four project files and place them in the same folder.

### 2. Create a virtual environment

**Windows (PowerShell or Command Prompt):**

```bash
python -m venv .venv
.venv\Scripts\activate
```

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Start Streamlit

Run this command from the project folder:

```bash
streamlit run app.py
```

Streamlit will print a local URL, usually `http://localhost:8501`, which you can open in your browser.

## Deploy with Streamlit Community Cloud

1. Create a GitHub repository and upload `app.py`, `football_players.csv`, `requirements.txt` and `README.md`.
2. Sign in to Streamlit Community Cloud using your GitHub account.
3. Create a new app and select your repository and branch.
4. Set the main file path to `app.py`.
5. Deploy the app.
6. Open the deployed URL and test the filters, charts and CSV download.

No API keys or secrets are required. Keep the CSV in the same directory as `app.py`.

## Validation and limitations

- The app checks for the CSV file and required columns.
- Numeric columns are converted to numeric types; invalid numeric values become missing.
- Rows missing essential identity fields are excluded.
- Duplicate `player_id` + `season` rows are deduplicated.
- Negative counts, invalid ratings, shots-on-target greater than shots, and clean sheets greater than appearances are handled as invalid/missing values.
- Derived rates guard against division by zero.
- Missing ratings are not treated as zero.
- An empty filter result produces a helpful message.
- Statistics and ratings are synthetic and must not be used for real scouting, betting, recruitment or performance decisions.

## Possible future improvements

- Add team crests and player portraits from licensed sources
- Add a season-over-season trend page
- Add more robust position-specific metrics
- Allow users to upload their own CSV after schema validation
- Add unit tests and automated data-quality checks
- Compare players using per-90 metrics and minimum-minutes thresholds

## License

This project is intended as a learning and portfolio project. Confirm appropriate licensing before replacing the synthetic dataset with any third-party football data.
