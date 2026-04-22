"""
AHA PDF Generator v2 — RESA Power Service
Multi-page fillable PDF Activity Hazard Analysis forms.

Usage:
    python aha_generator.py                          # Blank master
    python aha_generator.py --activity load_monitor   # Pre-populated activity AHA

Output lands in ../artifacts/
"""

import argparse
import importlib
import os
import sys
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.colors import HexColor, white, black, Color
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit

PACKAGE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTIFACTS_DIR = os.path.join(PACKAGE_ROOT, "artifacts")


# =============================================================================
# BRAND COLORS
# =============================================================================
RESA_NAVY = HexColor("#002B5C")
RESA_GREEN = HexColor("#5FA845")
COL_HEADER_BG = HexColor("#003366")
COL_HEADER_TEXT = white
ROW_ALT_1 = HexColor("#FFFFFF")
ROW_ALT_2 = HexColor("#EDF3F8")
GRID_LINE = HexColor("#8FAEC5")
FIELD_BG = HexColor("#FFFDE8")
LEGEND_EXTREME = HexColor("#D32F2F")
LEGEND_HIGH = HexColor("#F57C00")
LEGEND_MEDIUM = HexColor("#FBC02D")
LEGEND_LOW = HexColor("#4CAF50")
SECTION_BORDER = RESA_NAVY
LIGHT_GRAY = HexColor("#E0E0E0")
MED_GRAY = HexColor("#999999")
DARK_GRAY = HexColor("#444444")
RAC_COLORS = {"E": LEGEND_EXTREME, "H": LEGEND_HIGH,
              "M": LEGEND_MEDIUM, "L": LEGEND_LOW}


# =============================================================================
# PAGE DIMENSIONS
# =============================================================================
PAGE_W, PAGE_H = landscape(letter)
MARGIN = 20
CONTENT_W = PAGE_W - 2 * MARGIN
CONTENT_LEFT = MARGIN
CONTENT_RIGHT = PAGE_W - MARGIN

HEADER_H = 39
PROJ_INFO_H = 56
RISK_LEGEND_H = 43
GRID_HEADER_H = 22
FOOTER_H = 14
MIN_ROW_H = 34
SECTION_GAP = 3


# =============================================================================
# HELPERS
# =============================================================================
def set_font(c, name="Helvetica", size=8, color=black):
    c.setFont(name, size)
    c.setFillColor(color)

def draw_text_wrapped(c, text, x, y, max_width, font="Helvetica", size=7,
                      color=black, leading=9.5):
    set_font(c, font, size, color)
    lines = []
    for para in text.split("\n"):
        wrapped = simpleSplit(para, font, size, max_width)
        lines.extend(wrapped if wrapped else [""])
    cur_y = y
    for line in lines:
        c.drawString(x, cur_y, line)
        cur_y -= leading
    return cur_y

def text_height(text, max_width, font="Helvetica", size=7, leading=9.5):
    lines = []
    for para in text.split("\n"):
        wrapped = simpleSplit(para, font, size, max_width)
        lines.extend(wrapped if wrapped else [""])
    return len(lines) * leading

def add_text_field(c, name, x, y, w, h, font_size=7, multiline=False,
                   max_length=0, value="", indent=4):
    c.acroForm.textfield(
        name=name, x=x + indent, y=y, width=w - indent, height=h,
        fontSize=font_size, fontName="Helvetica",
        fillColor=FIELD_BG, borderColor=GRID_LINE, borderWidth=0.5,
        textColor=black,
        fieldFlags="multiline" if multiline else "",
        maxlen=max_length if max_length else 0,
        value=value, tooltip=name.replace("_", " "))

def add_rac_field(c, name, x, y, w, h, value=""):
    """RAC field — centered text, JS adds color in post-processing."""
    c.acroForm.textfield(
        name=name, x=x, y=y, width=w, height=h,
        fontSize=10, fontName="Helvetica-Bold",
        fillColor=FIELD_BG, borderColor=GRID_LINE, borderWidth=0.5,
        textColor=black, maxlen=1, value=value,
        tooltip="RAC: type E, H, M, or L")

