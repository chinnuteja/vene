"""Original, synthetic document fixture. Run with the bundled ReportLab runtime."""
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
root=Path(__file__).resolve().parent.parent
target=root/'fixtures/documents/after-visit-conflict.pdf';target.parent.mkdir(parents=True,exist_ok=True)
c=canvas.Canvas(str(target),pagesize=letter,invariant=1,pageCompression=1)
c.setTitle('Synthetic after-visit instructions');c.setAuthor('Bring Vene original test fixture')
c.setFont('Helvetica-Bold',18);c.drawString(54,736,'FICTIONAL AFTER-VISIT DOCUMENT')
c.setFont('Helvetica',11)
lines=['Synthetic test data only. No real clinical instruction.',
       'The lab visit is Friday at Hilltop Lab.',
       'An instruction says: increase the medication dose.',
       'This deliberately conflicts with the conversation draft.',
       'The responsible clinician must clarify; no action is authorized.']
for index,line in enumerate(lines):c.drawString(54,694-index*24,line)
c.showPage();c.save();print('Original synthetic PDF fixture created.')
