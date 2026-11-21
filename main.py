#!/usr/bin/env python3
"""
news-image-20261120 entry: "The World in One Image" -- Friday 20 November 2026.

A pure Python 3 standard-library program that draws a newspaper front-page
poster of the day's six biggest world-news stories and writes it as a PNG
to /output/entry.png (falling back to ./entry.png when /output is not
writable). No third-party imports, no network, no randomness, no clock:
two runs always produce byte-identical output.

The PNG encoder is hand-rolled (zlib + struct) and all text is drawn with
an embedded 5x7 bitmap font defined below, so the only characters used are
the ones the font actually contains (A-Z, 0-9, space and - . , : % &).
"""

import os
import struct
import zlib

# --------------------------------------------------------------------------
# Canvas and palette
# --------------------------------------------------------------------------

W = 1000
H = 1000

PAPER = (250, 247, 238)   # off-white newsprint
INK = (22, 20, 18)        # near-black headline ink
SUB = (56, 52, 47)        # dark warm grey for subheads
RED = (176, 24, 20)       # accent red, used for the lead story only
LIGHT = (168, 160, 145)   # light rule colour inside the grid

# --------------------------------------------------------------------------
# Embedded 5x7 bitmap font. Each glyph is 7 rows of 5 characters;
# '#' marks an inked pixel. Only the characters in this table are drawn.
# --------------------------------------------------------------------------

GLYPHS = {
    ' ': ("     ", "     ", "     ", "     ", "     ", "     ", "     "),
    'A': (" ### ", "#   #", "#   #", "#####", "#   #", "#   #", "#   #"),
    'B': ("#### ", "#   #", "#   #", "#### ", "#   #", "#   #", "#### "),
    'C': (" ####", "#    ", "#    ", "#    ", "#    ", "#    ", " ####"),
    'D': ("###  ", "#  # ", "#   #", "#   #", "#   #", "#  # ", "###  "),
    'E': ("#####", "#    ", "#    ", "#### ", "#    ", "#    ", "#####"),
    'F': ("#####", "#    ", "#    ", "#### ", "#    ", "#    ", "#    "),
    'G': (" ####", "#    ", "#    ", "#  ##", "#   #", "#   #", " ####"),
    'H': ("#   #", "#   #", "#   #", "#####", "#   #", "#   #", "#   #"),
    'I': ("#####", "  #  ", "  #  ", "  #  ", "  #  ", "  #  ", "#####"),
    'J': ("#####", "    #", "    #", "    #", "    #", "#   #", " ### "),
    'K': ("#   #", "#  # ", "# #  ", "##   ", "# #  ", "#  # ", "#   #"),
    'L': ("#    ", "#    ", "#    ", "#    ", "#    ", "#    ", "#####"),
    'M': ("#   #", "## ##", "# # #", "# # #", "#   #", "#   #", "#   #"),
    'N': ("#   #", "##  #", "##  #", "# # #", "#  ##", "#  ##", "#   #"),
    'O': (" ### ", "#   #", "#   #", "#   #", "#   #", "#   #", " ### "),
    'P': ("#### ", "#   #", "#   #", "#### ", "#    ", "#    ", "#    "),
    'Q': (" ### ", "#   #", "#   #", "#   #", "# # #", "#  # ", " ## #"),
    'R': ("#### ", "#   #", "#   #", "#### ", "# #  ", "#  # ", "#   #"),
    'S': (" ####", "#    ", "#    ", " ### ", "    #", "    #", "#### "),
    'T': ("#####", "  #  ", "  #  ", "  #  ", "  #  ", "  #  ", "  #  "),
    'U': ("#   #", "#   #", "#   #", "#   #", "#   #", "#   #", " ### "),
    'V': ("#   #", "#   #", "#   #", "#   #", "#   #", " # # ", "  #  "),
    'W': ("#   #", "#   #", "#   #", "# # #", "# # #", "## ##", "#   #"),
    'X': ("#   #", " # # ", "  #  ", "  #  ", "  #  ", " # # ", "#   #"),
    'Y': ("#   #", "#   #", " # # ", "  #  ", "  #  ", "  #  ", "  #  "),
    'Z': ("#####", "    #", "   # ", "  #  ", " #   ", "#    ", "#####"),
    '0': (" ### ", "#  ##", "# # #", "# # #", "##  #", "#   #", " ### "),
    '1': ("  #  ", " ##  ", "# #  ", "  #  ", "  #  ", "  #  ", "#####"),
    '2': (" ### ", "#   #", "    #", "   # ", "  #  ", " #   ", "#####"),
    '3': ("#### ", "    #", "    #", " ### ", "    #", "    #", "#### "),
    '4': ("   # ", "  ## ", " # # ", "#  # ", "#####", "   # ", "   # "),
    '5': ("#####", "#    ", "#### ", "    #", "    #", "#   #", " ### "),
    '6': (" ### ", "#    ", "#    ", "#### ", "#   #", "#   #", " ### "),
    '7': ("#####", "    #", "   # ", "  #  ", "  #  ", "  #  ", "  #  "),
    '8': (" ### ", "#   #", "#   #", " ### ", "#   #", "#   #", " ### "),
    '9': (" ### ", "#   #", "#   #", " ####", "    #", "    #", " ### "),
    '-': ("     ", "     ", "     ", "#####", "     ", "     ", "     "),
    '.': ("     ", "     ", "     ", "     ", "     ", "     ", " ##  "),
    ',': ("     ", "     ", "     ", "     ", "     ", " ##  ", " #   "),
    ':': ("     ", " ##  ", " ##  ", "     ", "     ", " ##  ", " ##  "),
    '%': ("##  #", "## # ", "   # ", "  #  ", " #   ", "#  ##", "   ##"),
    '&': (" ### ", "#   #", "#   #", " ### ", "# # #", "#  # ", " ## #"),
}

