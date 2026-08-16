#!/usr/bin/env python3
"""Build the one-page leave-behind: HTML -> PDF, with the QR generated in.

US Letter, one side, meant to be handed over at the end of a meeting or
dropped in an envelope. Same navy and gold as the data-centre explainer and
the 13F report, so the three read as one firm's paper.

The QR is drawn as an inline SVG path rather than a raster: it stays sharp at
any print size, adds no image file to carry around, and cannot silently fail
to embed the way a linked PNG can.
"""

import re
import subprocess
from pathlib import Path

import segno

OUT = Path("/var/www/fleminganalytic/client-prod/pitch")  # the web root, so it is downloadable
TARGET_URL = "https://fleminganalytic.com/approach"

NAVY = "#16324f"
NAVY_DEEP = "#0e2138"
GOLD = "#e8b923"
CREAM = "#fdfbf4"


def qr_svg(url: str) -> str:
    """The QR as an inline <svg>, gold on transparent.

    Error correction M: the code survives a coffee ring or a staple through
    a corner, which is the failure mode for something printed and carried.
    """
    qr = segno.make(url, error="m")
    # Dark modules on a light ground - the polarity every scanner expects.
    # Drawn the other way round (gold on navy) it looked better on the sheet
    # and would not decode: inverted codes are optional for a reader to
    # support, and a flyer has to work with whatever phone is in the room.
    # Verified by rendering the page and decoding it back.
    # border=4 is the quiet zone the QR spec requires. Without it many
    # readers simply never find the code - the cream padding around the
    # tile looks like the same thing and is not, because it is outside the
    # symbol's own coordinate space.
    scale, border = 10, 4
    svg = qr.svg_inline(scale=scale, border=border, dark=NAVY, light=CREAM)
    # segno stamps a fixed width/height on the <svg> and emits no viewBox, so
    # the code drew at its natural size in the corner of the tile whatever the
    # stylesheet said. Swap them for a viewBox and it scales to the frame.
    side = qr.symbol_size(scale=scale, border=border)[0]
    svg = re.sub(r'<svg[^>]*?>',
                 f'<svg viewBox="0 0 {side} {side}" xmlns="http://www.w3.org/2000/svg" class="segno">',
                 svg, count=1)
    return svg


