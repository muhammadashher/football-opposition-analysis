"""Opposition analysis for any UEFA Euro 2024 team (default: Spain), using StatsBomb open data.

Produces match KPIs, shot maps, pass network, build-up and pressing maps, set-piece and key-player
analysis, an xG timeline, a Nacsport clip playlist and metrics for the report.
Pitch coordinates follow StatsBomb: 120 x 80, every team attacking left to right.
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import matplotlib.patheffects as pe
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Rectangle
from mplsoccer import Pitch, VerticalPitch

ROOT = Path(__file__).resolve().parents[1]
DATA, FIG, OUT = ROOT / "data", ROOT / "outputs" / "figures", ROOT / "outputs"
TEAM = "Spain"
SAVE = True          # False when used from the Streamlit app: figures are kept in FIGS instead
FIGS = {}
BG, LINE, TEXT = "#0E1A1F", "#9FB3AE", "#F2F4F3"
RED, CYAN, GOLD, GREY = "#E63946", "#4CC9F0", "#F4B942", "#5C6B70"
OUTLINE = [pe.withStroke(linewidth=3.2, foreground=BG)]
BOX = dict(boxstyle="round,pad=0.25", facecolor=BG, edgecolor="none", alpha=0.85)
HEAT = LinearSegmentedColormap.from_list("heat", [BG, "#5A1B22", RED, GOLD])
plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": TEXT, "axes.labelcolor": TEXT,
                     "xtick.color": TEXT, "ytick.color": TEXT})


# ------------------------------------------------------------------ loading
def load():
    matches = json.loads((DATA / "matches_55_282.json").read_text())
    meta, frames = [], []
    for m in sorted(matches, key=lambda x: x["match_date"]):
        h, a = m["home_team"]["home_team_name"], m["away_team"]["away_team_name"]
        if TEAM not in (h, a):
            continue
        opp = a if h == TEAM else h
        gf = m["home_score"] if h == TEAM else m["away_score"]
        ga = m["away_score"] if h == TEAM else m["home_score"]
        meta.append({"match_id": m["match_id"], "date": m["match_date"], "stage": m["competition_stage"]["name"],
                     "opponent": opp, "score": f"{gf}-{ga}", "gf": gf, "ga": ga})
        ev = pd.json_normalize(json.loads((DATA / "events" / f"{m['match_id']}.json").read_text()), sep="_")
        ev["match_id"], ev["opponent"] = m["match_id"], opp
        frames.append(ev)
    ev = pd.concat(frames, ignore_index=True)
    for col, pre in [("location", ""), ("pass_end_location", "end_"), ("carry_end_location", "carry_end_")]:
        loc = ev[col].apply(lambda v: v if isinstance(v, list) else [np.nan, np.nan])
        ev[f"{pre}x"], ev[f"{pre}y"] = loc.str[0].astype(float), loc.str[1].astype(float)
    ev["is_team"] = ev["team_name"] == TEAM
    nick = {}
    for f in (DATA / "lineups").glob("*.json"):
        for t in json.loads(f.read_text()):
            for p in t["lineup"]:
                nick[p["player_name"]] = p.get("player_nickname") or p["player_name"]
    ev["player"] = ev["player_name"].map(nick).fillna(ev["player_name"])
    ev["recipient"] = ev["pass_recipient_name"].map(nick).fillna(ev["pass_recipient_name"])
    return pd.DataFrame(meta), ev


def is_progressive(x, y, ex, ey):
    """Moves the ball at least 25% closer to the goal centre (120, 40) and ends in the opposition half."""
    d0 = np.hypot(120 - x, 40 - y)
    d1 = np.hypot(120 - ex, 40 - ey)
    return (d1 <= 0.75 * d0) & (ex >= 60)


# ------------------------------------------------------------------ KPIs
def match_kpis(meta, ev):
    rows = []
    for m in meta.itertuples():
        e = ev[ev.match_id == m.match_id]
        sp, op = e[e.is_team], e[~e.is_team]
        p_sp, p_op = sp[sp.type_name == "Pass"], op[op.type_name == "Pass"]
        poss = len(p_sp) / (len(p_sp) + len(p_op))
        comp = p_sp["pass_outcome_name"].isna().mean()
        shots_sp, shots_op = sp[sp.type_name == "Shot"], op[op.type_name == "Shot"]
        # PPDA: opponent passes in their own 60% / Spain defensive actions in the opponent's 60%
        opp_passes = len(p_op[p_op.x < 72])
        def_act = sp[((sp.type_name == "Duel") & (sp.duel_type_name == "Tackle")) |
                     sp.type_name.isin(["Interception", "Foul Committed"])]
        def_act = len(def_act[def_act.x > 48])
        ft_sp, ft_op = len(p_sp[p_sp.x >= 80]), len(p_op[p_op.x >= 80])
        prog = p_sp[p_sp.pass_outcome_name.isna()]
        prog = prog[is_progressive(prog.x, prog.y, prog.end_x, prog.end_y)]
        high_rec = sp[(sp.type_name.isin(["Ball Recovery", "Interception"])) & (sp.x >= 72)]
        formation = sp[sp.type_name == "Starting XI"]["tactics_formation"].iloc[0]
        rows.append({"match": f"{m.opponent} ({m.score})", "opponent": m.opponent, "stage": m.stage,
                     "formation": str(int(formation)), "possession": poss, "passes": len(p_sp),
                     "pass_completion": comp, "shots": len(shots_sp), "shots_against": len(shots_op),
                     "xg": shots_sp.shot_statsbomb_xg.sum(), "xg_against": shots_op.shot_statsbomb_xg.sum(),
                     "goals": m.gf, "goals_against": m.ga, "ppda": opp_passes / max(def_act, 1),
                     "field_tilt": ft_sp / (ft_sp + ft_op), "progressive_passes": len(prog),
                     "high_recoveries": len(high_rec)})
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ figures
def finish(fig, name):
    """Save the figure to outputs/figures, or keep it in FIGS for the app."""
    if SAVE:
        fig.savefig(FIG / f"{name}.png", dpi=200, facecolor=BG)
        plt.close(fig)
    else:
        FIGS[name] = fig
    return fig


def new_pitch(vertical=False, half=False, pad_bottom=None):
    P = VerticalPitch if vertical else Pitch
    kw = {"pad_bottom": pad_bottom} if pad_bottom is not None else {}
    return P(pitch_type="statsbomb", pitch_color=BG, line_color=LINE, half=half, linewidth=1.2, goal_type="box",
             line_zorder=2, **kw)


SHORT_OVERRIDES = {"Fabián Ruiz": "Fabián", "Nico Williams": "N. Williams", "Iñaki Williams": "I. Williams",
                   "Lamine Yamal": "Yamal", "Daniel Olmo": "Olmo", "Mikel Oyarzabal": "Oyarzabal"}


def short_name(name):
    """Pitch label: 'Robin Le Normand' -> 'Le Normand', 'Lamine Yamal' -> 'Yamal', 'Rodri' -> 'Rodri'."""
    if not isinstance(name, str):
        return name
    if name in SHORT_OVERRIDES:
        return SHORT_OVERRIDES[name]
    parts = name.split()
    if len(parts) >= 3 and parts[-2].lower() in {"le", "de", "van", "von", "da", "di", "ten", "der", "el"}:
        return " ".join(parts[-2:])
    return parts[-1]


def place_labels(ax, pts, fontsize=10.5, min_dx=13, min_dy=4.2):
    """Place one label per node (above, below, left or right) avoiding overlaps with earlier labels."""
    placed = []
    offsets = [(0, -4.6, "center", "bottom"), (0, 4.6, "center", "top"), (-3.4, 0, "right", "center"),
               (3.4, 0, "left", "center"), (0, -8.2, "center", "bottom"), (0, 8.2, "center", "top")]
    for label, x, y in sorted(pts, key=lambda t: (t[2], t[1])):
        for dx, dy, ha, va in offsets:
            lx, ly = x + dx, y + dy
            cx = lx - (len(label) * 0.9 if ha == "right" else 0) + (len(label) * 0.9 if ha == "left" else 0)
            if all(abs(cx - px) > min_dx or abs(ly - py) > min_dy for px, py in placed):
                break
        placed.append((cx, ly))
        ax.text(lx, ly, label, ha=ha, va=va, fontsize=fontsize, color=TEXT, fontweight="bold", zorder=5,
                bbox=BOX, path_effects=OUTLINE)


def title(fig, t, sub):
    fig.text(0.03, 0.975, t, fontsize=19, fontweight="bold", va="top")
    fig.text(0.03, 0.925, sub, fontsize=11.5, color="#B8C4C0", va="top")
    fig.text(0.97, 0.015, "Data: StatsBomb Open Data | Euro 2024", fontsize=8.5, color=GREY, ha="right")


def pitch_fig(pitch, height=8, ncols=1, title_h=0.1):
    """Pitch figure with reserved space for a title block and an endnote."""
    fig, axs = pitch.grid(nrows=1, ncols=ncols, figheight=height, title_height=title_h, endnote_height=0.03,
                          title_space=0.01, endnote_space=0.01, grid_height=0.93 - title_h, axis=False, space=0.05)
    fig.set_facecolor(BG)
    for k in ("title", "endnote"):
        axs[k].remove()
    return fig, axs["pitch"]


def shot_map(ev, team=True, name="shot_map"):
    s = ev[(ev.type_name == "Shot") & (ev.is_team == team)]
    pitch = new_pitch(vertical=True, half=True, pad_bottom=-12)
    fig, ax = pitch_fig(pitch, 7.6)
    goals = s[s.shot_outcome_name == "Goal"]
    other = s[s.shot_outcome_name != "Goal"]
    col = RED if team else CYAN
    pitch.scatter(other.x, other.y, s=other.shot_statsbomb_xg * 900 + 30, c=col, alpha=0.35,
                  edgecolors=TEXT, linewidth=0.6, ax=ax)
    pitch.scatter(goals.x, goals.y, s=goals.shot_statsbomb_xg * 900 + 120, marker="football", ax=ax, zorder=3)
    who = TEAM if team else f"{TEAM}'s opponents"
    title(fig, f"{who}: shots, Euro 2024",
          f"{len(s)} shots | {s.shot_statsbomb_xg.sum():.1f} xG | {len(goals)} goals (football markers) | size = xG")
    finish(fig, name)


def pass_network(ev, match_id, label):
    e = ev[(ev.match_id == match_id) & ev.is_team]
    subs = e[e.type_name == "Substitution"]
    first_sub = subs.minute.min() if len(subs) else 90
    p = e[(e.type_name == "Pass") & e.pass_outcome_name.isna() & (e.minute < first_sub)].copy()
    p["passer"] = p.player
    short = lambda n: n
    avg = e[(e.minute < first_sub) & e.x.notna() & e.type_name.isin(["Pass", "Carry", "Ball Receipt*"])] \
        .groupby("player").agg(x=("x", "mean"), y=("y", "mean"), n=("id", "count"))
    links = p.groupby(["passer", "recipient"]).size().reset_index(name="n")
    links = links[links.n >= 4].merge(avg[["x", "y"]], left_on="passer", right_index=True) \
        .merge(avg[["x", "y"]], left_on="recipient", right_index=True, suffixes=("", "_end"))
    pitch = new_pitch()
    fig, ax = pitch_fig(pitch, 8.2)
    pitch.lines(links.x, links.y, links.x_end, links.y_end, lw=links.n / links.n.max() * 9, color=RED,
                alpha=0.55, zorder=1, ax=ax)
    pitch.scatter(avg.x, avg.y, s=avg.n * 3 + 200, color=BG, edgecolors=RED, linewidth=2.2, zorder=2, ax=ax)
    place_labels(ax, [(short_name(n), r.x, r.y) for n, r in avg.iterrows()])
    title(fig, f"{TEAM} pass network: {label}",
          f"Completed passes before the first substitution (min {int(first_sub)}) | lines = 4+ passes | node = involvement")
    finish(fig, "pass_network_final")


def buildup_map(ev):
    p = ev[ev.is_team & (ev.type_name == "Pass") & ev.pass_outcome_name.isna()]
    entries = p[(p.x < 80) & (p.end_x >= 80)]
    pitch = new_pitch()
    fig, ax = pitch_fig(pitch, 8.2)
    lanes = pd.cut(entries.end_y, [0, 26.67, 53.33, 80], labels=["Left", "Centre", "Right"])
    share = lanes.value_counts(normalize=True)
    top = max(share.max(), 0.01)
    for lane, (y0, y1) in [("Left", (0, 26.67)), ("Centre", (26.67, 53.33)), ("Right", (53.33, 80))]:
        v = share.get(lane, 0)
        ax.add_patch(Rectangle((80, y0), 40, y1 - y0, facecolor=HEAT(0.25 + 0.75 * v / top), alpha=0.55,
                               edgecolor=BG, lw=2, zorder=1))
    pitch.arrows(entries.x, entries.y, entries.end_x, entries.end_y, width=0.9, headwidth=4, color=TEXT,
                 alpha=0.13, zorder=1.5, ax=ax)
    for lane, ycen in [("Left", 13.3), ("Centre", 40), ("Right", 66.7)]:
        ax.text(104, ycen, f"{lane}\n{share.get(lane, 0):.0%}", ha="center", va="center", fontsize=15,
                fontweight="bold", color=TEXT, zorder=5, bbox=dict(boxstyle="round,pad=0.45", facecolor=BG,
                                                                   edgecolor=GOLD, lw=1.5, alpha=0.9))
    title(fig, f"Build-up: how {TEAM} enter the final third",
          f"{len(entries)} completed passes into the final third, {ev.match_id.nunique()} matches | "
          f"share by channel (their left = top)")
    finish(fig, "final_third_entries")
    return share.to_dict(), len(entries)


def pressing_map(ev):
    d = ev[ev.is_team & ev.type_name.isin(["Pressure", "Ball Recovery", "Interception", "Duel", "Foul Committed"])]
    pitch = new_pitch()
    fig, ax = pitch_fig(pitch, 8.2)
    bs = pitch.bin_statistic(d.x, d.y, statistic="count", bins=(6, 4), normalize=True)
    pitch.heatmap(bs, ax=ax, cmap=HEAT, edgecolors=BG, alpha=0.9)
    pitch.label_heatmap(bs, ax=ax, str_format="{:.0%}", color=TEXT, fontsize=12, fontweight="bold", ha="center",
                        va="center", path_effects=OUTLINE, zorder=4)
    avg_h = d.x.mean()
    ax.plot([avg_h, avg_h], [0, 80], color=CYAN, lw=2.2, ls="--", zorder=3)
    ax.text(avg_h, -2.2, f"Average height: {avg_h:.0f} m from own goal", ha="center", va="bottom", color=CYAN,
            fontsize=11.5, fontweight="bold", zorder=5, bbox=BOX)
    share_high = (d.x >= 80).mean()
    title(fig, f"Pressing: where {TEAM} win and contest the ball",
          f"{len(d):,} pressures, tackles, recoveries and interceptions | {share_high:.0%} in the attacking third")
    finish(fig, "pressing_heatmap")
    return avg_h, share_high


def corner_map(ev):
    c = ev[ev.is_team & (ev.type_name == "Pass") & (ev.pass_type_name == "Corner")].copy()
    c["tech"] = c.pass_technique_name.fillna("Other / short")
    pitch = new_pitch(vertical=True, half=True, pad_bottom=-24)
    fig, ax = pitch_fig(pitch, 7)
    colors = {"Inswinging": RED, "Outswinging": CYAN, "Other / short": GREY, "Straight": GOLD}
    for t, g in c.groupby("tech"):
        pitch.scatter(g.end_x, g.end_y, s=70, color=colors.get(t, GOLD), edgecolors=TEXT, linewidth=0.5,
                      alpha=0.85, ax=ax, label=f"{t} ({len(g)})")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 0.0), facecolor=BG, edgecolor=GREY, labelcolor=TEXT,
              fontsize=11, ncol=3, frameon=True)
    sp_shots = ev[ev.is_team & (ev.type_name == "Shot") & ev.play_pattern_name.isin(["From Corner", "From Free Kick"])]
    title(fig, f"Set pieces: {TEAM} corner deliveries",
          f"{len(c)} corners | {len(sp_shots)} shots and {sp_shots.shot_statsbomb_xg.sum():.1f} xG from corner/free-kick phases")
    finish(fig, "corners")
    return c.tech.value_counts().to_dict(), len(c), len(sp_shots), float(sp_shots.shot_statsbomb_xg.sum()), \
        int((sp_shots.shot_outcome_name == "Goal").sum())


def player_table(ev):
    t = ev[ev.is_team]
    shots = t[t.type_name == "Shot"]
    xg = shots.groupby("player").shot_statsbomb_xg.sum()
    goals = shots[shots.shot_outcome_name == "Goal"].groupby("player").size()
    key = shots.dropna(subset=["shot_key_pass_id"])[["shot_key_pass_id", "shot_statsbomb_xg"]] \
        .rename(columns={"shot_statsbomb_xg": "assisted_xg"})
    passes = t[t.type_name == "Pass"]
    xa = passes.merge(key, left_on="id", right_on="shot_key_pass_id").groupby("player").assisted_xg.sum()
    kp = passes[passes.pass_shot_assist.eq(True) | passes.pass_goal_assist.eq(True)].groupby("player").size()
    cp = passes[passes.pass_outcome_name.isna()]
    prog_p = cp[is_progressive(cp.x, cp.y, cp.end_x, cp.end_y)].groupby("player").size()
    car = t[t.type_name == "Carry"]
    prog_c = car[is_progressive(car.x, car.y, car.carry_end_x, car.carry_end_y)].groupby("player").size()
    press = t[t.type_name == "Pressure"].groupby("player").size()
    drib = t[(t.type_name == "Dribble") & (t.dribble_outcome_name == "Complete")].groupby("player").size()
    df = pd.DataFrame({"goals": goals, "xg": xg, "xa": xa, "key_passes": kp, "prog_passes": prog_p,
                       "prog_carries": prog_c, "dribbles": drib, "pressures": press}).fillna(0)
    df["xg_xa"] = df.xg + df.xa
    return df.sort_values("xg_xa", ascending=False)


def key_player_heatmaps(ev, players):
    pitch = new_pitch()
    fig, axs = pitch_fig(pitch, 6, ncols=len(players), title_h=0.2)
    for ax, (name, label) in zip(axs, players):
        e = ev[(ev.player == name) & ev.x.notna()]
        pitch.kdeplot(e.x, e.y, ax=ax, fill=True, levels=50, thresh=0.08, cmap=HEAT, alpha=0.85)
        ax.set_title(label, color=GOLD, fontsize=14, fontweight="bold", pad=8)
    title(fig, "Key threats: where they receive and act", f"All on-ball actions in the selected matches | {TEAM} attack left to right")
    finish(fig, "key_player_heatmaps")


def xg_timeline(ev, match_id, opp, label=None):
    s = ev[(ev.match_id == match_id) & (ev.type_name == "Shot")].copy()
    s["t"] = s.minute + s.second / 60
    fig, ax = plt.subplots(figsize=(12, 6))
    fig.set_facecolor(BG); ax.set_facecolor(BG)
    fig.subplots_adjust(top=0.8, bottom=0.12, left=0.07, right=0.97)
    for team, col, lab in [(True, RED, TEAM), (False, CYAN, opp)]:
        g = s[s.is_team == team].sort_values("t")
        xs = np.r_[0, g.t, 95]; ys = np.r_[0, g.shot_statsbomb_xg.cumsum(), g.shot_statsbomb_xg.sum()]
        ax.step(xs, ys, where="post", color=col, lw=2.5, label=f"{lab} ({g.shot_statsbomb_xg.sum():.2f} xG)")
        gl = g[g.shot_outcome_name == "Goal"]
        cum = g.shot_statsbomb_xg.cumsum()
        ax.scatter(gl.t, cum[gl.index], s=140, color=GOLD, edgecolors=BG, zorder=3)
        for _, r in gl.iterrows():
            ha = "right" if r.t > 80 else "left"
            ax.annotate(short_name(r.player) + f" {int(r.minute)}'", (r.t, cum[r.name]),
                        xytext=(-8 if ha == "right" else 8, 10), textcoords="offset points", ha=ha,
                        color=TEXT, fontsize=11, fontweight="bold", bbox=BOX, zorder=5)
    for sp in ax.spines.values():
        sp.set_color(GREY)
    ax.set_xlabel("Minute"); ax.set_ylabel("Cumulative xG"); ax.set_xlim(0, 96)
    ax.set_ylim(0, max(s[s.is_team].shot_statsbomb_xg.sum(), s[~s.is_team].shot_statsbomb_xg.sum(), 0.3) * 1.22)
    ax.legend(facecolor=BG, edgecolor=GREY, labelcolor=TEXT, loc="upper left")
    ax.grid(alpha=0.15)
    title(fig, label or f"{TEAM} vs {opp}: xG timeline", "Cumulative expected goals | gold dots = goals")
    finish(fig, "xg_timeline_final")


def kpi_chart(k):
    fig, axs = plt.subplots(1, 3, figsize=(15, 5.8))
    fig.set_facecolor(BG)
    fig.subplots_adjust(top=0.76, bottom=0.22, wspace=0.22, left=0.03, right=0.98)
    labels = [m.split(" (")[0] for m in k.match]
    for ax, (cols, ttl, fmt) in zip(axs, [(["xg", "xg_against"], "xG for vs against", "{:.1f}"),
                                           (["possession"], "Possession", "{:.0%}"),
                                           (["ppda"], "PPDA (lower = more intense press)", "{:.1f}")]):
        ax.set_facecolor(BG)
        w = 0.38 if len(cols) == 2 else 0.6
        for i, (c, col) in enumerate(zip(cols, [RED, CYAN])):
            pos = np.arange(len(k)) + (i - (len(cols) - 1) / 2) * w
            bars = ax.bar(pos, k[c], width=w, color=col)
            for b, v in zip(bars, k[c]):
                ax.text(b.get_x() + b.get_width() / 2, b.get_height(), fmt.format(v), ha="center", va="bottom",
                        fontsize=10.5, fontweight="bold", color=TEXT)
        ax.set_ylim(0, max(k[c_].max() for c_ in cols) * 1.18)
        ax.set_xticks(range(len(k)), labels, rotation=35, ha="right", fontsize=11)
        ax.set_title(ttl, color=TEXT, fontsize=12.5, fontweight="bold")
        ax.tick_params(left=False, labelleft=False)
        for sp in ax.spines.values():
            sp.set_visible(False)
    w = int((k.goals > k.goals_against).sum()); d = int((k.goals == k.goals_against).sum())
    title(fig, f"{TEAM} match by match, Euro 2024",
          f"Red = {TEAM}, blue = opponent | {len(k)} matches: {w}W {d}D {len(k) - w - d}L (90/120 min)")
    finish(fig, "match_kpis")


# ------------------------------------------------------------------ Nacsport clip playlist
def build_clips(ev):
    """Timecoded list of moments to cut in Nacsport (StatsBomb timestamps are per half)."""
    t = ev[ev.is_team].copy()
    shots = t[t.type_name == "Shot"].assign(category=lambda d: np.where(d.shot_outcome_name == "Goal", "Goal", "Shot"))
    in_box = lambda x, y: (x >= 102) & y.between(18, 62)
    entries = t[(t.type_name == "Pass") & t.pass_outcome_name.isna() & ~in_box(t.x, t.y) &
                in_box(t.end_x, t.end_y) & (t.pass_type_name != "Corner")].assign(category="Box entry (pass)")
    high = t[t.type_name.isin(["Ball Recovery", "Interception"]) & (t.x >= 80)].assign(category="High regain")
    corners = t[(t.type_name == "Pass") & (t.pass_type_name == "Corner")].assign(category="Corner")
    c = pd.concat([shots, entries, high, corners])
    c["match"] = c.opponent.map(lambda o: f"{TEAM} vs {o}")
    c["clip_start"] = c.timestamp.str[:8]
    return c[["match", "period", "clip_start", "minute", "second", "category", "player",
              "play_pattern_name"]].sort_values(["match", "period", "minute", "second"])


def clip_playlist(ev, meta):
    out = build_clips(ev)
    out.to_csv(ROOT / "nacsport" / "clip_playlist.csv", index=False)
    return out.category.value_counts().to_dict(), len(out)


# ------------------------------------------------------------------ main
def main():
    FIG.mkdir(parents=True, exist_ok=True)
    meta, ev = load()
    k = match_kpis(meta, ev)
    k.round(3).to_csv(OUT / "match_kpis.csv", index=False)
    kpi_chart(k)
    shot_map(ev, True, "shot_map_spain")
    shot_map(ev, False, "shot_map_conceded")
    final = meta.iloc[-1]
    pass_network(ev, final.match_id, f"Final vs {final.opponent}")
    lanes, n_entries = buildup_map(ev)
    avg_h, share_high = pressing_map(ev)
    corner_tech, n_corners, sp_shots, sp_xg, sp_goals = corner_map(ev)
    players = player_table(ev)
    players.round(2).to_csv(OUT / "player_stats.csv")
    labels = [(n, n) for n in ["Lamine Yamal", "Nico Williams", "Daniel Olmo"]]
    key_player_heatmaps(ev, labels)
    xg_timeline(ev, final.match_id, final.opponent, f"Final: {TEAM} {final.score} {final.opponent}, xG timeline")
    clips, n_clips = clip_playlist(ev, meta)

    tot = {"matches": len(k), "goals": int(k.goals.sum()), "goals_against": int(k.goals_against.sum()),
           "xg": float(k.xg.sum()), "xg_against": float(k.xg_against.sum()),
           "shots": int(k.shots.sum()), "shots_against": int(k.shots_against.sum()),
           "possession": float(k.possession.mean()), "pass_completion": float(k.pass_completion.mean()),
           "ppda": float(k.ppda.mean()), "field_tilt": float(k.field_tilt.mean()),
           "high_recoveries_pm": float(k.high_recoveries.mean()), "prog_passes_pm": float(k.progressive_passes.mean()),
           "formations": k.formation.value_counts().to_dict(),
           "lane_share": {str(a): float(b) for a, b in lanes.items()}, "final_third_entries": n_entries,
           "avg_action_height": float(avg_h), "share_actions_att_third": float(share_high),
           "corners": n_corners, "corner_technique": corner_tech, "set_piece_shots": sp_shots,
           "set_piece_xg": sp_xg, "set_piece_goals": sp_goals,
           "top_players": players.head(6).round(2).reset_index().rename(columns={"index": "player"}).to_dict("records"),
           "clip_counts": clips, "clips_total": n_clips,
           "xga_hi": float(k[k.ppda > 18].xg_against.mean()), "xga_lo": float(k[k.ppda <= 18].xg_against.mean()),
           "players": [dict(name=n, **{c: float(r[c]) for c in ["goals", "xg", "xa", "key_passes", "prog_carries", "dribbles"]})
                       for n, r in players.head(5).iterrows()],
           "kpis": k.round(3).to_dict("records")}
    (OUT / "metrics.json").write_text(json.dumps(tot, indent=2, default=str))
    print(json.dumps({x: tot[x] for x in tot if x not in ("kpis", "top_players")}, indent=2, default=str))
    print(players.head(8).round(2).to_string())


if __name__ == "__main__":
    main()
