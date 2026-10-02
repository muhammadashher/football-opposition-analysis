// Build the opposition-report deck. Run from the project root: node reports/build_deck.js
const pptxgen = require('pptxgenjs');
const path = require('path');
const fs = require('fs');
const ROOT = path.resolve(__dirname, '..');
const M = JSON.parse(fs.readFileSync(process.argv[2] || path.join(ROOT, 'outputs', 'metrics.json')));
const FIG = f => path.join(ROOT, 'outputs', 'figures', f);

// Place a PNG inside a box without distortion (reads size from the PNG header)
function fitImage(s, file, x, y, bw, bh) {
  const buf = fs.readFileSync(FIG(file));
  const iw = buf.readUInt32BE(16), ih = buf.readUInt32BE(20);
  const r = Math.min(bw / iw, bh / ih), w = iw * r, h = ih * r;
  s.addImage({ path: FIG(file), x: x + (bw - w) / 2, y: y + (bh - h) / 2, w, h });
}
const pres = new pptxgen(); pres.layout = 'LAYOUT_16x9'; pres.title = 'Opposition Report: Spain';
const BG = '0E1A1F', PANEL = '17262C', TEXT = 'F2F4F3', MUTED = 'A9B8B4', RED = 'E63946', GOLD = 'F4B942', CYAN = '4CC9F0';
const H = 'Arial', B = 'Calibri';
const pct = x => Math.round(x * 100) + '%';

function base(title, sub) {
  const s = pres.addSlide(); s.background = { color: BG };
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 0.12, h: 5.625, fill: { color: RED } });
  s.addText(title, { x: 0.4, y: 0.22, w: 9.2, h: 0.55, fontFace: H, fontSize: 24, bold: true, color: TEXT, margin: 0 });
  if (sub) s.addText(sub, { x: 0.4, y: 0.75, w: 9.2, h: 0.32, fontFace: B, fontSize: 13, color: MUTED, margin: 0 });
  s.addText('Data: StatsBomb Open Data | Euro 2024 | Non-confidential sample', { x: 0.4, y: 5.3, w: 9.2, h: 0.22, fontFace: B, fontSize: 8.5, color: '6F7F7B', margin: 0 });
  return s;
}
function points(s, items, x, y, w, h) {
  s.addText(items.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < items.length - 1 } })),
    { x, y, w, h, fontFace: B, fontSize: 13, color: TEXT, valign: 'top', paraSpaceAfter: 8, margin: 0 });
}
function stat(s, x, y, w, big, label, col) {
  s.addShape(pres.shapes.RECTANGLE, { x, y, w, h: 0.95, fill: { color: PANEL } });
  s.addShape(pres.shapes.RECTANGLE, { x, y, w: 0.06, h: 0.95, fill: { color: col || RED } });
  s.addText(big, { x: x + 0.2, y: y + 0.06, w: w - 0.3, h: 0.5, fontFace: H, fontSize: 22, bold: true, color: col || GOLD, margin: 0 });
  s.addText(label, { x: x + 0.2, y: y + 0.55, w: w - 0.3, h: 0.35, fontFace: B, fontSize: 11, color: MUTED, margin: 0 });
}
const L = M.lane_share, CT = M.corner_technique;

// 1 Title
let s = pres.addSlide(); s.background = { color: BG };
s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 0.25, h: 5.625, fill: { color: RED } });
s.addText('OPPOSITION REPORT', { x: 0.7, y: 1.2, w: 8, h: 0.4, fontFace: B, fontSize: 14, bold: true, color: GOLD, charSpacing: 4, margin: 0 });
s.addText('Spain', { x: 0.7, y: 1.65, w: 8, h: 1.0, fontFace: H, fontSize: 54, bold: true, color: TEXT, margin: 0 });
s.addText('UEFA Euro 2024 champions | 7 matches analysed', { x: 0.7, y: 2.7, w: 8, h: 0.45, fontFace: B, fontSize: 18, color: MUTED, margin: 0 });
s.addText('Opposition analysis by Muhammed Ashhar A, Performance Analyst', { x: 0.7, y: 4.2, w: 8.5, h: 0.35, fontFace: B, fontSize: 13, color: TEXT, margin: 0 });
s.addText('Tools: Nacsport (video coding) | StatsBomb event data | Python (mplsoccer)', { x: 0.7, y: 4.55, w: 8.5, h: 0.3, fontFace: B, fontSize: 11, color: MUTED, margin: 0 });
s.addNotes('Non-confidential sample report built on StatsBomb open data, written as if our team plays Spain next.');