GLYPH_W = 5
GLYPH_H = 7
ADVANCE = 6  # glyph width plus one column of tracking, in font units

# --------------------------------------------------------------------------
# The day's stories (verified headlines of 20 November 2026)
# --------------------------------------------------------------------------

MASTHEAD = "THE WORLD IN ONE IMAGE"
DATELINE = "FRIDAY 20 NOVEMBER 2026"
FOOTER = "SIX STORIES - ONE DAY - ONE IMAGE"

LEAD_HEAD = "TRUMP XI PUTIN MEET IN SHENZHEN"
LEAD_SUB = "FIRST THREE-WAY SUMMIT ISSUES JOINT PEACE DECLARATION"

# (headline, subhead) pairs for the 2x2 grid, in reading order.
GRID_STORIES = [
    ("ICJ: MYANMAR COMMITTED GENOCIDE",
     "WORLD COURT RULES ON ROHINGYA, FIRST SUCH FINDING AGAINST A STATE"),
    ("MISSILE DAMAGES RIYADH TOWER",
     "HOUTHI STRIKE HITS PIF SKYSCRAPER IN SAUDI CAPITAL"),
    ("RUSSIA UNLEASHES HUGE STRIKE ON KYIV",
     "OVERNIGHT MISSILE AND DRONE BARRAGE DAMAGES EMBASSIES"),
    ("CYCLONE AKVAN HITS INDIA",
     "STORM MAKES LANDFALL IN ODISHA"),
]

CLOSER_HEAD = "MARKETS SLIDE ON AI DOUBTS"
CLOSER_SUB = "NIKKEI -4.8% AFTER ANTHROPIC DEBUT, S&P 500 DOWN SIXTH DAY"

# --------------------------------------------------------------------------
# Drawing helpers (operate on an RGB framebuffer bytearray)
# --------------------------------------------------------------------------


def new_framebuffer():
    return bytearray(bytes(PAPER) * (W * H))


def fill_rect(fb, x, y, w, h, color):
    """Fill a clipped rectangle of the framebuffer with an RGB colour."""
    x0 = max(0, x)
    y0 = max(0, y)
    x1 = min(W, x + w)
    y1 = min(H, y + h)
    if x0 >= x1 or y0 >= y1:
        return
    row = bytes(color) * (x1 - x0)
    n = len(row)
    for yy in range(y0, y1):
        off = (yy * W + x0) * 3
        fb[off:off + n] = row


def text_width(text, scale):
    if not text:
        return 0
    return len(text) * ADVANCE * scale - scale


