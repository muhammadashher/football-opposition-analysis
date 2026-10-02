"""Turn the clip playlist into a Sportscode-style XML timeline and per-match CSVs.

StatsBomb timestamps restart at 00:00 each half. Set each match's video offsets
(seconds into the video file where each half kicks off) in OFFSETS, then re-run.
"""
from pathlib import Path
import xml.etree.ElementTree as ET

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
NAC = ROOT / "nacsport"
LEAD, LAG = 8, 6                      # seconds before / after each event
OFFSETS = {}                          # e.g. {"Spain vs England": {1: 35, 2: 3210}}


def to_seconds(ts):
    h, m, s = (int(x) for x in ts.split(":"))
    return h * 3600 + m * 60 + s


def main():
    clips = pd.read_csv(NAC / "clip_playlist.csv")
    clips["event_s"] = clips.clip_start.map(to_seconds)
    clips["offset"] = [OFFSETS.get(m, {}).get(p, 0) for m, p in zip(clips.match, clips.period)]
    clips["start_s"] = (clips.event_s + clips.offset - LEAD).clip(lower=0)
    clips["end_s"] = clips.event_s + clips.offset + LAG
    for match, g in clips.groupby("match"):
        root = ET.Element("file")
        instances = ET.SubElement(root, "ALL_INSTANCES")
        for i, r in enumerate(g.itertuples(), 1):
            inst = ET.SubElement(instances, "instance")
            ET.SubElement(inst, "ID").text = str(i)
            ET.SubElement(inst, "start").text = f"{r.start_s:.1f}"
            ET.SubElement(inst, "end").text = f"{r.end_s:.1f}"
            ET.SubElement(inst, "code").text = r.category
            for group, text in [("Player", r.player), ("Half", f"H{r.period}"), ("Phase", r.play_pattern_name)]:
                lab = ET.SubElement(inst, "label")
                ET.SubElement(lab, "group").text = group
                ET.SubElement(lab, "text").text = str(text)
        safe = match.replace(" ", "_")
        ET.ElementTree(root).write(NAC / f"timeline_{safe}.xml", encoding="utf-8", xml_declaration=True)
        g.drop(columns=["event_s", "offset"]).to_csv(NAC / f"clips_{safe}.csv", index=False)
    print(f"Exported {len(clips)} clips across {clips.match.nunique()} matches")


if __name__ == "__main__":
    main()