def build_html() -> str:
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>Fleming Analytic Resources</title>
<style>
  @page {{ size: Letter; margin: 0; }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; width: 8.5in; height: 11in;
    background: {NAVY_DEEP};
    color: {CREAM};
    font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
    -webkit-font-smoothing: antialiased;
  }}
  .sheet {{ padding: 0.62in 0.68in 0.5in; height: 11in; display: flex; flex-direction: column; }}

  .brand {{ display: flex; align-items: center; gap: 9px;
            font-size: 8pt; letter-spacing: .22em; text-transform: uppercase;
            color: {GOLD}; font-weight: 700; }}
  .brand .dot {{ width: 13px; height: 13px; border-radius: 999px; background: {GOLD}; flex: 0 0 13px; }}

  h1 {{ font-size: 33pt; line-height: 1.04; letter-spacing: -.025em; font-weight: 700;
        margin: 20px 0 0; max-width: 6.5in; }}
  h1 .quiet {{ color: {GOLD}; }}

  .lead {{ font-size: 12.4pt; line-height: 1.5; margin: 15px 0 0; max-width: 6.3in;
           color: #e7e3d8; }}
  .lead b {{ color: {CREAM}; font-weight: 600; }}

  .rule {{ height: 2px; background: {GOLD}; width: 54px; margin: 20px 0 0; }}

  .body {{ font-size: 10.4pt; line-height: 1.62; color: #c6cfdb; margin: 14px 0 0; max-width: 6.4in; }}
  .body .em {{ color: {CREAM}; font-weight: 600; }}

  .steps {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 13px; margin: 22px 0 0; }}
  .step {{ border-top: 2px solid rgba(232,185,35,.5); padding-top: 9px; }}
  .step h3 {{ margin: 0 0 5px; font-size: 11pt; color: {GOLD}; letter-spacing: -.01em; }}
  .step p {{ margin: 0; font-size: 8.6pt; line-height: 1.5; color: #b7c2d1; }}

  .proof {{ margin: 22px 0 0; padding: 14px 16px; background: rgba(255,255,255,.045);
            border-left: 3px solid {GOLD}; border-radius: 0 6px 6px 0; }}
  .proof p {{ margin: 0; font-size: 9.6pt; line-height: 1.62; color: #d3dae4; }}
  .proof b {{ color: {CREAM}; }}

  .spacer {{ flex: 1 1 auto; }}

  .concede {{ margin: 16px 0 0; }}
  .concede p {{ margin: 0; font-size: 9.6pt; line-height: 1.62; color: #9fb0c4; max-width: 6.4in; }}
  .concede .k {{ color: {GOLD}; font-weight: 700; }}

  .reframe {{ margin: 0 0 20px; font-size: 12.6pt; line-height: 1.48; color: #dfe6ee;
              max-width: 6.4in; letter-spacing: -.005em; }}
  .reframe .k {{ color: {CREAM}; font-weight: 700; }}

  .foot {{ display: flex; align-items: flex-end; justify-content: space-between; gap: 26px;
           border-top: 1px solid rgba(255,255,255,.15); padding-top: 17px; }}
  .ask h2 {{ margin: 0 0 7px; font-size: 15.5pt; letter-spacing: -.015em; color: {CREAM}; }}
  .ask p {{ margin: 0; font-size: 9.6pt; line-height: 1.6; color: #b7c2d1; max-width: 4.1in; }}
  .ask .contact {{ margin-top: 11px; font-size: 9.6pt; color: {GOLD}; font-weight: 600; }}

  .qr {{ flex: 0 0 auto; text-align: center; }}
  .qr .frame {{ width: 1.42in; height: 1.42in; padding: 9px; background: {CREAM};
                border-radius: 9px; box-shadow: 0 0 0 1.5px rgba(232,185,35,.55); }}
  .qr svg {{ width: 100%; height: 100%; display: block; }}
  .qr .cap {{ margin-top: 7px; font-size: 7pt; letter-spacing: .11em; text-transform: uppercase;
              color: #93a2b5; }}
</style></head>
<body><div class="sheet">

  <div class="brand"><span class="dot"></span> Fleming Analytic Resources</div>

  <h1>AI writes the first draft.<br><span class="quiet">Somebody still has to read it.</span></h1>

  <p class="lead">Here's the pitch you've heard all year: AI will do the work of ten
  people. It will. <b>It will also do the work of ten people who don't know they're
  wrong.</b></p>

  <div class="rule"></div>

  <p class="body">AI didn't remove the work — it moved it. The hours you used to spend
  producing a draft are the hours you now spend deciding whether it's true, and almost
  nobody has rebudgeted for that. Do all of it by hand and you pay ten times over for the
  same output. Ship it unread and you find out what was wrong from a customer.
  <span class="em">So that's what we sell: the reading.</span></p>

  <div class="steps">
    <div class="step"><h3>Scope</h3><p>A week with whoever runs the process and whoever
      pays for it. What breaks, and what "fixed" looks like on a Tuesday.</p></div>
    <div class="step"><h3>Draft</h3><p>AI does the first pass, directed by someone who
      already knows what the output should look like. The fast part.</p></div>
    <div class="step"><h3>Review</h3><p>A person reads every line and is answerable for
      it. The expensive part, and the part that gets skipped.</p></div>
    <div class="step"><h3>Hand over</h3><p>Into production, with a manual generated from
      the running software. Software nobody can use isn't a delivery.</p></div>
  </div>

  <div class="proof">
    <p><b>You don't have to take our word for it.</b> Nineteen working applications are on
    our site and you can open every one without talking to anybody — a parish running its
    own bulletin, a restaurant platform, an ICU dashboard, a ticketing site where fans pay
    what the venue set and nothing else. Five more run on client domains. Some of it was
    drafted by AI; all of it was read by someone who had to answer for it.</p>
  </div>

  <div class="concede">
    <p><span class="k">Credit where it's due:</span> none of that is clever. It's ordinary
    work done in the open, where you can check it. That's the whole argument — press the
    buttons before you spend a dollar.</p>
  </div>

  <div class="spacer"></div>

  <p class="reframe">Doing none of it by hand is how you end up with something confident and
  wrong. Doing all of it by hand is how you end up late. <span class="k">The work is in the
  middle.</span></p>

  <div class="foot">
    <div class="ask">
      <h2>Bring us the job you can't afford to get wrong.</h2>
      <p>The job that eats a day a week. The report nobody trusts. One conversation, no
      charge, and a straight answer about whether this is worth doing at all.</p>
      <div class="contact">fleminganalytic.com &nbsp;·&nbsp; john.fleming@fleminganalytic.com</div>
    </div>
    <div class="qr">
      <div class="frame">{qr_svg(TARGET_URL)}</div>
      <div class="cap">Scan to read more</div>
    </div>
  </div>

</div></body></html>"""


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    html_path = OUT / "fleming-analytic-onepager.html"
    pdf_path = OUT / "fleming-analytic-onepager.pdf"

    html_path.write_text(build_html())
    print(f"wrote {html_path} ({html_path.stat().st_size/1024:.0f} KB)")

    proc = subprocess.run(["weasyprint", str(html_path), str(pdf_path)],
                          capture_output=True, text=True, timeout=180)
    if proc.returncode != 0:
        raise SystemExit(f"weasyprint failed:\n{proc.stderr[:600]}")

    raw = pdf_path.read_bytes()
    import re, zlib
    pages = len(re.findall(rb"/Type\s*/Page[^s]", raw))
    for m in re.finditer(rb"stream\r?\n", raw):
        e = raw.find(b"endstream", m.end())
        try:
            pages += len(re.findall(rb"/Type\s*/Page[^s]", zlib.decompress(raw[m.end():e])))
        except Exception:
            pass
    print(f"wrote {pdf_path} ({pdf_path.stat().st_size/1024:.0f} KB, {pages} page(s))")
    if pages != 1:
        print(f"  ! a one-pager that is {pages} pages is not a one-pager")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
