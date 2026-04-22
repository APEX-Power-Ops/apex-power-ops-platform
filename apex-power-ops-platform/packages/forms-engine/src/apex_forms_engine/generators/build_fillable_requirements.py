"""
PSS Data Requirements Form — Fillable PDF Generator
Matches Figma layout: NmhCsWXDaSSyaMWcKpK2bq
Three checkbox columns: Req'd / Rec'd / Appr'd

Usage: cd to NETA-Forms/DataCollection/ and run:
    python build_fillable_requirements.py

Requires: pip install reportlab pypdf
"""
import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import HexColor, white, black, Color
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

# ── Brand colors ──
NAVY = HexColor("#002B5C")
BLUE = HexColor("#025687")
GREEN = HexColor("#5FA845")
DK = HexColor("#333333")
MD = HexColor("#666666")
LT_GRAY = HexColor("#F0F0F0")
CREAM = HexColor("#FFFDE8")
FB = HexColor("#8FAEC5")       # field border
SBG = HexColor("#003366")      # section bar
ROW_ALT = HexColor("#F7F9FC")  # alternating row tint

W, H = letter  # 612 x 792
ML = 50   # margin left
MR = 50   # margin right
CW = W - ML - MR  # 512

# Package-local paths
_HERE = os.path.dirname(os.path.abspath(__file__))
_PACKAGE_ROOT = os.path.dirname(_HERE)
NETA_LOGO = os.path.join(_PACKAGE_ROOT, "assets", "international-electrical-testing-association-neta-logo-vector.png")
RESA_LOGO = os.path.join(_PACKAGE_ROOT, "assets", "RESA-Service-Stack PNG.png")
OUTPUT = os.path.join(_PACKAGE_ROOT, "artifacts", "PSS_Data_Requirements_Fillable.pdf")

# ── Logo sizing — 0.50" tall (36pt), aspect-ratio preserved ──
LOGO_H = 36
NETA_W = 65   # 900x500px → aspect 1.80
RESA_W = 88   # 438x180px → aspect 2.43

def fy(figma_y):
    return H - figma_y

def draw_header(c):
    line_y = fy(80)
    logo_pdf_y = line_y + 6
    if os.path.exists(NETA_LOGO):
        c.drawImage(ImageReader(NETA_LOGO), ML, logo_pdf_y,
                     width=NETA_W, height=LOGO_H, mask='auto', preserveAspectRatio=True)
    else:
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(NAVY)
        c.drawString(ML, logo_pdf_y + 10, "NETA")

    if os.path.exists(RESA_LOGO):
        c.drawImage(ImageReader(RESA_LOGO), W - MR - RESA_W, logo_pdf_y,
                     width=RESA_W, height=LOGO_H, mask='auto', preserveAspectRatio=True)
    else:
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(BLUE)
        c.drawRightString(W - MR, logo_pdf_y + 10, "RESA Power Service")

    c.setStrokeColor(BLUE); c.setLineWidth(2); c.line(ML, line_y, W - MR, line_y)
    tag_y = fy(96)
    c.setFont("Helvetica-BoldOblique", 8); c.setFillColor(GREEN)
    c.drawString(ML, tag_y, "Reliable and Safe.")
    tw = c.stringWidth("Reliable and Safe.", "Helvetica-BoldOblique", 8)
    c.setFillColor(BLUE); c.drawString(ML + tw + 3, tag_y, "The Power of Us.")
    c.setFont("Helvetica", 8); c.setFillColor(MD)
    c.drawRightString(W - MR, tag_y, "2447 W 12th St. Suite 5 \u00b7 Tempe, AZ 85281")

def draw_footer(c, page_num, total=2):
    h = 18; gw = 120
    c.setFillColor(GREEN); c.rect(0, 0, gw, h, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 7); c.setFillColor(white); c.drawString(14, 5, "resapower.com")
    c.setFillColor(NAVY); c.rect(gw, 0, W - gw, h, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 7); c.setFillColor(white)
    c.drawCentredString(W / 2, 5, "NETA Accredited Company")
    c.setFont("Helvetica", 6.5)
    c.drawRightString(W - 14, 5, f"RESA Power Phoenix Services  \u00b7  480.730.8871    Page {page_num} of {total}")

def section_bar(c, figma_y, text, height=18):
    pdf_y = fy(figma_y + height)
    c.setFillColor(SBG); c.roundRect(ML, pdf_y, CW, height, 2, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 8.5); c.setFillColor(white); c.drawString(ML + 8, pdf_y + 5, text)