// 2 Summary
s = base('Summary: how Spain play and how we can hurt them');
const cards = [
  ['Control', `${pct(M.possession)} possession, ${pct(M.pass_completion)} passing and ${pct(M.field_tilt)} field tilt on average.`, RED],
  ['Wide threat', `${pct(L.Left)} of final-third entries come down their left, ${pct(L.Right)} down the right and only ${pct(L.Centre)} centrally.`, GOLD],
  ['Selective press', `PPDA ${M.ppda.toFixed(1)} and ${Math.round(M.high_recoveries_pm)} high regains per match. Short build-up is risky.`, CYAN],
  ['Vulnerable without the ball', `${M.xga_hi.toFixed(2)} xG conceded per match when their press dropped (PPDA above 18), vs ${M.xga_lo.toFixed(2)} otherwise.`, RED]];
cards.forEach((c, i) => {
  const x = 0.4 + (i % 2) * 4.65, y = 1.2 + Math.floor(i / 2) * 1.95;
  s.addShape(pres.shapes.RECTANGLE, { x, y, w: 4.45, h: 1.75, fill: { color: PANEL } });
  s.addShape(pres.shapes.RECTANGLE, { x, y, w: 4.45, h: 0.07, fill: { color: c[2] } });
  s.addText(c[0], { x: x + 0.25, y: y + 0.2, w: 4, h: 0.4, fontFace: H, fontSize: 17, bold: true, color: c[2], margin: 0 });
  s.addText(c[1], { x: x + 0.25, y: y + 0.65, w: 4, h: 1.0, fontFace: B, fontSize: 13.5, color: TEXT, valign: 'top', margin: 0 });
});
s.addNotes('Four messages for the team meeting. Each is backed by the slides that follow.');

// 3 Results
s = base('7 wins from 7, built on control', 'Match-by-match xG, possession and pressing intensity');
fitImage(s, 'match_kpis.png', 0.85, 1.15, 8.3, 2.99);
stat(s, 0.4, 4.3, 2.2, `${M.goals}-${M.goals_against}`, 'Goals for and against');
stat(s, 2.75, 4.3, 2.2, `${M.xg.toFixed(1)} - ${M.xg_against.toFixed(1)}`, 'xG for and against');
stat(s, 5.1, 4.3, 2.2, `${M.shots} - ${M.shots_against}`, 'Shots for and against');
stat(s, 7.45, 4.3, 2.2, `${M.formations['4231']} of 7`, 'Matches in 4-2-3-1', CYAN);

// 4 Shape
s = base('Shape and build-up: 4-2-3-1 with high full-backs', 'Pass network, final vs England (before first substitution)');
fitImage(s, 'pass_network_final.png', 0.35, 1.15, 5.9, 4.03);
points(s, ['Rodri and Fabián Ruiz form the double pivot; the build-up runs through Laporte, Le Normand and Rodri.',
  'Cucurella pushes high on the left, freeing Nico Williams to go 1v1.',
  'Yamal stays wide on the right with Carvajal behind him.',
  'Olmo floats between the lines as the No.10.'], 6.5, 1.25, 3.2, 3.9);

