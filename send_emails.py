import os, sys
import django
import datetime
from django.core.mail import EmailMultiAlternatives

proj = os.path.dirname(os.path.abspath('manage.py'))
sys.path.append(proj)
os.environ["DJANGO_SETTINGS_MODULE"] = "vacancy.settings"

django.setup()
from scraping.models import Vacancy
from usa_job_last.settings import (
    EMAIL_HOST_USER, EMAIL_SEND
)

ADMIN_USER = EMAIL_HOST_USER

today = datetime.date.today()
qs = Vacancy.objects.filter(timestamp=today).values()
count = len(qs)
subject = f"Newsletter of vacancies {count} by {today}"
text_content = f"Newsletter of vacancies {today}"
from_email = EMAIL_HOST_USER
empty = '<h2>Unfortunately, there are no data available for your preferences today.</h2>'

to_email = EMAIL_SEND

html = ''

for row in qs:
    html += f'<h3><a href="{row["url"]}">{row["title"]}</a></h3>'
    html += f'<p>{row["description"]}</p>'
    html += f'<p>{row["company"]}</p><br><hr>'
_html = html if html else empty

if subject:
    msg = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
    msg.attach_alternative(_html, "text/html")
    msg.send()