def text_field(c, name, figma_x, figma_y, w, h, font_size=9):
    INDENT = 5
    pdf_y = fy(figma_y + h)
    c.setFillColor(CREAM); c.rect(figma_x, pdf_y, w, h, fill=1, stroke=0)
    c.setStrokeColor(FB); c.setLineWidth(0.5); c.rect(figma_x, pdf_y, w, h, fill=0, stroke=1)
    c.acroForm.textfield(name=name, x=figma_x + INDENT, y=pdf_y + 1,
        width=w - INDENT - 2, height=h - 2, fontSize=font_size,
        borderWidth=0, fillColor=CREAM, textColor=black, fontName="Helvetica")

def checkbox_field(c, name, figma_x, figma_y, size=8):
    pdf_y = fy(figma_y + size)
    c.setStrokeColor(FB); c.setLineWidth(0.5); c.setFillColor(white)
    c.rect(figma_x, pdf_y, size, size, fill=1, stroke=1)
    c.acroForm.checkbox(name=name, x=figma_x, y=pdf_y, size=size,
        borderWidth=0.5, borderColor=FB, fillColor=white, buttonStyle="check", checked=False)

def label(c, text, figma_x, figma_y, font="Helvetica", size=8, color=None):
    c.setFont(font, size); c.setFillColor(color or DK)
    c.drawString(figma_x, fy(figma_y + size * 0.85), text)

def h_line(c, figma_y, x1=ML, x2=None):
    if x2 is None: x2 = W - MR
    c.setStrokeColor(HexColor("#E0E0E0")); c.setLineWidth(0.3); c.line(x1, fy(figma_y), x2, fy(figma_y))

def alt_row_bg(c, figma_y, height):
    c.setFillColor(ROW_ALT); c.rect(ML, fy(figma_y + height), CW, height, fill=1, stroke=0)

def draw_category_row(c, idx, figma_y, row_h, title, detail, page_prefix, has_alt_bg=False):
    if has_alt_bg: alt_row_bg(c, figma_y, row_h)
    label(c, title, ML + 5, figma_y + 2, "Helvetica-Bold", 8.5, DK)
    if detail:
        max_w = 258; words = detail.split(); line = ""; dy = figma_y + 14
        c.setFont("Helvetica", 7); c.setFillColor(MD)
        for word in words:
            test = line + " " + word if line else word
            if c.stringWidth(test, "Helvetica", 7) > max_w:
                c.drawString(ML + 14, fy(dy + 7 * 0.85), line); dy += 9; line = word
            else: line = test
        if line: c.drawString(ML + 14, fy(dy + 7 * 0.85), line)
    cb_y = figma_y + 6; cb_prefix = f"{page_prefix}_row{idx}"
    checkbox_field(c, f"{cb_prefix}_reqd", 320, cb_y)
    checkbox_field(c, f"{cb_prefix}_recd", 354, cb_y)
    checkbox_field(c, f"{cb_prefix}_apprd", 388, cb_y)
    text_field(c, f"{cb_prefix}_notes", 414, figma_y + 3, 148, row_h - 6, font_size=7)
    h_line(c, figma_y + row_h)

# ── Category data ──
NEW_CONSTRUCTION = [
    ("Electrical single-line diagrams", "As-built or updated to current config. Include voltage, ampere, and interrupting ratings."),
    ("Equipment submittals (switchgear, MCC, switchboards)", "Manufacturer cut sheets with frame, trip, sensor ratings, and AIC."),
    ("Panelboard schedules", "Main breaker data required. Branch circuit schedules not needed for study."),
    ("Transformer data", "kVA, primary/secondary voltage, %Z, X/R, winding connections (Delta / Wye / Wye-Gnd)."),
    ("Feeder & conductor information", "Sizes, Cu/Al, insulation, lengths, and conduit type (metal or PVC) for each run."),
    ("Utility fault current contribution letter", "3-phase and SLG fault current (kA) with X/R ratios. Request from utility if unavailable."),
    ("Generator / alternator submittals", "kW/kVA, voltage, Xd\", X/R ratio, RPM."),
    ("Protective relay information", "Mfr, model, CT ratio, settings (51P/50P/51N/50N) where applicable."),
    ("UPS / solar / battery storage system data", "kVA, input/output voltage, bypass configuration."),
    ("ATS submittals", "Normal source, emergency source, output, transfer type, amp rating, mfr/model."),
    ("Busway / bus plug information", "Manufacturer, ampacity, length, material (Cu/Al)."),
    ("Fuse information", "Type, size, and manufacturer for all fused devices."),
    ("Circuit breaker information", "Manufacturer, model, trip unit type."),
]

