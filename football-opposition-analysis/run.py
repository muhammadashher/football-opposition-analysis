"""Run the full opposition-analysis workflow."""
import subprocess
import sys

steps = [["src/download_data.py"], ["src/analysis.py"], ["src/nacsport_export.py"], ["src/report.py"]]
for step in steps:
    print(">>", " ".join(step))
    subprocess.run([sys.executable, *step], check=True)
print(">> Done. Dashboard: streamlit run app.py  |  Deck (optional): node reports/build_deck.js")
