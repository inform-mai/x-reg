from app.db.repo import ReportRepo, utc_now
from app.services.pdf import PdfReportRenderer
from app.db.models import Report, ReportMode, User
from datetime import date

class ReportService:
    def __init__(self, db):
        self.db = db
        self.repo = ReportRepo(db)


    def create_report(self, mode, comment, user):
        employees = self.repo.employees_for_report(mode)

        report = self.repo.create_with_items(
            mode=mode,
            comment=comment,
            file_name=f"Приложение к письму в 12 Центр_{date.today()}",
            user_id=user.id,
            employees=employees
        )
        return report


    def render_pdf(self, report):
        renderer = PdfReportRenderer()
        pdf_bytes = renderer.render(report)
        return pdf_bytes
