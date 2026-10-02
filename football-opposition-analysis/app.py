"""Interactive opposition-analysis dashboard (StatsBomb open data, UEFA Euro 2024).

Run:  streamlit run app.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
import analysis as A          # noqa: E402
import download_data as D     # noqa: E402

A.SAVE = False
st.set_page_config(page_title="Opposition Analysis | Euro 2024", page_icon="⚽", layout="wide")
st.markdown("""<style>
[data-testid="stMetricValue"] {font-size: 1.6rem;}
.block-container {padding-top: 1.6rem;}
</style>""", unsafe_allow_html=True)


# ------------------------------------------------------------------ data
@st.cache_data(show_spinner=False)
def team_list():
    path = ROOT / "data" / "matches_55_282.json"
    if not path.exists():
        D.main("Spain")
    m = json.loads(path.read_text())
    return sorted({x["home_team"]["home_team_name"] for x in m} | {x["away_team"]["away_team_name"] for x in m})


@st.cache_data(show_spinner="Downloading and preparing StatsBomb data...")
def load_team(team):
    D.main(team)
    A.TEAM = team
    meta, ev = A.load()
    return meta, ev


def fig(func, *args, **kwargs):
    """Run an analysis plotting function and show its figure."""
    A.FIGS.clear()
    out = func(*args, **kwargs)
    for f in A.FIGS.values():
        st.pyplot(f, width="stretch")
        A.plt.close(f)
    return out


def plotly_pitch(height=520, half=False):
    """StatsBomb pitch (120 x 80) drawn in Plotly, attacking left to right."""
    line = dict(color=A.LINE, width=1.5)
    shapes = [dict(type="rect", x0=0, y0=0, x1=120, y1=80, line=line),
              dict(type="line", x0=60, y0=0, x1=60, y1=80, line=line),
              dict(type="circle", x0=50, y0=30, x1=70, y1=50, line=line),
              dict(type="rect", x0=0, y0=18, x1=18, y1=62, line=line),
              dict(type="rect", x0=102, y0=18, x1=120, y1=62, line=line),
              dict(type="rect", x0=0, y0=30, x1=6, y1=50, line=line),
              dict(type="rect", x0=114, y0=30, x1=120, y1=50, line=line),
              dict(type="rect", x0=120, y0=36, x1=122, y1=44, line=line),
              dict(type="rect", x0=-2, y0=36, x1=0, y1=44, line=line)]
    f = go.Figure()
    f.update_layout(shapes=shapes, height=height, plot_bgcolor=A.BG, paper_bgcolor=A.BG,
                    font=dict(color=A.TEXT), margin=dict(l=10, r=10, t=40, b=10),
                    xaxis=dict(range=[58 if half else -3, 123], visible=False),
                    yaxis=dict(range=[82, -2], visible=False, scaleanchor="x"),
                    legend=dict(orientation="h", y=-0.02, bgcolor="rgba(0,0,0,0)"))
    return f


# ------------------------------------------------------------------ sidebar
st.sidebar.title("⚽ Opposition Analysis")
teams = team_list()
team = st.sidebar.selectbox("Opponent to analyse", teams, index=teams.index("Spain"))
meta, ev_all = load_team(team)
A.TEAM = team
labels = {r.match_id: f"{r.stage}: vs {r.opponent} ({r.score})" for r in meta.itertuples()}
chosen = st.sidebar.multiselect("Matches", list(labels), default=list(labels), format_func=labels.get)
if not chosen:
    st.warning("Select at least one match.")
    st.stop()
ev = ev_all[ev_all.match_id.isin(chosen)]
m_sel = meta[meta.match_id.isin(chosen)]
st.sidebar.caption("Data: StatsBomb Open Data, UEFA Euro 2024. Non-commercial use with attribution.")

k = A.match_kpis(m_sel, ev)
players = A.player_table(ev)
w = int((k.goals > k.goals_against).sum()); d = int((k.goals == k.goals_against).sum())

st.title(f"{team}: opposition report")
st.caption(f"{len(k)} matches selected | {w}W {d}D {len(k) - w - d}L | results after 90/120 minutes")
c = st.columns(6)
c[0].metric("Goals for / against", f"{int(k.goals.sum())} - {int(k.goals_against.sum())}")
c[1].metric("xG for / against", f"{k.xg.sum():.1f} - {k.xg_against.sum():.1f}")
c[2].metric("Possession", f"{k.possession.mean():.0%}")
c[3].metric("Pass completion", f"{k.pass_completion.mean():.0%}")
c[4].metric("PPDA", f"{k.ppda.mean():.1f}", help="Opponent passes per defensive action in the press zone. Lower = more intense press.")
c[5].metric("Field tilt", f"{k.field_tilt.mean():.0%}", help="Share of final-third passes")

tabs = st.tabs(["Overview", "Shots", "Build-up", "Pressing", "Set pieces", "Players", "Match view", "Video clips", "Report"])

# ------------------------------------------------------------------ overview
with tabs[0]:
    fig(A.kpi_chart, k)
    show = k[["match", "stage", "formation", "possession", "pass_completion", "shots", "xg", "shots_against",
              "xg_against", "ppda", "field_tilt", "progressive_passes", "high_recoveries"]]
    st.dataframe(show.style.format({"possession": "{:.0%}", "pass_completion": "{:.0%}", "field_tilt": "{:.0%}",
                                    "xg": "{:.2f}", "xg_against": "{:.2f}", "ppda": "{:.1f}"}),
                 width="stretch", hide_index=True)
    st.download_button("Download match KPIs (CSV)", k.to_csv(index=False), f"{team}_match_kpis.csv")

# ------------------------------------------------------------------ shots
with tabs[1]:
    col1, col2, col3 = st.columns(3)
    side = col1.radio("Shots by", [team, f"{team}'s opponents"], horizontal=True)
    is_t = side == team
    s = ev[(ev.type_name == "Shot") & (ev.is_team == is_t)].copy()
    sit = col2.selectbox("Situation", ["All", "Open play", "Set pieces", "Penalties"])
    if sit == "Open play":
        s = s[s.play_pattern_name.isin(["Regular Play", "From Counter", "From Keeper", "From Goal Kick"]) &
              (s.shot_type_name == "Open Play")]
    elif sit == "Set pieces":
        s = s[s.play_pattern_name.isin(["From Corner", "From Free Kick", "From Throw In"]) |
              (s.shot_type_name == "Free Kick")]
    elif sit == "Penalties":
        s = s[s.shot_type_name == "Penalty"]
    pl = col3.multiselect("Players", sorted(s.player.dropna().unique()))
    if pl:
        s = s[s.player.isin(pl)]
    s["goal"] = s.shot_outcome_name == "Goal"
    f = plotly_pitch(560, half=True)
    for g, name, color, sym in [(False, "Shot", A.RED if is_t else A.CYAN, "circle"), (True, "Goal", A.GOLD, "star")]:
        q = s[s.goal == g]
        f.add_trace(go.Scatter(x=q.x, y=q.y, mode="markers", name=name,
                               marker=dict(size=8 + q.shot_statsbomb_xg * 45, color=color, symbol=sym,
                                           line=dict(color=A.TEXT, width=0.7), opacity=0.8),
                               customdata=np.c_[q.player, q.opponent, q.minute, q.shot_statsbomb_xg.round(2),
                                                q.shot_outcome_name, q.shot_body_part_name],
                               hovertemplate="<b>%{customdata[0]}</b><br>vs %{customdata[1]}, min %{customdata[2]}"
                                             "<br>xG %{customdata[3]} | %{customdata[4]}<br>%{customdata[5]}<extra></extra>"))
    f.update_layout(title=f"{side}: {len(s)} shots, {s.shot_statsbomb_xg.sum():.2f} xG, {int(s.goal.sum())} goals "
                          f"(hover for details, size = xG)")
    st.plotly_chart(f, width="stretch")
    st.dataframe(s.groupby("player").agg(shots=("id", "count"), goals=("goal", "sum"),
                                         xg=("shot_statsbomb_xg", "sum")).sort_values("xg", ascending=False)
                 .round(2), width="stretch")

# ------------------------------------------------------------------ build-up
with tabs[2]:
    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("Pass network")
        mid = st.selectbox("Match", chosen, format_func=labels.get, index=len(chosen) - 1, key="pn")
        fig(A.pass_network, ev, mid, labels[mid].split(": ")[1])
    with col2:
        st.subheader("Final-third entries")
        share, n = fig(A.buildup_map, ev)
        st.write(" | ".join(f"**{k_}**: {v:.0%}" for k_, v in share.items()))
    st.subheader("Progressive passers and carriers")
    st.dataframe(players[["prog_passes", "prog_carries", "key_passes", "xa"]].sort_values("prog_passes", ascending=False)
                 .head(12).round(2), width="stretch")

# ------------------------------------------------------------------ pressing
with tabs[3]:
    col1, col2 = st.columns([3, 2])
    with col1:
        avg_h, share_high = fig(A.pressing_map, ev)
    with col2:
        f = go.Figure(go.Bar(x=k.opponent, y=k.ppda, marker_color=A.RED, text=k.ppda.round(1), textposition="outside"))
        f.update_layout(title="PPDA by match (lower = more intense press)", plot_bgcolor=A.BG, paper_bgcolor=A.BG,
                        font=dict(color=A.TEXT), height=320, margin=dict(t=50, b=10))
        st.plotly_chart(f, width="stretch")
        f = go.Figure(go.Bar(x=k.opponent, y=k.high_recoveries, marker_color=A.CYAN, text=k.high_recoveries,
                             textposition="outside"))
        f.update_layout(title="High regains by match", plot_bgcolor=A.BG, paper_bgcolor=A.BG,
                        font=dict(color=A.TEXT), height=300, margin=dict(t=50, b=10))
        st.plotly_chart(f, width="stretch")
    hi, lo = k[k.ppda > 18], k[k.ppda <= 18]
    if len(hi) and len(lo):
        st.info(f"When {team}'s press dropped (PPDA above 18) they conceded {hi.xg_against.mean():.2f} xG per match, "
                f"vs {lo.xg_against.mean():.2f} in the other matches.")

# ------------------------------------------------------------------ set pieces
with tabs[4]:
    col1, col2 = st.columns([3, 2])
    with col1:
        tech, n_c, sp_shots, sp_xg, sp_goals = fig(A.corner_map, ev)
    with col2:
        st.metric("Corners", n_c)
        st.metric("Set-piece shots / xG", f"{sp_shots} / {sp_xg:.2f}")
        st.metric("Set-piece goals", sp_goals)
        st.write("**Delivery types**")
        st.dataframe(pd.Series(tech, name="corners"), width="stretch")
        takers = ev[ev.is_team & (ev.pass_type_name == "Corner")].groupby("player").size().sort_values(ascending=False)
        st.write("**Corner takers**")
        st.dataframe(takers.rename("corners"), width="stretch")

# ------------------------------------------------------------------ players
with tabs[5]:
    st.subheader("Player output (selected matches)")
    st.dataframe(players.round(2), width="stretch")
    default = [p for p in players.index[:3]]
    pick = st.multiselect("Key-threat heatmaps (up to 3)", list(players.index), default=default, max_selections=3)
    if pick:
        fig(A.key_player_heatmaps, ev, [(p, p) for p in pick])
    one = st.selectbox("Player profile", list(players.index))
    pe = ev[ev.player == one]
    r = players.loc[one]
    cc = st.columns(6)
    for col, (lab, val) in zip(cc, [("Goals", int(r.goals)), ("xG", f"{r.xg:.2f}"), ("xA", f"{r.xa:.2f}"),
                                    ("Key passes", int(r.key_passes)), ("Prog. carries", int(r.prog_carries)),
                                    ("Dribbles", int(r.dribbles))]):
        col.metric(lab, val)
    acts = pe[pe.type_name.isin(["Pass", "Carry", "Shot", "Dribble", "Pressure", "Ball Recovery", "Interception"])]
    f = plotly_pitch(500)
    for t, color in [("Pass", A.LINE), ("Carry", A.CYAN), ("Shot", A.GOLD), ("Dribble", A.RED), ("Pressure", "#9B5DE5"),
                     ("Ball Recovery", "#2EC4B6"), ("Interception", "#2EC4B6")]:
        q = acts[acts.type_name == t]
        if len(q):
            f.add_trace(go.Scatter(x=q.x, y=q.y, mode="markers", name=f"{t} ({len(q)})",
                                   marker=dict(size=7, color=color, opacity=0.7),
                                   customdata=np.c_[q.opponent, q.minute],
                                   hovertemplate=f"{t}<br>vs %{{customdata[0]}}, min %{{customdata[1]}}<extra></extra>"))
    f.update_layout(title=f"{one}: on-ball actions (click legend items to toggle)")
    st.plotly_chart(f, width="stretch")

# ------------------------------------------------------------------ match view
with tabs[6]:
    mid = st.selectbox("Match", chosen, format_func=labels.get, index=len(chosen) - 1, key="mv")
    mrow = meta[meta.match_id == mid].iloc[0]
    fig(A.xg_timeline, ev, mid, mrow.opponent, f"{mrow.stage}: {team} {mrow.score} {mrow.opponent}, xG timeline")
    one = k[k.opponent == mrow.opponent].iloc[0]
    cc = st.columns(5)
    cc[0].metric("Possession", f"{one.possession:.0%}")
    cc[1].metric("Shots", f"{one.shots} - {one.shots_against}")
    cc[2].metric("xG", f"{one.xg:.2f} - {one.xg_against:.2f}")
    cc[3].metric("PPDA", f"{one.ppda:.1f}")
    cc[4].metric("Formation", one.formation)

# ------------------------------------------------------------------ clips
with tabs[7]:
    clips = A.build_clips(ev)
    col1, col2, col3 = st.columns(3)
    cat = col1.multiselect("Category", sorted(clips.category.unique()), default=sorted(clips.category.unique()))
    mt = col2.multiselect("Match", sorted(clips.match.unique()), default=sorted(clips.match.unique()))
    who = col3.multiselect("Player", sorted(clips.player.dropna().unique()))
    q = clips[clips.category.isin(cat) & clips.match.isin(mt)]
    if who:
        q = q[q.player.isin(who)]
    st.write(f"**{len(q)} clips**. Timestamps restart at 00:00 each half; add each half's kick-off time in your video.")
    st.dataframe(q, width="stretch", hide_index=True, height=420)
    st.download_button("Download clip list for Nacsport (CSV)", q.to_csv(index=False), f"{team}_clip_playlist.csv")
    with st.expander("Nacsport code window template"):
        st.markdown((ROOT / "nacsport" / "Code_Window_Template.md").read_text())

# ------------------------------------------------------------------ report
with tabs[8]:
    p_ent = ev[ev.is_team & (ev.type_name == "Pass") & ev.pass_outcome_name.isna() & (ev.x < 80) & (ev.end_x >= 80)]
    lanes = pd.cut(p_ent.end_y, [0, 26.67, 53.33, 80], labels=["left", "centre", "right"]).value_counts(normalize=True)
    top = players.head(3)
    d_act = ev[ev.is_team & ev.type_name.isin(["Pressure", "Ball Recovery", "Interception", "Duel", "Foul Committed"])]
    corners = ev[ev.is_team & (ev.pass_type_name == "Corner")]
    insw = (corners.pass_technique_name == "Inswinging").sum()
    main_lane = lanes.idxmax()
    report = f"""### Opposition summary: {team}

