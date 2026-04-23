# cv_generator.py
import os
import re
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, Iterable, List

from docxtpl import DocxTemplate
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.platypus import HRFlowable, Image as RLImage, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
OUTPUT_DIR = BASE_DIR / "output"
LOGO_CANDIDATES = [
    BASE_DIR / "assets" / "ntt_data_logo.png",
    BASE_DIR / "assets" / "NTT_Logo.png",
    BASE_DIR / "assets" / "ntt_logo.png",
    BASE_DIR / "assets" / "logo.png",
]


def _get_footer_logo():
    for logo_path in LOGO_CANDIDATES:
        if logo_path.exists():
            return ImageReader(str(logo_path))
    return None


def _draw_confidential_footer(canvas, doc):
    canvas.saveState()
    logo = _get_footer_logo()
    footer_y = 0.35 * inch
    if logo is not None:
        canvas.drawImage(
            logo,
            doc.leftMargin,
            footer_y - 0.08 * inch,
            width=0.9 * inch,
            height=0.26 * inch,
            preserveAspectRatio=True,
            mask="auto",
        )
    canvas.setFont("Helvetica-Bold", 9)
    canvas.setFillColor(colors.HexColor("#64748B"))
    canvas.drawCentredString(A4[0] / 2, footer_y, "NTT DATA CONFIDENTIAL")
    canvas.restoreState()


def _safe_filename(value: str, fallback: str = "candidate_cv") -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "_", (value or "").strip()).strip("_")
    return cleaned or fallback


def _flatten_education(education_items: Iterable[Any]) -> List[str]:
    rows = []
    for item in education_items or []:
        if isinstance(item, dict):
            values = [str(value).strip() for value in item.values() if str(value).strip()]
            if values:
                rows.append(" | ".join(values))
        elif str(item).strip():
            rows.append(str(item).strip())
    return rows


def _normalize_experience(experience_items: Iterable[Any]) -> List[Dict[str, Any]]:
    rows = []
    for item in experience_items or []:
        if not isinstance(item, dict):
            continue
        normalized = dict(item)
        responsibilities = item.get("responsibilities") or item.get("bullets") or []
        if isinstance(responsibilities, str):
            responsibilities = [responsibilities] if responsibilities.strip() else []
        normalized["responsibilities"] = [str(value).strip() for value in responsibilities if str(value).strip()]
        rows.append(normalized)
    return rows


def generate_docx(
    cv_data: Dict[str, Any],
    output_filename: str = "generated_cv.docx",
    template_id: str = "custom",
) -> str:
    """
    Fill the Word template placeholders and save a DOCX copy.
    """
    template_path = TEMPLATES_DIR / "cv_template_clean.docx"
    if not template_path.exists():
        template_path = TEMPLATES_DIR / "cv_template.docx"
    doc = DocxTemplate(str(template_path))

    context = {
        "objectives": cv_data.get("objectives", ""),
        "name": cv_data.get("name", ""),
        "title": cv_data.get("title", ""),
        "total_it_experience": cv_data.get("total_it_experience", ""),
        "contact": cv_data.get("contact", ""),
        "location": cv_data.get("location", ""),
        "summary": cv_data.get("summary", ""),
        "skills": cv_data.get("skills", []),
        "education": _flatten_education(cv_data.get("education", [])),
        "experience": _normalize_experience(cv_data.get("experience", [])),
        "certifications": cv_data.get("certifications", []),
        "achievements": cv_data.get("achievements", []),
        "template_id": template_id,
    }

    doc.render(context)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = OUTPUT_DIR / output_filename
    doc.save(str(out_path))
    return str(out_path)