// 5 Entries
s = base('They attack down the flanks, mostly the left', `${M.final_third_entries} completed passes into the final third`);
fitImage(s, 'final_third_entries.png', 0.35, 1.15, 5.9, 4.03);
stat(s, 6.55, 1.25, 3.1, pct(L.Left), 'Entries down their left (Nico, Cucurella)');
stat(s, 6.55, 2.35, 3.1, pct(L.Right), 'Entries down their right (Yamal, Carvajal)', CYAN);
stat(s, 6.55, 3.45, 3.1, pct(L.Centre), 'Entries through the centre', MUTED);
s.addText('Plan: protect both flanks and keep the middle compact.', { x: 6.55, y: 4.55, w: 3.1, h: 0.6, fontFace: B, fontSize: 12, italic: true, color: GOLD, margin: 0 });

// 6 Shots
s = base('Chances come from central zones in the box', `${M.shots} shots, ${M.xg.toFixed(1)} xG, 14 goals from shots`);
fitImage(s, 'shot_map_spain.png', 0.3, 1.15, 5.3, 4.0);
points(s, ['Most shots are taken inside the box, between the posts.',
  `Average shot quality ${(M.xg / M.shots).toFixed(2)} xG: they work the ball into good positions rather than shooting from range.`,
  'Defend the six-yard box and the penalty spot area; track late runners like Olmo and Fabián Ruiz.'], 5.85, 1.3, 3.8, 3.8);

// 7 Pressing
s = base('Pressing: selective, but sharp when it triggers', 'Share of Spain defensive actions by zone');
fitImage(s, 'pressing_heatmap.png', 0.35, 1.15, 5.9, 4.03);
stat(s, 6.55, 1.25, 3.1, M.ppda.toFixed(1), 'Average PPDA');
stat(s, 6.55, 2.35, 3.1, String(Math.round(M.high_recoveries_pm)), 'High regains per match', CYAN);
stat(s, 6.55, 3.45, 3.1, pct(M.share_actions_att_third), 'Defensive actions in the attacking third');
s.addText('Plan: avoid slow short build-up; play beyond the first line.', { x: 6.55, y: 4.55, w: 3.1, h: 0.6, fontFace: B, fontSize: 12, italic: true, color: GOLD, margin: 0 });

// 8 Key players
s = base('Key threats', 'Where they receive and act, plus tournament output');
fitImage(s, 'key_player_heatmaps.png', 0.35, 1.1, 9.3, 2.6);
const head = ['Player', 'Goals', 'xG', 'xA', 'Key passes', 'Prog. carries', 'Dribbles'].map(t => ({ text: t, options: { bold: true, color: BG, fill: { color: GOLD } } }));
const rows = M.players.map(p => [p.name, p.goals, p.xg.toFixed(2), p.xa.toFixed(2), p.key_passes, p.prog_carries, p.dribbles].map(v => ({ text: String(v), options: { color: TEXT, fill: { color: PANEL } } })));
s.addTable([head, ...rows], { x: 0.4, y: 3.75, w: 9.2, colW: [2.2, 1, 1, 1, 1.3, 1.5, 1.2], fontFace: B, fontSize: 10.5, rowH: 0.24, border: { type: 'solid', pt: 0.5, color: BG }, align: 'center' });

// 9 Set pieces
s = base('Set pieces: inswinging corners to the six-yard box', `${M.corners} corners analysed`);
fitImage(s, 'corners.png', 0.3, 1.15, 5.5, 4.0);
stat(s, 6.0, 1.25, 3.65, `${CT.Inswinging} of ${M.corners}`, 'Corners delivered inswinging');
stat(s, 6.0, 2.35, 3.65, `${M.set_piece_shots} shots, ${M.set_piece_xg.toFixed(1)} xG`, 'From corner and free-kick phases', CYAN);
stat(s, 6.0, 3.45, 3.65, String(M.set_piece_goals), 'Goals from set-piece phases');
s.addText('Plan: zone the six-yard box and near post; man-mark Laporte and Le Normand.', { x: 6.0, y: 4.55, w: 3.65, h: 0.6, fontFace: B, fontSize: 12, italic: true, color: GOLD, margin: 0 });