def add_initials_field(c, name, x, y, w, h, value=""):
    """Initials field — italic font for a personal touch."""
    c.acroForm.textfield(
        name=name, x=x + 2, y=y, width=w - 2, height=h,
        fontSize=10, fontName="Times-Italic",
        fillColor=FIELD_BG, borderColor=GRID_LINE, borderWidth=0.5,
        textColor=DARK_GRAY, maxlen=4, value=value,
        tooltip="Initials")


# =============================================================================
# RAC JAVASCRIPT
# =============================================================================
RAC_FORMAT_JS = """
var v = event.value.toUpperCase();
var f = event.target;
if (v == "E") { f.fillColor = ["RGB",0.83,0.18,0.18]; f.textColor = color.white; }
else if (v == "H") { f.fillColor = ["RGB",0.96,0.49,0.0]; f.textColor = color.white; }
else if (v == "M") { f.fillColor = ["RGB",0.98,0.75,0.18]; f.textColor = color.black; }
else if (v == "L") { f.fillColor = ["RGB",0.30,0.69,0.31]; f.textColor = color.white; }
else { f.fillColor = ["RGB",1.0,0.99,0.91]; f.textColor = color.black; }
"""

RAC_KEYSTROKE_JS = """
event.change = event.change.toUpperCase();
"""

def postprocess_rac_js(pdf_path):
    """Post-process: inject RAC color JS + convert sig fields to digital signature."""
    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import (
        DictionaryObject, NameObject, NumberObject,
        ArrayObject, create_string_object
    )
    reader = PdfReader(pdf_path)
    writer = PdfWriter()
    writer.clone_document_from_reader(reader)

    fmt_action = DictionaryObject()
    fmt_action[NameObject("/S")] = NameObject("/JavaScript")
    fmt_action[NameObject("/JS")] = create_string_object(RAC_FORMAT_JS)

    key_action = DictionaryObject()
    key_action[NameObject("/S")] = NameObject("/JavaScript")
    key_action[NameObject("/JS")] = create_string_object(RAC_KEYSTROKE_JS)

    for page in writer.pages:
        if "/Annots" not in page:
            continue
        for annot_ref in page["/Annots"]:
            annot = annot_ref.get_object()
            name = str(annot.get("/T", ""))

            # RAC color-coding + center alignment
            if "rac_" in name or name.endswith("_c3") or name.endswith("_c4"):
                aa = DictionaryObject()
                aa[NameObject("/F")] = fmt_action
                aa[NameObject("/K")] = key_action
                annot[NameObject("/AA")] = aa
                # Center text: /Q = 1
                annot[NameObject("/Q")] = NumberObject(1)

            # Center initials fields too
            if "initials" in name or name.endswith("_c5"):
                annot[NameObject("/Q")] = NumberObject(1)

            # Convert sig_field_* text fields to digital signature fields
            if name.startswith("sig_field_"):
                annot[NameObject("/FT")] = NameObject("/Sig")
                # Remove text-field-specific keys
                for key in ["/MaxLen", "/V", "/DV"]:
                    if key in annot:
                        del annot[key]
                # Set SigFlags on AcroForm (1=SigsExist, 2=AppendOnly)
                if "/AcroForm" in writer._root_object:
                    acro = writer._root_object["/AcroForm"]
                    acro[NameObject("/SigFlags")] = NumberObject(3)

    with open(pdf_path, "wb") as f:
        writer.write(f)


# =============================================================================
# DRAWING COMPONENTS
# =============================================================================

