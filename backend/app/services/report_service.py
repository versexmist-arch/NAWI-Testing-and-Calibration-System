import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from fastapi import HTTPException

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
    HRFlowable,
)

from ..config import settings
from ..models import (
    TestSession,
    TestRevision,
    GeneratedReport,
    Observation,
    CalculationResult,
    RuleEvaluation,
    LaboratorySettings,
)
from .audit_service import record_audit_event


def generate_pdf_report(db: Session, test_session_id: str, operator_name: str = "Lead Metrologist") -> GeneratedReport:
    """Generate an official laboratory-grade PDF report from saved database records."""
    session = db.query(TestSession).filter(TestSession.id == test_session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Test session not found.")

    instrument = session.instrument
    if not instrument:
        raise HTTPException(status_code=404, detail="Instrument not found.")

    calc_record = db.query(CalculationResult).filter(CalculationResult.test_session_id == test_session_id).first()
    eval_record = db.query(RuleEvaluation).filter(RuleEvaluation.test_session_id == test_session_id).first()
    obs_record = db.query(Observation).filter(Observation.test_session_id == test_session_id).first()

    if not calc_record or not eval_record:
        raise HTTPException(
            status_code=400,
            detail="Cannot generate report: test session must be calculated and evaluated first."
        )

    # Unique Report ID and Revision Tracking (BUG-8)
    report_id = f"REP-{uuid.uuid4().hex[:8].upper()}"
    report_version = session.version or 1
    filename = f"{report_id}_v{report_version}_{session.test_category.lower()}_{instrument.serial_number}.pdf"
    os.makedirs(settings.REPORTS_DIR, exist_ok=True)
    file_path = os.path.join(settings.REPORTS_DIR, filename)

    # Build document
    doc = SimpleDocTemplate(
        file_path,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()

    # Custom typography styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=18,
        textColor=colors.HexColor('#0f172a'),
    )
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#475569'),
    )
    h2_style = ParagraphStyle(
        'Heading2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=13,
        textColor=colors.HexColor('#1e3a8a'),
        spaceBefore=7,
        spaceAfter=3,
    )
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10.5,
        textColor=colors.HexColor('#1e293b'),
    )
    bold_body = ParagraphStyle(
        'BoldBody',
        parent=body_style,
        fontName='Helvetica-Bold',
    )
    badge_pass = ParagraphStyle(
        'BadgePass',
        parent=body_style,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#15803d'),
    )
    badge_fail = ParagraphStyle(
        'BadgeFail',
        parent=body_style,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#b91c1c'),
    )
    badge_pending = ParagraphStyle(
        'BadgePending',
        parent=body_style,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#d97706'),
    )

    lab = db.query(LaboratorySettings).first()
    lab_name = lab.lab_name if lab else "NAWI TESTING & CALIBRATION MANAGEMENT SYSTEM"
    org_name = lab.organization if lab else "Smart India Hackathon 2026 | Problem ID: SIH26035 | Team: VisionVerity"
    accred_no = lab.accreditation_number if lab else "OIML R-76 Calibrated Testing Protocol"

    story = []

    # 1. Header Banner
    now_utc = datetime.now(timezone.utc)
    rev_label = f"Rev {report_version} (AMENDED)" if report_version > 1 else f"Rev {report_version} (ORIGINAL)"
    header_data = [
        [
            Paragraph(f"<b>{lab_name.upper()}</b>", title_style),
            Paragraph(f"<b>REPORT ID:</b> {report_id}<br/><b>REPORT VERSION:</b> {rev_label}<br/><b>DATE:</b> {now_utc.strftime('%Y-%m-%d %H:%M UTC')}", subtitle_style)
        ],
        [
            Paragraph(f"{org_name}<br/><b>Accreditation:</b> {accred_no}", subtitle_style),
            Paragraph(f"<b>TEST SESSION:</b> {session.id} (v{report_version})<br/><b>STATUS:</b> {session.status}", subtitle_style)
        ]
    ]
    header_table = Table(header_data, colWidths=[360, 180])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#1e3a8a'), spaceAfter=7))

    # Amendment Notice (if amended report)
    if report_version > 1:
        last_rev = db.query(TestRevision).filter(TestRevision.test_session_id == session.id).order_by(TestRevision.revision_number.desc()).first()
        if last_rev:
            amend_time_str = last_rev.created_at.strftime('%Y-%m-%d %H:%M UTC') if hasattr(last_rev.created_at, 'strftime') else str(last_rev.created_at)
            amend_box = [
                [Paragraph("<b>OFFICIAL AMENDMENT / REVISION RECORD:</b>", bold_body)],
                [Paragraph(
                    f"This calibration report represents <b>Revision {report_version}</b> and formally supersedes previous certificate revisions. "
                    f"<br/><b>Amendment Justification:</b> {last_rev.amendment_reason}"
                    f"<br/><b>Authorized Metrologist:</b> {last_rev.amended_by} (Recorded: {amend_time_str})",
                    body_style
                )]
            ]
            amend_table = Table(amend_box, colWidths=[540])
            amend_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fef3c7')),
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#d97706')),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ]))
            story.append(amend_table)
            story.append(Spacer(1, 6))

    # 2. Instrument & Environmental Specifications Table
    story.append(Paragraph("1. INSTRUMENT & ENVIRONMENTAL SPECIFICATIONS", h2_style))
    spec_data = [
        [
            Paragraph("<b>Manufacturer:</b>", bold_body),
            Paragraph(str(instrument.manufacturer), body_style),
            Paragraph("<b>Max Capacity:</b>", bold_body),
            Paragraph(f"{instrument.max_capacity} {instrument.unit}", body_style),
        ],
        [
            Paragraph("<b>Model:</b>", bold_body),
            Paragraph(str(instrument.model), body_style),
            Paragraph("<b>Verification Interval (e):</b>", bold_body),
            Paragraph(f"{instrument.verification_scale_interval} {instrument.unit}", body_style),
        ],
        [
            Paragraph("<b>Serial Number:</b>", bold_body),
            Paragraph(str(instrument.serial_number), body_style),
            Paragraph("<b>Accuracy Class:</b>", bold_body),
            Paragraph(str(instrument.accuracy_class), body_style),
        ],
        [
            Paragraph("<b>Instrument Type:</b>", bold_body),
            Paragraph(str(instrument.instrument_type), body_style),
            Paragraph("<b>Intervals Count (n):</b>", bold_body),
            Paragraph(str(instrument.scale_intervals_count or int(instrument.max_capacity / instrument.verification_scale_interval)), body_style),
        ],
        [
            Paragraph("<b>Location:</b>", bold_body),
            Paragraph(str(session.laboratory_location or instrument.location or "Metrology Lab"), body_style),
            Paragraph("<b>Operator:</b>", bold_body),
            Paragraph(str(session.operator_name or operator_name), body_style),
        ],
        [
            Paragraph("<b>Test Category:</b>", bold_body),
            Paragraph(session.test_category.capitalize(), body_style),
            Paragraph("<b>Environment:</b>", bold_body),
            Paragraph(f"Temp: {session.ambient_temperature or '20.0'} °C | RH: {session.relative_humidity or '50'} %", body_style),
        ],
    ]
    spec_table = Table(spec_data, colWidths=[110, 160, 130, 140])
    spec_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(spec_table)
    story.append(Spacer(1, 6))

    # 3. Recorded Observations & Calculations
    cat = session.test_category.lower()
    full_calc = calc_record.full_data or {}

    story.append(Paragraph("2. RECORDED OBSERVATIONS & CALCULATION RESULTS", h2_style))

    if cat == "eccentricity":
        pos_results = full_calc.get("position_results", [])
        obs_header = [
            Paragraph("<b>Pos ID</b>", bold_body),
            Paragraph("<b>Receptor Position</b>", bold_body),
            Paragraph(f"<b>Load ({instrument.unit})</b>", bold_body),
            Paragraph(f"<b>Indication ({instrument.unit})</b>", bold_body),
            Paragraph(f"<b>Zero ({instrument.unit})</b>", bold_body),
            Paragraph(f"<b>Indication Error</b>", bold_body),
            Paragraph(f"<b>Eccentricity Dev (ΔE)</b>", bold_body),
        ]
        obs_rows = [obs_header]
        for p in pos_results:
            obs_rows.append([
                Paragraph(str(p.get("position_id")), body_style),
                Paragraph(str(p.get("position_name")), body_style),
                Paragraph(f"{p.get('reference_load'):.2f}", body_style),
                Paragraph(f"{p.get('indication'):.2f}", body_style),
                Paragraph(f"{p.get('zero_indication', 0.0):.2f}", body_style),
                Paragraph(f"{p.get('indication_error'):+.4f}", body_style),
                Paragraph(f"{p.get('eccentricity_deviation'):+.4f}", body_style),
            ])
        ecc_table = Table(obs_rows, colWidths=[55, 95, 75, 80, 65, 85, 85])
        ecc_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e2e8f0')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#94a3b8')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#ffffff'), colors.HexColor('#f8fafc')]),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
        ]))
        story.append(ecc_table)

    elif cat == "linearity":
        pts = full_calc.get("point_results", [])
        obs_header = [
            Paragraph("<b>#</b>", bold_body),
            Paragraph(f"<b>Ref Load ({instrument.unit})</b>", bold_body),
            Paragraph(f"<b>Indication ({instrument.unit})</b>", bold_body),
            Paragraph("<b>Direction</b>", bold_body),
            Paragraph(f"<b>Ind. Error</b>", bold_body),
            Paragraph(f"<b>Corrected Error (Ec)</b>", bold_body),
            Paragraph("<b>Error in e</b>", bold_body),
        ]
        obs_rows = [obs_header]
        for pt in pts:
            e_str = f"{pt.get('corrected_error_in_e'):+.2f} e" if pt.get("corrected_error_in_e") is not None else "N/A"
            obs_rows.append([
                Paragraph(str(pt.get("index")), body_style),
                Paragraph(f"{pt.get('load'):.2f}", body_style),
                Paragraph(f"{pt.get('indication'):.2f}", body_style),
                Paragraph(str(pt.get("direction")), body_style),
                Paragraph(f"{pt.get('indication_error'):+.4f}", body_style),
                Paragraph(f"{pt.get('corrected_error'):+.4f}", body_style),
                Paragraph(e_str, body_style),
            ])
        lin_table = Table(obs_rows, colWidths=[30, 95, 95, 75, 80, 85, 80])
        lin_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e2e8f0')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#94a3b8')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#ffffff'), colors.HexColor('#f8fafc')]),
            ('TOPPADDING', (0, 0), (-1, -1), 2.5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ]))
        story.append(lin_table)

    elif cat == "repeatability":
        runs = full_calc.get("run_records", [])
        obs_header = [
            Paragraph("<b>Run #</b>", bold_body),
            Paragraph(f"<b>Applied Load ({instrument.unit})</b>", bold_body),
            Paragraph(f"<b>Indication ({instrument.unit})</b>", bold_body),
            Paragraph(f"<b>Run Error ({instrument.unit})</b>", bold_body),
            Paragraph(f"<b>Dev from Mean ({instrument.unit})</b>", bold_body),
        ]
        obs_rows = [obs_header]
        for r in runs:
            obs_rows.append([
                Paragraph(str(r.get("run_number")), body_style),
                Paragraph(f"{r.get('reference_load'):.2f}", body_style),
                Paragraph(f"{r.get('indication'):.2f}", body_style),
                Paragraph(f"{r.get('error'):+.4f}", body_style),
                Paragraph(f"{r.get('deviation_from_mean', 0.0):+.4f}", body_style),
            ])
        rep_table = Table(obs_rows, colWidths=[55, 120, 120, 120, 125])
        rep_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e2e8f0')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#94a3b8')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#ffffff'), colors.HexColor('#f8fafc')]),
            ('TOPPADDING', (0, 0), (-1, -1), 2.5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        story.append(rep_table)

    story.append(Spacer(1, 6))

    # 4. Calculation Summary Box
    summary_data = calc_record.summary_data or {}
    summary_items = []
    for k, v in summary_data.items():
        if isinstance(v, (int, float)):
            summary_items.append(f"<b>{k.replace('_', ' ').title()}:</b> {v:.4f}")
        elif isinstance(v, str):
            summary_items.append(f"<b>{k.replace('_', ' ').title()}:</b> {v}")

    story.append(Paragraph(
        "<b>Calculation Engine Summary:</b> " + " | ".join(summary_items[:6]),
        subtitle_style
    ))
    story.append(Spacer(1, 6))

    # 5. OIML R-76 Configured Rule Evaluation Table
    eval_dict = eval_record.evaluations_data or {}
    story.append(Paragraph("3. OIML R-76 CONFIGURED RULE EVALUATION", h2_style))

    rule_header = [
        Paragraph("<b>Rule ID & Source</b>", bold_body),
        Paragraph("<b>Applicable Criterion</b>", bold_body),
        Paragraph("<b>Observed Value</b>", bold_body),
        Paragraph("<b>Tolerance</b>", bold_body),
        Paragraph("<b>Outcome</b>", bold_body),
    ]
    rule_rows = [rule_header]

    for item in eval_dict.get("evaluations", []):
        outcome = item.get("outcome", "INCOMPLETE")
        if outcome == "PASS":
            out_style = badge_pass
        elif outcome == "FAIL":
            out_style = badge_fail
        else:
            out_style = badge_pending

        rule_rows.append([
            Paragraph(f"<b>{item.get('rule_id')}</b><br/>{item.get('source_reference')}", body_style),
            Paragraph(item.get("applicable_criterion", "N/A"), body_style),
            Paragraph(item.get("observed_value", "N/A"), body_style),
            Paragraph(item.get("tolerance_limit", "N/A"), body_style),
            Paragraph(f"<b>{outcome}</b>", out_style),
        ])

    rule_table = Table(rule_rows, colWidths=[120, 130, 110, 100, 80])
    rule_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e2e8f0')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#94a3b8')),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(rule_table)
    story.append(Spacer(1, 8))

    # 6. Overall Evaluation Summary Banner
    overall_outcome = eval_dict.get("overall_outcome", "INCOMPLETE")
    banner_bg = (
        colors.HexColor('#dcfce7') if overall_outcome == "PASS"
        else colors.HexColor('#fee2e2') if overall_outcome == "FAIL"
        else colors.HexColor('#fef3c7')
    )
    banner_text = (
        f"<b>OVERALL EVALUATION OUTCOME: {overall_outcome}</b> — {eval_dict.get('summary_text', '')} "
        f"[Rule Version: {eval_dict.get('rule_version', 'OIML-R76-2006-v1.0')}]"
    )
    banner_table = Table([[Paragraph(banner_text, body_style)]], colWidths=[540])
    banner_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), banner_bg),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#94a3b8')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(banner_table)
    story.append(Spacer(1, 8))

    # 7. Regulatory Disclaimer & Sign-Off Section
    disclaimer_text = f"<b>METROLOGICAL DISCLAIMER & LIMITATIONS:</b> {lab.report_disclaimer if lab and lab.report_disclaimer else 'This evaluation report is generated by the VisionVerity SIH 2026 NAWI Calibration Support prototype. It provides structured calculation, traceable observations, and rule-based checking against configured OIML R-76 recommendations. It does not replace an authorized verification certificate issued by an accredited legal metrology authority.'}"
    story.append(Paragraph(disclaimer_text, subtitle_style))
    story.append(Spacer(1, 8))

    # Sign-off Box
    signoff_data = [
        [
            Paragraph("<b>Tested By (Operator):</b>", bold_body),
            Paragraph(str(session.operator_name or operator_name), body_style),
            Paragraph("<b>Verified By (Technical Reviewer):</b>", bold_body),
            Paragraph("____________________________", body_style),
        ],
        [
            Paragraph("<b>Signature:</b>", bold_body),
            Paragraph("____________________________", body_style),
            Paragraph("<b>Date of Review:</b>", bold_body),
            Paragraph(now_utc.strftime('%Y-%m-%d'), body_style),
        ]
    ]
    signoff_table = Table(signoff_data, colWidths=[135, 135, 140, 130])
    signoff_table.setStyle(TableStyle([
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LINEABOVE', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
    ]))
    story.append(KeepTogether([signoff_table]))

    # Build document
    doc.build(story)

    # Mark any previously active reports for this session as superseded (BUG-8)
    prior_reports = db.query(GeneratedReport).filter(
        GeneratedReport.test_session_id == test_session_id,
        GeneratedReport.superseded_by == None
    ).all()
    for pr in prior_reports:
        pr.is_superseded = True
        pr.superseded_by = report_id

    # Save new report to database
    report_record = GeneratedReport(
        id=report_id,
        test_session_id=test_session_id,
        instrument_id=instrument.id,
        version=report_version,
        is_superseded=False,
        superseded_by=None,
        file_path=file_path,
        file_name=filename,
        generated_by=session.operator_name or operator_name,
        report_type="OIML R-76 Metrological Test Report",
    )
    db.add(report_record)
    db.commit()
    db.refresh(report_record)

    record_audit_event(
        db=db,
        action="REPORT_GENERATED",
        actor=session.operator_name or operator_name,
        test_session_id=test_session_id,
        instrument_id=instrument.id,
        details={
            "report_id": report_id,
            "file_name": filename,
            "version": report_version,
            "superseded_reports_count": len(prior_reports),
        }
    )

    return report_record