// 10 Vulnerability
s = base('Where Spain are vulnerable', 'Shots conceded across the tournament');
fitImage(s, 'shot_map_conceded.png', 0.3, 1.15, 5.3, 4.0);
stat(s, 5.85, 1.25, 3.8, `${M.xga_hi.toFixed(2)} vs ${M.xga_lo.toFixed(2)}`, 'xG conceded per match: low press (PPDA 18+) vs others');
points(s, ['Croatia (2.48 xG) and Germany (1.63 xG) hurt Spain when possession was close to 50/50.',
  'When games become open and less controlled, Spain concede far more chances.',
  'Compete for the ball and play quickly in transition rather than sitting deep for 90 minutes.'], 5.85, 2.45, 3.8, 2.7);

// 11 Game plan
s = pres.addSlide(); s.background = { color: BG };
s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 0.12, h: 5.625, fill: { color: RED } });
s.addText('Game plan', { x: 0.4, y: 0.25, w: 9, h: 0.6, fontFace: H, fontSize: 28, bold: true, color: TEXT, margin: 0 });
[['Protect the flanks', 'Double up on Nico Williams and Yamal: full-back plus winger, show them inside.'],
 ['Stay compact centrally', 'Force play wide early; defend crosses and cut-backs into the six-yard area.'],
 ['Break their control', 'Press Rodri and the centre-backs in short, planned spells to deny rhythm.'],
 ['Play beyond the press', 'Avoid slow short build-up; attack the space behind their high full-backs.'],
 ['Set pieces', 'Zonal six-yard box and near post for inswinging corners; mark the centre-backs.']].forEach((r, i) => {
  const y = 1.1 + i * 0.82;
  s.addShape(pres.shapes.OVAL, { x: 0.45, y, w: 0.5, h: 0.5, fill: { color: GOLD } });
  s.addText(String(i + 1), { x: 0.45, y, w: 0.5, h: 0.5, fontFace: H, fontSize: 16, bold: true, color: BG, align: 'center', valign: 'middle', margin: 0 });
  s.addText(r[0], { x: 1.15, y: y - 0.03, w: 3.0, h: 0.56, fontFace: H, fontSize: 15, bold: true, color: TEXT, valign: 'middle', margin: 0 });
  s.addText(r[1], { x: 4.2, y: y - 0.03, w: 5.4, h: 0.56, fontFace: B, fontSize: 13, color: MUTED, valign: 'middle', margin: 0 });
});

// 12 Video plan
s = base('Video plan: clips for the team meeting', `${M.clips_total} timecoded moments to code and cut in Nacsport`);
const order = ['Shot', 'High regain', 'Box entry (pass)', 'Corner', 'Goal'];
s.addChart(pres.charts.BAR, [{ name: 'Clips', labels: order, values: order.map(o => M.clip_counts[o] || 0) }],
  { x: 0.4, y: 1.2, w: 5.2, h: 3.9, barDir: 'bar', chartColors: [RED], showValue: true, dataLabelColor: TEXT, dataLabelFontSize: 11,
    catAxisLabelColor: TEXT, valAxisLabelColor: MUTED, valGridLine: { color: '22343A', size: 0.5 }, catGridLine: { style: 'none' },
    catAxisOrientation: 'maxMin', showLegend: false, catAxisLabelFontSize: 12 });
points(s, ['Playlists by phase: build-up, final-third entries, chance creation, pressing, transitions, set pieces.',
  '6-10 clips per playlist, drawn with arrows and zones.',
  '2-3 minute key-threat reels for Yamal, Nico Williams and Olmo.',
  'Clip list and code window template included with this report.'], 5.9, 1.3, 3.8, 3.8);

pres.writeFile({ fileName: path.join(ROOT, 'reports', 'Opposition_Report_Spain_Euro2024.pptx') }).then(f => console.log('saved', f));