EXISTING_SYSTEMS = [
    ("Utility fault current data", "Fault current letter (3\u03a6 and SLG with X/R). Utility XFMR kVA, %Z, winding config."),
    ("Distribution system sketch / riser diagram", "Show all 3-phase equipment: source \u2192 protective device \u2192 load for every feeder."),
    ("Breaker data (panels, switchgear, disconnects)", "Manufacturer, model, frame, trip, AIC. Photograph every nameplate."),
    ("Breaker settings (adjustable trip units)", "LTPU, LTD, STPU, STD, I\u00b2t, INST, GFPU, GFD. Photo the trip unit display."),
    ("Feeder lengths & conductor sizes", "Measure or verify. Include # of sets, wire size, Cu/Al, insulation type."),
    ("Conduit type for each feeder run", "Metal (EMT/RGS/IMC) vs. PVC/tray/direct. Directly affects impedance calcs."),
    ("Transformer nameplate data", "kVA, voltage, %Z, X/R, winding connections (Delta / Wye / Wye-Gnd), dry/liquid."),
    ("Generator nameplate data", "kW/kVA, voltage, Xd\", X/R, RPM. Include alternator data sheet if available."),
    ("UPS system data", "kVA, input/output voltage, bypass config, battery runtime, output breaker."),
    ("ATS nameplate data", "Normal source, emergency source, output, amp rating, transfer type, mfr/model."),
    ("Protective relay settings", "Mfr, model, CT ratio. Record 51P/50P pickup, curve, TD, and 51N/50N settings."),
    ("Busway / bus plug data", "Manufacturer, ampacity, length, Cu/Al, bus plug information."),
    ("Fuse data (all fused devices)", "Type, size, mfr for disconnects, bus plugs, Pringles, combo starters."),
    ("Maintenance reports (if available)", "Recent breaker test reports, IR scan results, or other maintenance records."),
]

IMPORTANT_NOTES = [
    "Cable lengths are critical \u2014 estimates significantly impact arc flash results.",
    "Conduit type (metal vs. PVC) changes cable impedance \u2014 don\u2019t skip this.",
    "Confirm transformer winding connections on the nameplate \u2014 affects ground fault modeling.",
    "Photograph everything \u2014 nameplates, trip settings, relay faceplates, panel directories.",
    "Request the utility fault current letter early \u2014 utilities can take weeks to respond.",
]