def _build_common_pdf_styles():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="ResumeHeader",
            parent=styles["Title"],
            alignment=TA_CENTER,
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=26,
            textColor=colors.HexColor("#0F172A"),
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="ResumeSubheader",
            parent=styles["BodyText"],
            alignment=TA_CENTER,
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#475569"),
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SectionHeading",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#0F766E"),
            spaceBefore=12,
            spaceAfter=6,
            uppercase=True,
        )
    )
    styles.add(
        ParagraphStyle(
            name="RoleHeading",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#0F172A"),
            spaceAfter=2,
        )
    )
    styles.add(
        ParagraphStyle(
            name="MetaText",
            parent=styles["BodyText"],
            fontName="Helvetica-Oblique",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#64748B"),
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BulletText",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            leftIndent=12,
            bulletIndent=0,
            textColor=colors.HexColor("#1E293B"),
            spaceAfter=2,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CardHeader",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            textColor=colors.white,
            alignment=TA_LEFT,
        )
    )
    return styles


def _create_output_path(cv_data: Dict[str, Any], output_filename: str | None) -> str:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    candidate_name = cv_data.get("name", "")
    filename = output_filename or f"{_safe_filename(candidate_name)}.pdf"
    return str(OUTPUT_DIR / filename)


def _build_custom_story(cv_data: Dict[str, Any], styles):
    story = []
    name = cv_data.get("name") or "Candidate Name"
    title = cv_data.get("title") or "Professional Title"
    experience_text = cv_data.get("total_it_experience") or ""
    location = cv_data.get("location") or ""
    contact = cv_data.get("contact") or ""
    summary = (cv_data.get("summary") or "").strip()
    objectives = (cv_data.get("objectives") or "").strip()
    profile_photo_bytes = cv_data.get("profile_photo_bytes")

    subheader_parts = [part for part in [title, experience_text, location, contact] if part]

    if profile_photo_bytes:
        header_flowables = [Paragraph(name, styles["ResumeHeader"])]
        if subheader_parts:
            header_flowables.append(Paragraph(" | ".join(subheader_parts), styles["ResumeSubheader"]))

        photo = RLImage(BytesIO(profile_photo_bytes), width=1.1 * inch, height=1.35 * inch)
        photo.hAlign = "RIGHT"
        header_table = Table(
            [[header_flowables, photo]],
            colWidths=[5.65 * inch, 1.0 * inch],
            hAlign="LEFT",
        )
        header_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )
        story.append(header_table)
    else:
        story.append(Paragraph(name, styles["ResumeHeader"]))
        if subheader_parts:
            story.append(Paragraph(" | ".join(subheader_parts), styles["ResumeSubheader"]))

    story.append(HRFlowable(width="100%", thickness=1.2, color=colors.HexColor("#CBD5E1")))
    story.append(Spacer(1, 0.12 * inch))

    def add_section(title_text: str, body_items: List[Any]):
        if not body_items:
            return
        story.append(Paragraph(title_text, styles["SectionHeading"]))
        story.extend(body_items)

    if objectives:
        add_section("Career Objective", [Paragraph(objectives, styles["BodyText"])])

    summary_blocks = []
    if experience_text:
        summary_blocks.append(Paragraph(f"Total IT Experience: {experience_text}", styles["BodyText"]))
    if summary:
        summary_blocks.append(Paragraph(summary, styles["BodyText"]))
    add_section("Professional Summary", summary_blocks)

    skills = [str(skill).strip() for skill in cv_data.get("skills", []) if str(skill).strip()]
    if skills:
        add_section("Core Skills", [Paragraph(" | ".join(skills), styles["BodyText"])])

    experience_blocks = []
    for item in _normalize_experience(cv_data.get("experience", [])):
        role = item.get("role") or "Role"
        company = item.get("company") or "Company"
        start_date = item.get("start_date") or ""
        end_date = item.get("end_date") or "Present"

        experience_blocks.append(Paragraph(f"{role} | {company}", styles["RoleHeading"]))
        if start_date or end_date:
            experience_blocks.append(Paragraph(f"{start_date} - {end_date}".strip(" -"), styles["MetaText"]))
        for responsibility in item.get("responsibilities", []):
            experience_blocks.append(Paragraph(responsibility, styles["BulletText"], bulletText="-"))
        experience_blocks.append(Spacer(1, 0.04 * inch))
    add_section("Professional Experience", experience_blocks)

    education_rows = [Paragraph(item, styles["BodyText"]) for item in _flatten_education(cv_data.get("education", []))]
    add_section("Education", education_rows)

    certification_rows = [
        Paragraph(str(item).strip(), styles["BulletText"], bulletText="-")
        for item in cv_data.get("certifications", [])
        if str(item).strip()
    ]
    add_section("Certifications", certification_rows)

    achievement_rows = [
        Paragraph(str(item).strip(), styles["BulletText"], bulletText="-")
        for item in cv_data.get("achievements", [])
        if str(item).strip()
    ]
    add_section("Achievements", achievement_rows)
    return story