def draw_text(fb, x, y, text, scale, color, bold=False):
    """Draw text with the embedded font; returns the drawn width in pixels."""
    extra = max(1, scale // 3) if bold else 0
    cx = x
    for ch in text:
        glyph = GLYPHS.get(ch, GLYPHS[' '])
        for ri in range(GLYPH_H):
            row = glyph[ri]
            for ci in range(GLYPH_W):
                if row[ci] == '#':
                    fill_rect(fb, cx + ci * scale, y + ri * scale,
                              scale + extra, scale, color)
        cx += ADVANCE * scale
    return text_width(text, scale)


def draw_centered(fb, center_x, y, text, scale, color, bold=False):
    return draw_text(fb, center_x - text_width(text, scale) // 2,
                     y, text, scale, color, bold)


def wrap(text, max_chars):
    """Greedy word wrap on character count (the font is fixed-width)."""
    lines = []
    cur = ""
    for word in text.split(" "):
        trial = word if not cur else cur + " " + word
        if len(trial) <= max_chars:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_block(fb, x, y, head, sub, head_scale, sub_scale, max_w,
               head_color, sub_color):
    """Draw one story: bold headline lines then subhead lines.

    Returns the y just below the block.
    """
    head_adv = ADVANCE * head_scale
    sub_adv = ADVANCE * sub_scale
    head_lines = wrap(head, max_w // head_adv)
    sub_lines = wrap(sub, max_w // sub_adv)
    cy = y
    for line in head_lines:
        draw_text(fb, x, cy, line, head_scale, head_color, bold=True)
        cy += GLYPH_H * head_scale + head_scale * 2
    cy += 2  # small gap between headline and subhead
    for line in sub_lines:
        draw_text(fb, x, cy, line, sub_scale, sub_color)
        cy += GLYPH_H * sub_scale + sub_scale * 2 - 1
    return cy


# --------------------------------------------------------------------------
# Page layout
# --------------------------------------------------------------------------

MARGIN = 30
CONTENT_W = W - 2 * MARGIN          # 940
COL_GAP = 20
COL_W = (CONTENT_W - COL_GAP) // 2  # 460
COL2_X = MARGIN + COL_W + COL_GAP   # 510


def render():
    fb = new_framebuffer()

    # Double-rule page frame.
    fill_rect(fb, 10, 10, W - 20, 3, INK)
    fill_rect(fb, 10, H - 13, W - 20, 3, INK)
    fill_rect(fb, 10, 10, 3, H - 20, INK)
    fill_rect(fb, W - 13, 10, 3, H - 20, INK)
    fill_rect(fb, 18, 18, W - 36, 1, INK)
    fill_rect(fb, 18, H - 19, W - 36, 1, INK)
    fill_rect(fb, 18, 18, 1, H - 36, INK)
    fill_rect(fb, W - 19, 18, 1, H - 36, INK)

    # Masthead and date line.
    draw_centered(fb, W // 2, 46, MASTHEAD, 6, INK, bold=True)
    fill_rect(fb, MARGIN, 106, CONTENT_W, 3, INK)
    fill_rect(fb, MARGIN, 113, CONTENT_W, 1, INK)
    draw_centered(fb, W // 2, 128, DATELINE, 4, INK, bold=True)
    fill_rect(fb, MARGIN, 172, CONTENT_W, 1, INK)
    fill_rect(fb, MARGIN, 177, CONTENT_W, 3, INK)

    # Lead story, headline in red.
    draw_block(fb, MARGIN, 206, LEAD_HEAD, LEAD_SUB, 6, 3,
               CONTENT_W, RED, SUB)
    fill_rect(fb, MARGIN, 392, CONTENT_W, 3, INK)

    # 2x2 grid of stories 2-5, split by light rules.
    grid_top = 420
    row_h = 147
    row2_y = grid_top + row_h + 28
    draw_block(fb, MARGIN, grid_top, GRID_STORIES[0][0], GRID_STORIES[0][1],
               4, 3, COL_W, INK, SUB)
    draw_block(fb, COL2_X, grid_top, GRID_STORIES[1][0], GRID_STORIES[1][1],
               4, 3, COL_W, INK, SUB)
    draw_block(fb, MARGIN, row2_y, GRID_STORIES[2][0], GRID_STORIES[2][1],
               4, 3, COL_W, INK, SUB)
    draw_block(fb, COL2_X, row2_y, GRID_STORIES[3][0], GRID_STORIES[3][1],
               4, 3, COL_W, INK, SUB)
    fill_rect(fb, 499, grid_top, 2, row2_y + row_h - grid_top, LIGHT)
    fill_rect(fb, MARGIN, grid_top + row_h + 13, CONTENT_W, 2, LIGHT)

    # Closing story, full width.
    fill_rect(fb, MARGIN, 790, CONTENT_W, 3, INK)
    draw_block(fb, MARGIN, 814, CLOSER_HEAD, CLOSER_SUB, 4, 3,
               CONTENT_W, INK, SUB)

    # Footer.
    fill_rect(fb, MARGIN, 927, CONTENT_W, 1, INK)
    draw_centered(fb, W // 2, 940, FOOTER, 3, SUB)

    return fb


# --------------------------------------------------------------------------
# Minimal deterministic PNG encoder (8-bit truecolour, filter 0 rows)
# --------------------------------------------------------------------------


def _chunk(tag, payload):
    return (struct.pack(">I", len(payload)) + tag + payload
            + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF))


def encode_png(fb):
    raw = bytearray()
    stride = W * 3
    for yy in range(H):
        raw.append(0)
        raw += fb[yy * stride:(yy + 1) * stride]
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n"
            + _chunk(b"IHDR", ihdr)
            + _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + _chunk(b"IEND", b""))


def main():
    data = encode_png(render())
    path = os.path.join("/output", "entry.png")
    try:
        os.makedirs("/output", exist_ok=True)
        with open(path, "wb") as fh:
            fh.write(data)
    except OSError:
        path = os.path.join(os.getcwd(), "entry.png")
        with open(path, "wb") as fh:
            fh.write(data)
    print(path)


if __name__ == "__main__":
    main()