**Profile.** {len(k)} matches: {w} wins, {d} draws and {len(k) - w - d} defeats (after 90/120 minutes), {int(k.goals.sum())} goals for and
{int(k.goals_against.sum())} against, {k.xg.sum():.1f} xG for and {k.xg_against.sum():.1f} against. Average possession {k.possession.mean():.0%},
pass completion {k.pass_completion.mean():.0%}, field tilt {k.field_tilt.mean():.0%}.

**Shape.** Most-used formation: {k.formation.mode()[0]} ({(k.formation == k.formation.mode()[0]).sum()} of {len(k)} matches).

**Attack.** {len(p_ent)} completed passes into the final third: {lanes.get('left', 0):.0%} down their left,
{lanes.get('centre', 0):.0%} through the centre and {lanes.get('right', 0):.0%} down their right. Main route: **{main_lane}**.
{int(k.shots.sum())} shots at {k.xg.sum() / max(k.shots.sum(), 1):.2f} xG per shot.

**Pressing.** Average PPDA {k.ppda.mean():.1f}; {(d_act.x >= 80).mean():.0%} of defensive actions in the attacking third;
{k.high_recoveries.mean():.0f} high regains per match.

**Set pieces.** {len(corners)} corners ({insw} inswinging).

**Key players.** {', '.join(f"{n} ({r.xg:.2f} xG, {r.xa:.2f} xA)" for n, r in top.iterrows())}.

**Suggested focus.**
1. Protect the **{main_lane}** channel: it carries the most final-third entries.
2. Plan for {top.index[0]}: highest combined xG + xA in the selected matches.
3. {"Build up carefully under pressure: they press high often." if k.ppda.mean() < 12 else "Use the ball: their press is selective, so there is time to build when structured."}
4. Prepare set-piece defence for {"inswinging" if insw >= len(corners) / 2 else "mixed"} corner deliveries.
"""
    st.markdown(report)
    st.download_button("Download summary (Markdown)", report, f"{team}_opposition_summary.md")
    if team == "Spain":
        with st.expander("Full written report (Spain)"):
            st.markdown((ROOT / "reports" / "Opposition_Report_Spain.md").read_text())