def draw_header(c, y_top):
    h = 36
    y = y_top - h
    base_dir = os.path.dirname(os.path.abspath(__file__))

    c.setFillColor(white)
    c.rect(CONTENT_LEFT, y, CONTENT_W, h, fill=1, stroke=0)

    resa = os.path.join(base_dir, "resa-logo-90px.png")
    if os.path.exists(resa):
        lh = h - 8
        c.drawImage(resa, CONTENT_LEFT + 6, y + 4,
                    width=lh * (219.0/90.0), height=lh,
                    preserveAspectRatio=True, mask='auto')
    else:
        set_font(c, "Helvetica-Bold", 9, RESA_NAVY)
        c.drawString(CONTENT_LEFT + 8, y + h/2 - 3, "RESA POWER SERVICE")

    neta = os.path.join(base_dir, "neta-logo-90px.png")
    if os.path.exists(neta):
        nh = h - 8
        nw = nh * (162.0/90.0)
        c.drawImage(neta, CONTENT_RIGHT - nw - 6, y + 4,
                    width=nw, height=nh,
                    preserveAspectRatio=True, mask='auto')

    set_font(c, "Helvetica-Bold", 16, RESA_NAVY)
    c.drawCentredString(PAGE_W/2, y + h/2 - 5, "Activity Hazard Analysis")

    c.setStrokeColor(RESA_GREEN)
    c.setLineWidth(2.5)
    c.line(CONTENT_LEFT, y, CONTENT_RIGHT, y)
    return y - SECTION_GAP


def draw_project_info(c, y_top, activity_data=None):
    row_h = 13
    block_h = row_h * 4 + 2
    y = y_top - block_h
    c.setStrokeColor(SECTION_BORDER)
    c.setLineWidth(0.75)
    c.rect(CONTENT_LEFT, y, CONTENT_W, block_h, fill=0, stroke=1)

    aha_id = activity_data.get("aha_form_id", "") if activity_data else ""
    act_name = activity_data.get("activity_name", "") if activity_data else ""
    lw, fw, c2 = 115, 180, 310
    fields = [
        ("AHA Form:", "aha_form_id", 0, 0, aha_id),
        ("Activity / Work Task:", "activity_work_task", 0, 1, act_name),
        ("Activity Start Date:", "start_date", 0, 2, ""),
        ("Activity Duration:", "activity_duration", 0, 3, ""),
        ("Crew Leader:", "crew_leader", 1, 0, ""),
        ("Job Number:", "job_number", 1, 1, ""),
        ("Activity Location(s):", "activity_location", 1, 2, ""),
        ("Prepared By:", "prepared_by", 1, 3, ""),
    ]
    for label, fname, col, row, val in fields:
        fx = CONTENT_LEFT + 4 + col * c2
        fy = y_top - (row + 1) * row_h + 3
        set_font(c, "Helvetica-Bold", 7, DARK_GRAY)
        c.drawString(fx, fy + 2, label)
        field_x = fx + lw
        ffw = fw if col == 0 else (CONTENT_W - c2 - lw - 8)
        if val:
            set_font(c, "Helvetica", 8, black)
            c.drawString(field_x + 2, fy + 2, val)
        else:
            add_text_field(c, fname, field_x, fy - 2, ffw, row_h - 2, font_size=8)
    return y - SECTION_GAP