def _card(title: str, body: List[Any], width: float, accent_hex: str):
    header = Table(
        [[Paragraph(title, ParagraphStyle("CardHeaderInline", fontName="Helvetica-Bold", fontSize=11, textColor=colors.white))]],
        colWidths=[width],
    )
    header.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(accent_hex)),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    body_table = Table([[body]], colWidths=[width])
    body_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.whitesmoke),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#D6E3F0")),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return [header, body_table]


def _build_postcard_story(cv_data: Dict[str, Any], styles):
    name = cv_data.get("name") or "Candidate Name"
    title = cv_data.get("title") or "Professional Title"
    summary = (cv_data.get("summary") or "").strip() or "Summary pending."
    skills = [str(skill).strip() for skill in cv_data.get("skills", []) if str(skill).strip()]
    certifications = [str(item).strip() for item in cv_data.get("certifications", []) if str(item).strip()]
    achievements = [str(item).strip() for item in cv_data.get("achievements", []) if str(item).strip()]
    education = _flatten_education(cv_data.get("education", []))
    experience = _normalize_experience(cv_data.get("experience", []))

    hero = Table(
        [[
            Paragraph(
                f"<font size='22'><b>{name}</b></font><br/><font size='11'>{title}</font><br/><font size='10'>{cv_data.get('total_it_experience') or ''}</font>",
                ParagraphStyle("PostcardHero", fontName="Helvetica", fontSize=11, leading=14, textColor=colors.white),
            )
        ]],
        colWidths=[7.0 * inch],
    )
    hero.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#0E1A3B")),
                ("LEFTPADDING", (0, 0), (-1, -1), 18),
                ("RIGHTPADDING", (0, 0), (-1, -1), 18),
                ("TOPPADDING", (0, 0), (-1, -1), 18),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 18),
            ]
        )
    )

    left_body = [Paragraph(summary, styles["BodyText"])]
    if skills:
        left_body.append(Spacer(1, 0.08 * inch))
        left_body.append(Paragraph(" | ".join(skills), styles["BodyText"]))
    right_body = []
    for row in certifications or ["No certifications listed"]:
        right_body.append(Paragraph(row, styles["BulletText"], bulletText="-"))
    if achievements:
        right_body.append(Spacer(1, 0.08 * inch))
        for row in achievements:
            right_body.append(Paragraph(row, styles["BulletText"], bulletText="-"))

    cards = [
        hero,
        Spacer(1, 0.16 * inch),
    ]
    left_card = _card("Profile Snapshot", left_body, 3.35 * inch, "#1479C9")
    right_card = _card("Certifications & Wins", right_body, 3.35 * inch, "#0E1A3B")
    cards.append(Table([[left_card, right_card]], colWidths=[3.45 * inch, 3.45 * inch]))
    cards.append(Spacer(1, 0.14 * inch))

    experience_rows: List[Any] = []
    for item in experience:
        role = item.get("role") or "Role"
        company = item.get("company") or "Company"
        experience_rows.append(Paragraph(f"<b>{role}</b> | {company}", styles["BodyText"]))
        for bullet in item.get("responsibilities", [])[:3]:
            experience_rows.append(Paragraph(bullet, styles["BulletText"], bulletText="-"))
        experience_rows.append(Spacer(1, 0.05 * inch))
    if not experience_rows:
        experience_rows.append(Paragraph("Experience will appear here.", styles["BodyText"]))

    education_rows = [Paragraph(item, styles["BodyText"]) for item in education] or [Paragraph("Education pending.", styles["BodyText"])]
    bottom_left = _card("Experience Highlights", experience_rows, 4.55 * inch, "#18A0AE")
    bottom_right = _card("Education", education_rows, 2.15 * inch, "#1479C9")
    cards.append(Table([[bottom_left, bottom_right]], colWidths=[4.65 * inch, 2.25 * inch]))
    return cards