def build_fillable_requirements(output_path=None):
    output_path = output_path or OUTPUT

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    c = canvas.Canvas(output_path, pagesize=letter)
    c.setTitle("Power System Study \u2014 Data Requirements")
    c.setAuthor("RESA Power Service")

    # === PAGE 1: NEW CONSTRUCTION ===
    draw_header(c)
    c.setFont("Helvetica-Bold", 14); c.setFillColor(NAVY)
    c.drawCentredString(W / 2, fy(126), "POWER SYSTEM STUDY \u2014 DATA REQUIREMENTS")
    c.setFont("Helvetica", 8); c.setFillColor(MD)
    c.drawCentredString(W / 2, fy(144), "Arc Flash Risk Assessment & Device Coordination Study per IEEE 1584-2018 / NFPA 70E-2024")

    for label_y, fields in [(156,[("Project Name",ML,249),("Project Number",313,249)]),
        (190,[("Client / Owner",ML,249),("Site Address",313,249)]),
        (224,[("Submitted To (Company)",ML,249),("Attention",313,249)]),
        (258,[("Submitted By",ML,249),("Date",313,249)])]:
        for fl, x, w in fields:
            label(c, fl, x, label_y, "Helvetica", 8, MD)
            text_field(c, f"p1_{fl.lower().replace(' ','_').replace('/','_').replace('(','').replace(')','')}", x, label_y+10, w, 16)

    label(c, "Study type:", ML, 294, "Helvetica-Bold", 9, DK)
    for sl, sx in [("New Construction",110),("Existing System",209),("System Modification",299)]:
        checkbox_field(c, f"p1_study_{sl.lower().replace(' ','_')}", sx, 294, 9)
        label(c, sl, sx+14, 294, "Helvetica", 9, DK)

    section_bar(c, 316, "NEW CONSTRUCTION \u2014 Submittals & Documentation Required")
    label(c, "Mark each item as Required, Received, or Approved. Use Notes for clarifications.", ML+5, 340, "Helvetica-Oblique", 7.5, MD)
    c.setFont("Helvetica-Bold", 6.5); c.setFillColor(MD); hdr_y = fy(362)
    c.drawCentredString(324, hdr_y, "Req'd"); c.drawCentredString(358, hdr_y, "Rec'd")
    c.drawCentredString(392, hdr_y, "Appr'd"); c.drawString(414, hdr_y, "Notes / clarification")
    c.setStrokeColor(FB); c.setLineWidth(0.5); c.line(ML, fy(364), W-MR, fy(364))

    row_y = 368; row_h = 30
    for i, (t, d) in enumerate(NEW_CONSTRUCTION):
        draw_category_row(c, i, row_y, row_h, t, d, "p1", i%2==0); row_y += row_h
    c.setStrokeColor(FB); c.setLineWidth(0.5); c.line(ML, fy(row_y+8), W-MR, fy(row_y+8))
    c.setFillColor(GREEN); c.circle(ML+8, fy(row_y+12), 2, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 7.5); c.setFillColor(DK)
    c.drawString(ML+15, fy(row_y+14), "Photograph all equipment nameplates, trip unit settings, relay faceplates, and panel directories.")
    draw_footer(c, 1); c.showPage()

    # === PAGE 2: EXISTING SYSTEMS ===
    draw_header(c)
    for fl, fx, fw in [("Project Name (from Page 1)",ML,164),("Project Number",224,164),("Date",398,164)]:
        label(c, fl, fx, 112, "Helvetica", 8, MD)
        text_field(c, f"p2_{fl.lower().replace(' ','_').replace('(','').replace(')','')}", fx, 122, fw, 15)
    section_bar(c, 150, "EXISTING SYSTEMS \u2014 Field Data Collection Requirements")
    label(c, "If as-built drawings are unavailable, collect the following in the field. Photograph all nameplates.", ML+5, 174, "Helvetica-Oblique", 7.5, MD)
    c.setFont("Helvetica-Bold", 6.5); c.setFillColor(MD); hdr_y = fy(196)
    c.drawCentredString(324, hdr_y, "Req'd"); c.drawCentredString(358, hdr_y, "Rec'd")
    c.drawCentredString(392, hdr_y, "Appr'd"); c.drawString(414, hdr_y, "Notes / clarification")
    c.setStrokeColor(FB); c.setLineWidth(0.5); c.line(ML, fy(198), W-MR, fy(198))

    row_y = 202; row_h = 28
    for i, (t, d) in enumerate(EXISTING_SYSTEMS):
        draw_category_row(c, i, row_y, row_h, t, d, "p2", i%2==0); row_y += row_h
    c.setFillColor(GREEN); c.circle(ML+8, fy(row_y+12), 2, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 7.5); c.setFillColor(DK)
    c.drawString(ML+15, fy(row_y+14), "Photograph all equipment nameplates, trip unit settings, relay faceplates, and panel directories.")

    notes_start = row_y + 24; section_bar(c, notes_start, "IMPORTANT NOTES"); bullet_y = notes_start + 26
    c.setFont("Helvetica", 7)
    for note in IMPORTANT_NOTES:
        c.setFillColor(GREEN); c.circle(ML+8, fy(bullet_y+1.5), 1.8, fill=1, stroke=0)
        c.setFillColor(DK); words = note.split(); line = ""; cur_y = bullet_y
        for word in words:
            test = line+" "+word if line else word
            if c.stringWidth(test,"Helvetica",7) > CW-18:
                c.drawString(ML+15, fy(cur_y+7*0.85), line); cur_y += 9; line = word
            else: line = test
        if line: c.drawString(ML+15, fy(cur_y+7*0.85), line)
        bullet_y = cur_y + 13

    sig_sep_y = bullet_y + 2; c.setStrokeColor(FB); c.setLineWidth(0.5); c.line(ML, fy(sig_sep_y), W-MR, fy(sig_sep_y))
    sig_y = sig_sep_y + 8
    label(c, "Received by:", ML, sig_y, "Helvetica-Bold", 7, MD)
    text_field(c, "p2_received_by", ML, sig_y+10, 246, 14)
    label(c, "Date received:", 316, sig_y, "Helvetica-Bold", 7, MD)
    text_field(c, "p2_date_received", 316, sig_y+10, 246, 14)
    draw_footer(c, 2); c.save()

    from pypdf import PdfReader

    print(f"Saved: {output_path}")
    print(f"Size: {os.path.getsize(output_path):,} bytes")
    reader = PdfReader(output_path)
    fields = reader.get_fields()

    print(f"Pages: {len(reader.pages)}")
    if fields:
        cb = sum(1 for f in fields.values() if f.get("/FT") == "/Btn")
        tf = sum(1 for f in fields.values() if f.get("/FT") == "/Tx")
        print(f"Form fields: {len(fields)} total ({cb} checkboxes, {tf} text fields)")

    return output_path


def main():
    build_fillable_requirements()


if __name__ == "__main__":
    main()