def draw_risk_legend(c, y_top):
    h = 40
    y = y_top - h
    c.setStrokeColor(SECTION_BORDER)
    c.setLineWidth(0.5)
    c.rect(CONTENT_LEFT, y, CONTENT_W, h, fill=0, stroke=1)
    set_font(c, "Helvetica-Bold", 7, DARK_GRAY)
    c.drawString(CONTENT_LEFT + 4, y + h - 10, "Risk Assessment Code (RAC)")
    items = [
        ("E","Extreme",LEGEND_EXTREME,"Extreme risks \u2014 Stop work, notify supervision immediately"),
        ("H","High",LEGEND_HIGH,"High risks \u2014 Must be reduced before work continues"),
        ("M","Medium",LEGEND_MEDIUM,"Medium risks \u2014 If cannot be reduced to Low, document and get approval"),
        ("L","Low",LEGEND_LOW,"Low risks \u2014 Acceptable with standard controls in place"),
    ]
    ix, iy, cw = CONTENT_LEFT + 8, y + h - 24, CONTENT_W/2 - 10
    for i, (code, label, color, desc) in enumerate(items):
        cx, cy = ix + (i%2)*cw, iy - (i//2)*12
        c.setFillColor(color)
        c.rect(cx, cy-2, 12, 10, fill=1, stroke=0)
        set_font(c, "Helvetica-Bold", 7, white)
        c.drawCentredString(cx+6, cy, code)
        set_font(c, "Helvetica", 6.5, DARK_GRAY)
        c.drawString(cx+16, cy, f"{label}: {desc}")
    return y - SECTION_GAP


# =============================================================================
# TASK GRID
# =============================================================================
COL_DEFS = [
    ("Task Steps", 0.22), ("Hazards", 0.14),
    ("Actions to Eliminate or Minimize Hazards", 0.34),
    ("RAC\n(Normal)", 0.07), ("RAC\n(Actual)", 0.07), ("Initials", 0.07),
]
TOTAL_FRAC = sum(f for _, f in COL_DEFS)
ROW_NUM_W = CONTENT_W * (1.0 - TOTAL_FRAC)

def get_col_positions():
    positions = []
    cx = CONTENT_LEFT + ROW_NUM_W
    for label, frac in COL_DEFS:
        w = CONTENT_W * frac
        positions.append((cx, w, label))
        cx += w
    return positions

def calc_row_height(step, col_positions):
    h = MIN_ROW_H
    for ci, key in [(0,"step"),(1,"hazards"),(2,"mitigations")]:
        txt = step.get(key, "")
        th = text_height(txt, col_positions[ci][1] - 6, "Helvetica", 7, 9.5) + 12
        h = max(h, th)
    return h

def draw_grid_header(c, y_top, col_positions):
    h = GRID_HEADER_H
    y = y_top - h
    c.setFillColor(COL_HEADER_BG)
    c.rect(CONTENT_LEFT, y, ROW_NUM_W, h, fill=1, stroke=0)
    set_font(c, "Helvetica-Bold", 6, COL_HEADER_TEXT)
    c.drawCentredString(CONTENT_LEFT + ROW_NUM_W/2, y + h/2 - 3, "#")
    for cx, cw, label in col_positions:
        c.setFillColor(COL_HEADER_BG)
        c.rect(cx, y, cw, h, fill=1, stroke=0)
        lines = label.split("\n")
        set_font(c, "Helvetica-Bold", 6.5, COL_HEADER_TEXT)
        if len(lines) == 1:
            c.drawCentredString(cx+cw/2, y+h/2-3, lines[0])
        else:
            for li, ln in enumerate(lines):
                c.drawCentredString(cx+cw/2, y+h/2+3-li*9, ln)
    c.setStrokeColor(white)
    c.setLineWidth(0.5)
    for cx, _, _ in col_positions:
        c.line(cx, y, cx, y+h)
    return y

def draw_task_row(c, ri, step, rh, cur_y, col_positions, is_blank=False):
    bg = ROW_ALT_1 if ri % 2 == 0 else ROW_ALT_2
    c.setFillColor(bg)
    c.rect(CONTENT_LEFT, cur_y, CONTENT_W, rh, fill=1, stroke=0)
    set_font(c, "Helvetica", 6.5, MED_GRAY)
    c.drawCentredString(CONTENT_LEFT + ROW_NUM_W/2, cur_y + rh/2 - 2, str(ri+1))

    # Field geometry (shared by RAC Normal + Actual for visual balance)
    rac_x_pad, rac_y_pad = 3, 4
    rac_w = col_positions[3][1] - rac_x_pad * 2
    rac_h = rh - rac_y_pad * 2

    if not is_blank and step:
        # Text columns (indented via add_text_field default)
        draw_text_wrapped(c, step["step"], col_positions[0][0]+6, cur_y+rh-8,
                          col_positions[0][1]-10, "Helvetica", 7, DARK_GRAY, 9.5)
        draw_text_wrapped(c, step["hazards"], col_positions[1][0]+6, cur_y+rh-8,
                          col_positions[1][1]-10, "Helvetica", 7, DARK_GRAY, 9.5)
        draw_text_wrapped(c, step["mitigations"], col_positions[2][0]+6, cur_y+rh-8,
                          col_positions[2][1]-10, "Helvetica", 7, DARK_GRAY, 9.5)

        # RAC Normal — field-sized badge (matches Actual column dimensions)
        rac_n = step.get("rac_normal", "")
        if rac_n:
            rc = RAC_COLORS.get(rac_n, MED_GRAY)
            nx = col_positions[3][0] + rac_x_pad
            ny = cur_y + rac_y_pad
            c.setFillColor(rc)
            c.roundRect(nx, ny, rac_w, rac_h, 2, fill=1, stroke=0)
            # Thin border to match field appearance
            c.setStrokeColor(GRID_LINE)
            c.setLineWidth(0.5)
            c.roundRect(nx, ny, rac_w, rac_h, 2, fill=0, stroke=1)
            set_font(c, "Helvetica-Bold", 10, white)
            c.drawCentredString(nx + rac_w/2, ny + rac_h/2 - 3.5, rac_n)

        # RAC Actual (fillable, same dimensions)
        add_rac_field(c, f"rac_actual_{ri}",
                      col_positions[4][0] + rac_x_pad, cur_y + rac_y_pad,
                      rac_w, rac_h)

        # Initials (cursive-style)
        add_initials_field(c, f"initials_{ri}",
                           col_positions[5][0] + rac_x_pad, cur_y + rac_y_pad,
                           col_positions[5][1] - rac_x_pad*2, rac_h)
    else:
        # Blank row — all cells fillable
        for ci, (cx, cw, _) in enumerate(col_positions):
            if ci in (3, 4):
                add_rac_field(c, f"task_r{ri}_c{ci}",
                              cx + rac_x_pad, cur_y + rac_y_pad, rac_w, rac_h)
            elif ci == 5:
                add_initials_field(c, f"task_r{ri}_c{ci}",
                                   cx + rac_x_pad, cur_y + rac_y_pad,
                                   cw - rac_x_pad*2, rac_h)
            else:
                add_text_field(c, f"task_r{ri}_c{ci}", cx+3, cur_y+4, cw-6, rh-8,
                               font_size=7, multiline=True)

    c.setStrokeColor(GRID_LINE)
    c.setLineWidth(0.3)
    c.line(CONTENT_LEFT, cur_y, CONTENT_RIGHT, cur_y)
    for cx, _, _ in col_positions:
        c.line(cx, cur_y, cx, cur_y+rh)


# =============================================================================
# CLOSING SECTIONS
# =============================================================================
def calc_closing_height(activity_data):
    qual = activity_data.get("qualification") if activity_data else None
    qual_rows = 3 if qual else 2
    note_h = 18 if qual and qual.get("note") else 0
    qual_h = 13 + qual_rows * 14 + note_h + SECTION_GAP
    crew_rows = 5
    if activity_data and "crew_rows" in activity_data:
        crew_rows = activity_data["crew_rows"]
    signoff_h = 13 + 13 + crew_rows * 20 + SECTION_GAP
    return 12 + qual_h + signoff_h  # 12 for continuation note

def draw_qualification_table(c, y_top, activity_data=None):
    qual = activity_data.get("qualification") if activity_data else None
    row_h = 14
    rows = 3 if qual else 2
    note_h = 18 if qual and qual.get("note") else 0
    block_h = 13 + rows * row_h + note_h
    y = y_top - block_h
    c.setFillColor(COL_HEADER_BG)
    c.rect(CONTENT_LEFT, y+block_h-13, CONTENT_W, 13, fill=1, stroke=0)
    set_font(c, "Helvetica-Bold", 7, COL_HEADER_TEXT)
    c.drawString(CONTENT_LEFT+4, y+block_h-10, "ACTIVITY QUALIFICATION REQUIREMENTS")
    label_w = 120
    ch_y = y + block_h - 13 - row_h
    c.setFillColor(ROW_ALT_2)
    c.rect(CONTENT_LEFT, ch_y, CONTENT_W, row_h, fill=1, stroke=0)
    set_font(c, "Helvetica-Bold", 7, DARK_GRAY)
    c.drawString(CONTENT_LEFT+4, ch_y+4, "Role")
    c.drawString(CONTENT_LEFT+label_w, ch_y+4, "Required Training / Certification")
    if qual:
        ry = ch_y - row_h
        set_font(c, "Helvetica-Bold", 7, DARK_GRAY)
        c.drawString(CONTENT_LEFT+4, ry+4, "Crew Leader")
        set_font(c, "Helvetica", 6.5, DARK_GRAY)
        c.drawString(CONTENT_LEFT+label_w, ry+4, qual["crew_leader"])
        ry -= row_h
        c.setFillColor(ROW_ALT_2)
        c.rect(CONTENT_LEFT, ry, CONTENT_W, row_h, fill=1, stroke=0)
        set_font(c, "Helvetica-Bold", 7, DARK_GRAY)
        c.drawString(CONTENT_LEFT+4, ry+4, "Crew Member")
        set_font(c, "Helvetica", 6.5, DARK_GRAY)
        c.drawString(CONTENT_LEFT+label_w, ry+4, qual["crew_member"])
        if qual.get("note"):
            ny = ry - note_h
            draw_text_wrapped(c, "Note: "+qual["note"], CONTENT_LEFT+4, ny+note_h-4,
                              CONTENT_W-8, "Helvetica-Oblique", 6, MED_GRAY, 8)
    else:
        for ri in range(2):
            ry = ch_y - (ri+1)*row_h
            if ri % 2 == 1:
                c.setFillColor(ROW_ALT_2)
                c.rect(CONTENT_LEFT, ry, CONTENT_W, row_h, fill=1, stroke=0)
            add_text_field(c, f"qual_role_{ri}", CONTENT_LEFT+2, ry+2,
                           label_w-4, row_h-4, font_size=7)
            add_text_field(c, f"qual_training_{ri}", CONTENT_LEFT+label_w, ry+2,
                           CONTENT_W-label_w-4, row_h-4, font_size=7)
    c.setStrokeColor(SECTION_BORDER)
    c.setLineWidth(0.75)
    c.rect(CONTENT_LEFT, y, CONTENT_W, block_h, fill=0, stroke=1)
    return y - SECTION_GAP

def draw_signoff_table(c, y_top, activity_data=None):
    days = ["SUN","MON","TUE","WED","THU","FRI","SAT"]
    crew_rows = 5
    if activity_data and "crew_rows" in activity_data:
        crew_rows = activity_data["crew_rows"]
    tech_w = 105       # widened from 65
    sig_w = 80         # slightly narrower to compensate
    day_w = (CONTENT_W - tech_w - sig_w) / len(days)
    hdr_h, sub_h, row_h = 13, 13, 20   # taller rows for signature comfort
    block_h = hdr_h + sub_h + crew_rows * row_h
    y = y_top - block_h
    c.setFillColor(COL_HEADER_BG)
    c.rect(CONTENT_LEFT, y+block_h-hdr_h, CONTENT_W, hdr_h, fill=1, stroke=0)
    set_font(c, "Helvetica-Bold", 7, COL_HEADER_TEXT)
    c.drawCentredString(PAGE_W/2, y+block_h-hdr_h+3,
        "CREW SIGN-OFF \u2014 Initial each day the activity is OPEN and AHA is reviewed")
    shy = y + block_h - hdr_h - sub_h
    c.setFillColor(ROW_ALT_2)
    c.rect(CONTENT_LEFT, shy, CONTENT_W, sub_h, fill=1, stroke=0)
    set_font(c, "Helvetica-Bold", 6.5, DARK_GRAY)
    c.drawCentredString(CONTENT_LEFT + tech_w/2, shy+3, "Field Technician")
    c.drawCentredString(CONTENT_LEFT + tech_w + sig_w/2, shy+3, "Signature")
    cx = CONTENT_LEFT + tech_w + sig_w
    for day in days:
        c.drawCentredString(cx + day_w/2, shy+3, day)
        cx += day_w
    for ri in range(crew_rows):
        ry = shy - (ri+1)*row_h
        bg = ROW_ALT_1 if ri%2==0 else ROW_ALT_2
        c.setFillColor(bg)
        c.rect(CONTENT_LEFT, ry, CONTENT_W, row_h, fill=1, stroke=0)
        # Technician name field
        add_text_field(c, f"tech_name_{ri}", CONTENT_LEFT+2, ry+2,
                       tech_w-4, row_h-4, font_size=8)
        # Digital signature field (placeholder — pypdf post-processing converts to /Sig)
        add_text_field(c, f"sig_field_{ri}", CONTENT_LEFT+tech_w+2, ry+2,
                       sig_w-4, row_h-4, font_size=7)
        # Day initials
        cx = CONTENT_LEFT + tech_w + sig_w
        for di, day in enumerate(days):
            add_text_field(c, f"day_{ri}_{day}", cx+2, ry+2, day_w-4, row_h-4, font_size=7)
            cx += day_w
        c.setStrokeColor(GRID_LINE)
        c.setLineWidth(0.3)
        c.line(CONTENT_LEFT, ry, CONTENT_RIGHT, ry)
    c.setStrokeColor(GRID_LINE)
    c.setLineWidth(0.3)
    for vx in [CONTENT_LEFT+tech_w, CONTENT_LEFT+tech_w+sig_w]:
        c.line(vx, y, vx, y+block_h-hdr_h)
    cx = CONTENT_LEFT + tech_w + sig_w
    for day in days:
        c.line(cx, y, cx, y+block_h-hdr_h)
        cx += day_w
    c.setStrokeColor(SECTION_BORDER)
    c.setLineWidth(0.75)
    c.rect(CONTENT_LEFT, y, CONTENT_W, block_h, fill=0, stroke=1)
    return y - SECTION_GAP

def draw_footer(c, activity_name="", page_num=1, total_pages=1):
    set_font(c, "Helvetica", 5.5, MED_GRAY)
    label = f"AHA \u2014 {activity_name}" if activity_name else "AHA \u2014 Blank Master Template"
    c.drawString(CONTENT_LEFT, MARGIN-2, label)
    c.drawCentredString(PAGE_W/2, MARGIN-2, f"Page {page_num} of {total_pages}")
    c.drawRightString(CONTENT_RIGHT, MARGIN-2, "RESA Power Service")
    c.setStrokeColor(LIGHT_GRAY)
    c.setLineWidth(0.5)
    c.line(CONTENT_LEFT, MARGIN+4, CONTENT_RIGHT, MARGIN+4)


# =============================================================================
# MAIN GENERATOR — Multi-page flow
# =============================================================================
def build_filename(activity_data):
    """Build standardized filename from activity data.
    
    Pattern: {DocType}-{Client}-{Project}-{Location}-{Activity}.pdf
    Example: AHA-CW-BDC-Mech_A_SWBD-Load_Monitor_Installation.pdf
    
    Falls back to just AHA-{Activity}.pdf if filename_parts not provided.
    """
    activity = activity_data["activity_name"].replace(" ", "_")
    parts = activity_data.get("filename_parts")
    
    if parts:
        segments = ["AHA"]
        for key in ("client", "project", "location"):
            val = parts.get(key, "").strip()
            if val:
                segments.append(val)
        segments.append(activity)
        return "-".join(segments) + ".pdf"
    else:
        return f"AHA-{activity}.pdf"


def generate_aha(activity_data=None, output_path=None):
    if output_path is None:
        if activity_data:
            output_path = os.path.join(ARTIFACTS_DIR, build_filename(activity_data))
        else:
            output_path = os.path.join(ARTIFACTS_DIR, "AHA-Blank-Master.pdf")

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    col_positions = get_col_positions()
    task_steps = activity_data["task_steps"] if activity_data else None
    activity_name = activity_data["activity_name"] if activity_data else ""
    blank_rows = 0 if task_steps else 14

    rows_data = task_steps or []
    total_rows = max(len(rows_data), blank_rows)
    row_heights = []
    for ri in range(total_rows):
        if ri < len(rows_data):
            row_heights.append(calc_row_height(rows_data[ri], col_positions))
        else:
            row_heights.append(MIN_ROW_H)

    closing_h = calc_closing_height(activity_data)

    # Page 1 available grid space
    p1_avail = (PAGE_H - MARGIN - HEADER_H - PROJ_INFO_H - RISK_LEGEND_H
                - GRID_HEADER_H - FOOTER_H - MARGIN)
    # Continuation page available grid space
    cont_avail = PAGE_H - MARGIN - HEADER_H - GRID_HEADER_H - FOOTER_H - MARGIN

    # Plan page breaks
    pages = []
    ri = 0
    page_num = 0
    while ri < total_rows:
        page_num += 1
        avail = p1_avail if page_num == 1 else cont_avail
        remaining_h = sum(row_heights[ri:])

        # Can all remaining rows + closing fit on this page?
        if remaining_h + closing_h <= avail:
            grid_space = avail - closing_h
        else:
            grid_space = avail

        start_ri = ri
        used = 0
        while ri < total_rows and used + row_heights[ri] <= grid_space + 0.5:
            used += row_heights[ri]
            ri += 1
        if ri == start_ri and ri < total_rows:
            ri += 1

        all_rows_placed = (ri >= total_rows)

        # Check: if all rows are placed, is there actually room for closing?
        if all_rows_placed and (avail - used) >= closing_h:
            is_last = True
        elif all_rows_placed:
            # All rows placed but no room for closing — closing goes on next page
            is_last = False
        else:
            is_last = False

        pages.append((start_ri, ri, is_last))

    # If closing still needs a page (no page marked as last)
    if pages and not any(p[2] for p in pages):
        pages.append((total_rows, total_rows, True))  # empty grid, just closing

    total_pages = len(pages)

    # Draw
    c = canvas.Canvas(output_path, pagesize=landscape(letter))
    c.setTitle("Activity Hazard Analysis")
    c.setAuthor("RESA Power Service")
    c.setSubject(activity_name or "Blank AHA Template")

    for page_idx, (start_ri, end_ri, is_last) in enumerate(pages):
        if page_idx > 0:
            c.showPage()
        y = PAGE_H - MARGIN
        y = draw_header(c, y)
        if page_idx == 0:
            y = draw_project_info(c, y, activity_data)
            y = draw_risk_legend(c, y)

        has_grid_rows = (start_ri < end_ri)

        if has_grid_rows:
            grid_top = y
            y = draw_grid_header(c, y, col_positions)
            cur_y = y
            for ri in range(start_ri, end_ri):
                rh = row_heights[ri]
                cur_y -= rh
                step = rows_data[ri] if ri < len(rows_data) else None
                draw_task_row(c, ri, step, rh, cur_y, col_positions, is_blank=(step is None))
            # Grid border
            c.setStrokeColor(SECTION_BORDER)
            c.setLineWidth(0.75)
            c.rect(CONTENT_LEFT, cur_y, CONTENT_W, grid_top - cur_y, fill=0, stroke=1)
            # Continuation note
            set_font(c, "Helvetica-Oblique", 6, MED_GRAY)
            if not is_last:
                c.drawString(CONTENT_LEFT + 4, cur_y - 8, "Continued on next page...")
            else:
                c.drawString(CONTENT_LEFT + 4, cur_y - 8,
                             "Add sheet listing additional tasks if necessary.")
            close_start = cur_y - 14
        else:
            close_start = y - SECTION_GAP

        if is_last:
            close_y = close_start
            close_y = draw_qualification_table(c, close_y, activity_data)
            close_y = draw_signoff_table(c, close_y, activity_data)

        draw_footer(c, activity_name, page_idx + 1, total_pages)

    c.save()
    postprocess_rac_js(output_path)
    return output_path


# =============================================================================
# CLI
# =============================================================================
def main():
    parser = argparse.ArgumentParser(description="Generate AHA PDFs")
    parser.add_argument("--activity", "-a", default=None)
    parser.add_argument("--output", "-o", default=None)
    args = parser.parse_args()
    activity_data = None
    if args.activity:
        try:
            mod = importlib.import_module(
                f"apex_forms_engine.aha.aha_data.{args.activity}"
            )
            activity_data = mod.ACTIVITY
            print(f"Loaded activity: {activity_data['activity_name']}")
        except ImportError as e:
            print(f"Error loading 'apex_forms_engine.aha.aha_data.{args.activity}': {e}")
            sys.exit(1)
    path = generate_aha(activity_data, args.output)
    print(f"Generated: {path}")

if __name__ == "__main__":
    main()
