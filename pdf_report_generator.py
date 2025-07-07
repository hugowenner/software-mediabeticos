# pdf_report_generator.py

import datetime as dt
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
)
from reportlab.lib.styles import getSampleStyleSheet

class PdfReportGenerator:
    @staticmethod
    def generate_report(filename: str, start_br: str, end_br: str, rows: list, glargina_by_date: dict):
        doc = SimpleDocTemplate(filename, pagesize=A4, leftMargin=1.5 * cm, rightMargin=1.5 * cm)
        styles = getSampleStyleSheet()
        story = []

        title = f"Relatório de Registro – {start_br} a {end_br}"
        story.append(Paragraph(title, styles["Heading1"]))
        story.append(Spacer(1, 12))

        data_by_date_iso = {}
        for date_iso, meal, carbs, glicemia, lispro, bolus, observations in rows:
            data_by_date_iso.setdefault(date_iso, []).append(
                [meal,
                 f"{carbs:.1f}" if carbs is not None else "",
                 f"{glicemia:.1f}" if glicemia is not None else "",
                 f"{lispro:.1f}" if lispro is not None else "",
                 f"{bolus:.1f}" if bolus is not None else "",
                 observations if observations is not None else ""]
            )

        all_dates_iso = sorted(list(set(list(data_by_date_iso.keys()) + list(glargina_by_date.keys()))))

        head = ["Refeição", "Carbs (g)", "Glicemia", "Lispro (UI)", "Bolus (UI)", "Observações"]
        tbl_style = TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightblue),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (1, 0), (4, -1), "CENTER"),
                ("ALIGN", (5, 0), (5, -1), "LEFT"),
            ]
        )

        grand_totals = {"carbs": 0.0, "glicemia_sum": 0.0, "glicemia_count": 0, "lispro": 0.0, "bolus": 0.0, "glargina_sum": 0.0, "glargina_count": 0}

        for date_iso in all_dates_iso:
            date_br = dt.date.fromisoformat(date_iso).strftime("%d/%m/%Y")
            story.append(Paragraph(f"<b>Data: {date_br}</b>", styles["Heading3"]))
            story.append(Spacer(1, 5))

            if date_iso in data_by_date_iso:
                tbl_data = [head] + data_by_date_iso[date_iso]
                col_widths = [2.0*cm, 2.0*cm, 2.0*cm, 2.0*cm, 2.0*cm, 6.0*cm]
                story.append(Table(tbl_data, colWidths=col_widths, style=tbl_style))
                story.append(Spacer(1, 8))
            else:
                story.append(Paragraph("<i>Nenhuma refeição registrada para este dia.</i>", styles["Normal"]))
                story.append(Spacer(1, 8))

            glargina_dose_day = glargina_by_date.get(date_iso, None)
            if glargina_dose_day is not None:
                story.append(Paragraph(f"<b>Insulina Glargina: {glargina_dose_day:.1f} UI</b>", styles["Normal"]))
                if glargina_dose_day > 0:
                    grand_totals["glargina_sum"] += glargina_dose_day
                    grand_totals["glargina_count"] += 1
            else:
                story.append(Paragraph("<i>Insulina Glargina: N/A</i>", styles["Normal"]))

            d_tot = {"carbs": 0.0, "glicemia_sum": 0.0, "glicemia_count": 0, "lispro": 0.0, "bolus": 0.0}
            if date_iso in data_by_date_iso:
                for _meal, carbs_str, glic_str, lispro_str, bolus_str, _obs_str in data_by_date_iso[date_iso]:
                    d_tot["carbs"] += float(carbs_str) if carbs_str else 0
                    if glic_str:
                        d_tot["glicemia_sum"] += float(glic_str)
                        d_tot["glicemia_count"] += 1
                    d_tot["lispro"] += float(lispro_str) if lispro_str else 0
                    d_tot["bolus"] += float(bolus_str) if bolus_str else 0

            daily_avg_glicemia = (
                d_tot["glicemia_sum"] / d_tot["glicemia_count"]
                if d_tot["glicemia_count"] > 0
                else 0.0
            )

            story.append(
                Paragraph(
                    (
                        f"Totais do dia:<br/>"  # Adiciona quebra de linha aqui
                        f"  <b>Carbs</b>: {d_tot['carbs']:.1f} g<br/>"  # Adiciona quebra de linha aqui
                        f"  <b>Glicemia Média</b>: {daily_avg_glicemia:.1f} mg/dL<br/>"  # Adiciona quebra de linha aqui
                        f"  <b>Lispro</b>: {d_tot['lispro']:.1f} UI<br/>"  # Adiciona quebra de linha aqui
                        f"  <b>Bolus</b>: {d_tot['bolus']:.1f} UI"
                    ),
                    styles["Normal"],
                )
            )
            story.append(Spacer(1, 12))

            for k in ["carbs", "lispro", "bolus"]:
                grand_totals[k] += d_tot[k]
            grand_totals["glicemia_sum"] += d_tot["glicemia_sum"]
            grand_totals["glicemia_count"] += d_tot["glicemia_count"]

        period_avg_glicemia = (
            grand_totals["glicemia_sum"] / grand_totals["glicemia_count"]
            if grand_totals["glicemia_count"] > 0
            else 0.0
        )
        period_avg_glargina = (
            grand_totals["glargina_sum"] / grand_totals["glargina_count"]
            if grand_totals["glargina_count"] > 0
            else 0.0
        )

        story.append(Paragraph("<b>Totais do período</b>", styles["Heading2"]))
        story.append(
            Paragraph(
                (
                    f"<b>Carboidratos</b>: {grand_totals['carbs']:.1f} g<br/>" # Adiciona <br/>
                    f"<b>Glicemia Média</b>: {period_avg_glicemia:.1f} mg/dL<br/>" # Adiciona <br/>
                    f"<b>Insulina Lispro total</b>: {grand_totals['lispro']:.1f} UI<br/>" # Adiciona <br/>
                    f"<b>Bolus correção total</b>: {grand_totals['bolus']:.1f} UI<br/>" # Adiciona <br/>
                    f"<b>Glargina média diária</b>: {period_avg_glargina:.1f} UI"
                ),
                styles["Normal"],
            )
        )

        doc.build(story)