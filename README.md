# Football Match & Opposition Analysis: Spain at UEFA Euro 2024

A complete opposition-analysis workflow of the kind a club performance analyst delivers before a match:
event-data analysis, a Nacsport coding and clip plan, a written report and a coaching-staff presentation.
It is built as if our team plays Spain next, using all 7 of Spain's Euro 2024 matches.

> **Data:** StatsBomb Open Data (free for non-commercial use with attribution), https://github.com/statsbomb/open-data.
> This is a non-confidential sample report.

## Interactive dashboard

Run `streamlit run app.py` (full setup steps in [How to run](#how-to-run)). Pick **any of the 24 Euro 2024 teams** as the opponent (data downloads automatically on first use), filter by match,
and explore nine tabs:

| Tab | What you can do |
|---|---|
| Overview | KPI cards, match-by-match xG / possession / PPDA chart, KPI table (CSV download) |
| Shots | Interactive shot map with hover details; filter by side, situation (open play, set pieces, penalties) and player |
| Build-up | Pass network for any match, final-third entries by channel, top progressive passers |
| Pressing | Defensive-action heatmap, PPDA and high regains by match |
| Set pieces | Corner delivery map, set-piece shots and xG, corner takers |
| Players | Full player table, key-threat heatmaps (choose up to 3), interactive player action map |
| Match view | xG timeline and key stats for one match |
| Video clips | Filter the timecoded clip list by category, match and player; download for Nacsport |
| Report | Auto-written opposition summary with suggested focus points (Markdown download) |

## Deliverables

| File | What it is |
|---|---|
| `reports/Opposition_Report_Spain_Euro2024.pptx` / `.pdf` | 12-slide presentation for coaching staff |
| `reports/Opposition_Report_Spain.md` | Written opposition report with game-plan recommendations |
| `outputs/figures/` | Shot maps, pass network, final-third entries, pressing heatmap, corners, key-player heatmaps, xG timeline, match KPIs |
| `nacsport/Code_Window_Template.md` | Nacsport code window: categories, lead/lag times and descriptors |
| `nacsport/clip_playlist.csv` | 369 timecoded moments (shots, goals, box entries, high regains, corners) for clip preparation |
| `nacsport/timeline_*.xml` | Sportscode-style XML timelines per match, for tools that import them |
| `outputs/match_kpis.csv`, `player_stats.csv` | Team and player metrics |

## Key findings

- **Control:** 7 wins, 15 goals for and 4 against; 58% average possession, 87% pass completion, 65% field tilt.
- **Wide threat:** 49% of final-third entries come down Spain's left and 37% down the right; only 14% centrally.
- **Pressing:** average PPDA 15.2 and 22 high regains per match, with 34% of defensive actions in the attacking third.
- **Weakness:** in the 3 matches where Spain's press dropped (PPDA above 18) they conceded 1.65 xG per match, against 0.37 in the other four.
- **Key threats:** Lamine Yamal (2.15 xA, 18 key passes, 45 progressive carries), Nico Williams (15 successful dribbles) and Dani Olmo (3 goals).
- **Set pieces:** 25 of 45 corners inswinging; 35 shots and 3.2 xG from set-piece phases.

## Metrics used

- **xG / xA:** StatsBomb expected goals; xA = xG of shots created by a player's pass.
- **PPDA:** opponent passes in their own 60% of the pitch divided by Spain's tackles, interceptions and fouls there (lower = more intense press).
- **Field tilt:** Spain's share of all passes played in the final third.
- **Progressive pass / carry:** moves the ball at least 25% closer to the centre of goal and ends in the opponent's half.
- **High regain:** ball recovery or interception in the attacking 40% of the pitch.

## Workflow

1. `src/download_data.py` downloads matches, events and lineups from StatsBomb Open Data.
2. `src/analysis.py` computes KPIs and player stats and draws every chart with mplsoccer.
3. `src/nacsport_export.py` turns key events into timecoded clip lists and XML timelines
   (set each match's video offsets in `OFFSETS` so clips line up with your footage).
4. `src/report.py` writes the opposition report.
5. `reports/build_deck.js` builds the PowerPoint (Node.js + pptxgenjs).

Video coding in Nacsport follows `nacsport/Code_Window_Template.md`: code the full match, then use the clip
list to cut playlists by phase of play and key player.

## How to run

### 1. Install (first time only)

- **Python 3.10 or newer** from [python.org](https://www.python.org/downloads/). On Windows, tick **"Add Python to PATH"** during installation.
- **Node.js** from [nodejs.org](https://nodejs.org/), only needed to rebuild the PowerPoint deck.

### 2. Open a terminal in the project folder

- **Windows:** open the folder, click the address bar, type `cmd` and press Enter.
- **Mac:** right-click the folder and choose **New Terminal at Folder**.

### 3. Create a virtual environment and install the libraries

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Mac / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

On Mac, use `python3` instead of `python` if needed.

### 4. Run the analysis

```bash
python run.py
```

This downloads Spain's 7 Euro 2024 matches from StatsBomb into `data/` (internet needed, about a minute),
calculates the stats, draws every chart in `outputs/figures/`, creates the Nacsport clip lists in `nacsport/`
and writes `reports/Opposition_Report_Spain.md`.

### 5. Open the interactive dashboard

```bash
streamlit run app.py
```

It opens in your browser at `http://localhost:8501`. Pick any Euro 2024 team in the sidebar; its data
downloads automatically the first time. Stop the dashboard with `Ctrl + C` in the terminal.

### 6. Rebuild the PowerPoint (optional)

```bash
npm install pptxgenjs
node reports/build_deck.js
```

### Analyse a different team

Change `TEAM = "Spain"` in `src/analysis.py` (for example to `"England"`), then run:

```bash
python src/download_data.py England
python run.py
```

The dashboard does this automatically: just pick the team in the sidebar.

### Line clips up with your Nacsport video

StatsBomb timestamps restart at 00:00 each half. Find the kick-off time of each half in your video file and add it
to `OFFSETS` in `src/nacsport_export.py`, for example `{"Spain vs England": {1: 35, 2: 3210}}`, then run
`python src/nacsport_export.py`. The clip times in `nacsport/clips_*.csv` and `timeline_*.xml` will match your footage.

### Troubleshooting

| Problem | Fix |
|---|---|
| `python is not recognized` | Reinstall Python and tick "Add Python to PATH" |
| `No module named mplsoccer` (or streamlit) | Activate the virtual environment, then run `pip install -r requirements.txt` again |
| Data download fails | Check your internet connection; the data comes from GitHub |
| Dashboard port already in use | Run `streamlit run app.py --server.port 8502` |

### Deploy the dashboard online (free)

Push the project to GitHub, sign in at [share.streamlit.io](https://share.streamlit.io), choose the repository and
set the main file to `app.py`. You get a public link to share.

## Tools

Nacsport, StatsBomb Open Data, Python (Pandas, NumPy, Matplotlib, mplsoccer), Streamlit, Plotly, PowerPoint.
