# Nacsport Code Window: Opposition Analysis Template

Use this layout to code full matches of the opponent in Nacsport. Each **category** is a button
(lead / lag in seconds); **descriptors** are added to the clip after it is created.

## Categories (buttons)

| Category | Lead | Lag | When to press it |
|---|---|---|---|
| Build-up (own third) | 5 | 10 | Opponent GK or centre-backs start a possession |
| Progression (middle third) | 5 | 8 | Ball played or carried into the middle third under control |
| Final-third entry | 6 | 8 | Completed pass or carry into the final third |
| Box entry | 6 | 6 | Ball enters the penalty area |
| Shot | 8 | 4 | Any shot (descriptor: on target / off target / blocked / goal) |
| High press | 4 | 8 | Opponent presses our build-up in our defensive third |
| Mid / low block | 4 | 10 | Opponent sets a compact block |
| Regain (high) | 6 | 8 | Opponent wins the ball in our half |
| Attacking transition | 2 | 12 | Opponent wins the ball and attacks immediately |
| Defensive transition | 2 | 10 | Opponent loses the ball; reaction in first 5 seconds |
| Corner for | 3 | 12 | Opponent corner (descriptor: inswing / outswing / short) |
| Free kick for | 3 | 12 | Opponent attacking free kick |
| Corner against / free kick against | 3 | 12 | Our set pieces, to see their defensive set-up |

## Descriptors

- **Channel:** Left / Centre / Right (from the opponent's attacking direction)
- **Outcome:** Successful / Unsuccessful / Shot / Goal / Foul won
- **Key player:** one button per key player (e.g. Lamine Yamal, Nico Williams, Dani Olmo, Rodri, Pedri)
- **Structure:** 4-2-3-1 / 4-3-3 / back three in build-up

## Output for coaches

1. Playlist per phase: build-up, progression, chance creation, pressing, transitions, set pieces.
2. 6-10 clips per playlist, labelled with minute and key player, drawn with arrows and zones.
3. Two- to three-minute "key threats" reel per key player.

`clip_playlist.csv` lists 369 timecoded moments from StatsBomb event data (shots, goals, box entries,
high regains and corners). Use it to jump straight to each moment when cutting clips, or run
`python src/nacsport_export.py` to generate Sportscode-style XML timelines (set video offsets first).
