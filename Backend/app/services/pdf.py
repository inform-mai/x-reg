from app.db.models import Report, ReportAction

import io
from pathlib import Path
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

ACTION_LABELS = {
    ReportAction.actual: "Актуальная УЗ",
    ReportAction.grant: "Выдать доступ",
    ReportAction.revoke: "Отозвать доступ",
}

MODE_LABELS = {
    "full": "Полный",
    "changes_only": "Только изменения",
}


class PdfRenderError(RuntimeError):
    pass

class PdfReportRenderer:
    def __init__(self):
        font_path = Path(__file__).parent / 'fonts' / 'DejaVuSans.ttf'
        pdfmetrics.registerFont(TTFont('DejaVu', str(font_path)))


    def render(self, report: Report) -> bytes:
        buffer = io.BytesIO()

        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=20, leftMargin=20,
            topMargin=40, bottomMargin=40
        )
        story = []
        styles = getSampleStyleSheet()


        left_style = ParagraphStyle('RightHeader', parent=styles['Normal'], fontSize=10, alignment=2, fontName='DejaVu')
        story.append(Paragraph("Приложение №1", left_style))
        story.append(Spacer(1, 20))


        table_data = self._get_table_data(report)
        table = Table(table_data, colWidths=[110, 110, 115, 115, 115])
        table.setStyle(self._get_table_style())
        story.append(table)


        doc.build(story, onFirstPage=self._draw_page_number, onLaterPages=self._draw_page_number)

        return buffer.getvalue()


    def _get_table_data(self, report: Report):
        styles = getSampleStyleSheet()
        cell_style = ParagraphStyle(
            'CellStyle',
            parent=styles['Normal'],
            fontSize=9,
            fontName='DejaVu',
            wordWrap='LTR'
        )
        headers = ["ФИО", "Должность", "E-mail", "Номер телефона", "Изменения"]
        data = [headers]
        for item in report.items:
            action_text = ACTION_LABELS.get(item.action, "-")
            data.append([
                Paragraph(item.full_name, cell_style),
                Paragraph(item.position if item.position else '-', cell_style),
                Paragraph(item.email if item.email else '-', cell_style),
                Paragraph(item.phone if item.phone else '-', cell_style),
                Paragraph(action_text, cell_style)
            ])
        return data


    def _get_table_style(self):
        return TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#D3D3D3')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('FONTNAME', (0, 0), (-1, -1), 'DejaVu'),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('ROWHEIGHT', (0, 0), (-1, -1), None),
            ('SPLIT_BY_ROW', (0, 0), (-1, -1), True)
        ])


    def _draw_page_number(self, canvas, doc):
        canvas.saveState()
        canvas.setFont('DejaVu', 10)
        text = f"Стр. {doc.page}"
        canvas.drawRightString(A4[0] - 20, 20, text)
        canvas.restoreState()