def _build_sample_story(cv_data: Dict[str, Any], styles):
    story: List[Any] = []
    name = cv_data.get("name") or "Candidate Name"
    title = cv_data.get("title") or "Professional Title"
    meta_parts = [part for part in [cv_data.get("location"), cv_data.get("contact"), cv_data.get("total_it_experience")] if part]
    story.append(Paragraph(name, ParagraphStyle("SampleName", fontName="Helvetica-Bold", fontSize=24, textColor=colors.HexColor("#102542"), spaceAfter=4)))
    story.append(Paragraph(title, ParagraphStyle("SampleTitle", fontName="Helvetica", fontSize=12, textColor=colors.HexColor("#1479C9"), spaceAfter=5)))
    if meta_parts:
        story.append(Paragraph(" | ".join(meta_parts), styles["MetaText"]))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#1479C9")))
    story.append(Spacer(1, 0.12 * inch))

    summary = (cv_data.get("summary") or "").strip()
    if summary:
        story.append(Paragraph("Summary", styles["SectionHeading"]))
        story.append(Paragraph(summary, styles["BodyText"]))

    skills = [str(skill).strip() for skill in cv_data.get("skills", []) if str(skill).strip()]
    if skills:
        story.append(Paragraph("Skills", styles["SectionHeading"]))
        story.append(Paragraph("  •  ".join(skills), styles["BodyText"]))

    story.append(Paragraph("Experience", styles["SectionHeading"]))
    experience = _normalize_experience(cv_data.get("experience", []))
    if experience:
        for item in experience:
            role = item.get("role") or "Role"
            company = item.get("company") or "Company"
            dates = " - ".join(filter(None, [item.get("start_date"), item.get("end_date")]))
            story.append(Paragraph(f"<b>{role}</b> at {company}", styles["BodyText"]))
            if dates:
                story.append(Paragraph(dates, styles["MetaText"]))
            for bullet in item.get("responsibilities", []):
                story.append(Paragraph(bullet, styles["BulletText"], bulletText="-"))
            story.append(Spacer(1, 0.05 * inch))
    else:
        story.append(Paragraph("Experience pending.", styles["BodyText"]))

    education = _flatten_education(cv_data.get("education", []))
    if education:
        story.append(Paragraph("Education", styles["SectionHeading"]))
        for item in education:
            story.append(Paragraph(item, styles["BodyText"]))

    certifications = [str(item).strip() for item in cv_data.get("certifications", []) if str(item).strip()]
    if certifications:
        story.append(Paragraph("Certifications", styles["SectionHeading"]))
        for item in certifications:
            story.append(Paragraph(item, styles["BulletText"], bulletText="-"))

    return story


def generate_pdf(cv_data: Dict[str, Any], output_filename: str | None = None, template_id: str = "custom") -> str:
    out_path = _create_output_path(cv_data, output_filename)
    styles = _build_common_pdf_styles()
    name = cv_data.get("name") or "Candidate Name"

    if template_id == "postcard":
        story = _build_postcard_story(cv_data, styles)
    elif template_id == "sample":
        story = _build_sample_story(cv_data, styles)
    else:
        story = _build_custom_story(cv_data, styles)

    doc = SimpleDocTemplate(
        out_path,
        pagesize=A4,
        rightMargin=0.65 * inch,
        leftMargin=0.65 * inch,
        topMargin=0.65 * inch,
        bottomMargin=0.55 * inch,
        title=f"{name} CV",
        author=name,
    )
    doc.build(story, onFirstPage=_draw_confidential_footer, onLaterPages=_draw_confidential_footer)
    return out_path
