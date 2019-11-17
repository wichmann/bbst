
import logging
from datetime import datetime

from reportlab.lib.units import cm, mm
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.platypus.flowables import Image, PageBreak


logger = logging.getLogger('bbst.data')


PAGE_WIDTH, PAGE_HEIGHT = A4
BORDER_HORIZONTAL = 2.0*cm
BORDER_VERTICAL = 1.5*cm


def build_footer(canvas, doc):
    today = datetime.today().strftime('%d.%m.%Y')
    canvas.saveState()
    canvas.setFont('Helvetica', 10)
    canvas.drawString(BORDER_HORIZONTAL, BORDER_VERTICAL, 'Berufsbildende Schule des Landkreises Osnabrück, Brinkstraße')
    canvas.drawRightString(PAGE_WIDTH-BORDER_HORIZONTAL, BORDER_VERTICAL, today)
    canvas.restoreState()

def create_user_info_document(output_file, teacher_list):
    logger.debug('Creating user info document...')
    subject_paragraph_style = ParagraphStyle(name='Normal', fontSize=12, leading=20,
                                             fontName='Times-Bold', spaceAfter=0.75*cm)
    main_paragraph_style = ParagraphStyle(name='Normal', fontSize=11, leading=18,
                                          fontName='Times-Roman', spaceAfter=0.25*cm,
                                          hyphenationLang='de_DE', embeddedHyphenation=1, uriWasteReduce=0.3)
    data_paragraph_style = ParagraphStyle(name='Normal', fontSize=11, fontName='Courier',
                                          spaceAfter=0.5*cm, alignment=TA_CENTER)
    # prepare data for document
    title = 'Benutzerdaten'
    author = 'bbst - BBS Teacher Management'
    logo = Image('logo.png', width=PAGE_WIDTH-2*BORDER_HORIZONTAL, height=5.2445*cm, hAlign='CENTER')
    info_text_greeting = 'Liebe Kollegin, lieber Kollege,<br/>ihre Benutzerdaten lauten wie folgt:'
    info_text_paragraphs = ["""Diese Zugangsdaten erlauben die Rechnernutzung in allen Räumen mit dem Logodidact-System.
    Außerdem kann es zum Zugriff auf den Stundenplan über WebUntis und die Lernplattform Moodle genutzt werden.""",
    """In Logodidact, Moodle und WebUntis lässt sich das Passwort ändern. Allerdings gilt jede Änderung nur für
    das jeweilige System! Sollten Sie ihr Passwort vergessen haben, besteht bei Moodle und Webuntis die
    Möglichkeit, sich ein neues Passwort per Mail zusenden zu lassen.""",
    """Weitere Informationen finden Sie im Moodle-Kurs unter
    <a color="blue" href="https://moodle.nibis.de/bbs_osb/course/view.php?id=7">https://moodle.nibis.de/bbs_osb/course/view.php?id=7</a>.
    Bei allen weiteren Fragen können Sie sich gerne bei mir melden.""", 
    """<br/>Viele Grüße<br/>&nbsp;&nbsp;&nbsp;&nbsp;Christian Wichmann<br/>&nbsp;&nbsp;&nbsp;&nbsp;wichmann@bbs-os-brinkstr.de"""]
    # building document
    doc = SimpleDocTemplate(output_file, author=author, title=title)
    story = []
    for t in teacher_list:
        user_data = '{}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{}'.format(t.username, t.password)
        story.append(logo)
        story.append(Spacer(1,1.75*cm))
        story.append(Paragraph('<b>{}</b>'.format(title), subject_paragraph_style))
        story.append(Paragraph(info_text_greeting, main_paragraph_style))
        story.append(Paragraph(user_data, data_paragraph_style))
        for p in info_text_paragraphs: story.append(Paragraph(p, main_paragraph_style)) 
        story.append(PageBreak())
    doc.build(story, onFirstPage=build_footer, onLaterPages=build_footer)
