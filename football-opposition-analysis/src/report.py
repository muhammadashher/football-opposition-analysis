"""Write reports/Opposition_Report_Spain.md from outputs/metrics.json and match KPIs."""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
m = json.loads((ROOT / "outputs" / "metrics.json").read_text())
k = pd.read_csv(ROOT / "outputs" / "match_kpis.csv")
pl = pd.read_csv(ROOT / "outputs" / "player_stats.csv", index_col=0)
hi, lo = k[k.ppda > 18], k[k.ppda <= 18]
lane = m["lane_share"]
P = lambda x: f"{x * 100:.0f}%"

rows = "\n".join(f"| {r.match} | {r.formation} | {P(r.possession)} | {r.xg:.2f} | {r.xg_against:.2f} | "
                 f"{r.ppda:.1f} | {P(r.field_tilt)} |" for r in k.itertuples())
prow = "\n".join(f"| {n} | {int(r.goals)} | {r.xg:.2f} | {r.xa:.2f} | {int(r.key_passes)} | {int(r.prog_carries)} | "
                 f"{int(r.dribbles)} |" for n, r in pl.head(6).iterrows())

md = f"""# Opposition Report: Spain (UEFA Euro 2024)

> Non-confidential sample analysis built on StatsBomb Open Data (all 7 Spain matches). Prepared as if our
> team faces Spain next. Video clips were cut in Nacsport using the timecoded playlist in `nacsport/`.

## 1. Summary for the coaching staff

- **Profile:** 7 wins from 7, {m['goals']} goals scored and {m['goals_against']} conceded, {m['xg']:.1f} xG for vs {m['xg_against']:.1f} against.
  Spain control games: {P(m['possession'])} average possession, {P(m['pass_completion'])} pass completion and {P(m['field_tilt'])} field tilt.
- **Shape:** 4-2-3-1 in {m['formations'].get('4231', 0)} of 7 matches (4-3-3 in {m['formations'].get('433', 0)}), with Rodri and Fabián Ruiz as the double pivot.
- **Main threat:** wide play. {P(lane['Left'])} of final-third entries arrive down Spain's left (Nico Williams, Cucurella) and
  {P(lane['Right'])} down the right (Lamine Yamal, Carvajal); only {P(lane['Centre'])} come through the centre.
- **Weakness:** when Spain cannot control the ball they are far more open. In the 3 matches where their PPDA
  was above 18 (Croatia, Germany, France) they conceded **{hi.xg_against.mean():.2f} xG per match**, against
  **{lo.xg_against.mean():.2f}** in the other four.

## 2. Match by match

| Match | Formation | Possession | xG | xG against | PPDA | Field tilt |
|---|---|---|---|---|---|---|
{rows}

## 3. Build-up and chance creation

- {m['final_third_entries']} completed passes into the final third ({m['prog_passes_pm']:.0f} progressive passes per match).
- In the final, the strongest passing links ran through Laporte, Le Normand and Rodri, while Cucurella pushed high on the left so Nico Williams could isolate defenders 1v1.
- {m['shots']} shots for {m['xg']:.1f} xG (0.09 xG per shot); most shots come from central zones inside the box.

## 4. Pressing and transitions

- Average PPDA {m['ppda']:.1f}: an organised, selective press rather than constant high pressure.
- {P(m['share_actions_att_third'])} of defensive actions happen in the attacking third, and Spain make
  {m['high_recoveries_pm']:.0f} high regains per match. Short build-up through our centre-backs is risky.
- Average defensive action height: {m['avg_action_height']:.0f} m from their own goal.

## 5. Set pieces

- {m['corners']} corners: {m['corner_technique'].get('Inswinging', 0)} inswinging, {m['corner_technique'].get('Outswinging', 0)} outswinging,
  {m['corner_technique'].get('Other / short', 0)} short or other.
- {m['set_piece_shots']} shots, {m['set_piece_xg']:.1f} xG and {m['set_piece_goals']} goals from corner and free-kick phases.

## 6. Key players

| Player | Goals | xG | xA | Key passes | Progressive carries | Dribbles |
|---|---|---|---|---|---|---|
{prow}

- **Lamine Yamal (right wing):** the main creator, with the most xA and key passes; receives wide on the right and drives at defenders (most progressive carries).
- **Nico Williams (left wing):** direct 1v1 threat with the most successful dribbles; attacks the space behind our right-back.
- **Dani Olmo:** joint top scorer at the tournament (3 goals), arriving late into the box from the No.10 role.

## 7. Game plan recommendations

1. **Protect the flanks:** double up on both wingers (full-back plus winger), show them inside onto a screened midfield.
2. **Stay compact centrally:** Spain rarely play through the middle; force them wide early and defend crosses and cut-backs.
3. **Break their control:** press Rodri and the centre-backs in short spells to deny rhythm; Spain conceded most when possession was shared.
4. **Avoid short build-up under pressure:** play beyond their first line and attack the space left by their high full-backs.
5. **Defend inswinging corners:** zone the six-yard box and the near post.

## Video plan (Nacsport)

{m['clips_total']} timecoded clips: {', '.join(f"{v} {k_.lower()}" for k_, v in m['clip_counts'].items())}.
See `nacsport/Code_Window_Template.md` for the coding structure.

---
Data: StatsBomb Open Data. Definitions: PPDA = opponent passes in their own 60% of the pitch divided by
Spain's tackles, interceptions and fouls there; field tilt = Spain's share of final-third passes;
progressive pass = moves the ball at least 25% closer to goal and ends in the opponent's half.
"""
(ROOT / "reports" / "Opposition_Report_Spain.md").write_text(md, encoding="utf-8")
print(md[:1800])
