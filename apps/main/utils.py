import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

def send_email_code(email, code, code_type):
    # Рендерим HTML-шаблон
    html_message = render_to_string('email_send_code.html', {
        'code': code,
        'code_type': code_type,
        'email': email,
    })
    # Plain text версия
    if code_type == 'register':
        subject = 'Код подтверждения регистрации'
        text_message = f'Ваш код подтверждения регистрации: {code}\n\nЕсли вы не регистрировались, проигнорируйте это письмо.'
    else:
        subject = 'Код для сброса пароля'
        text_message = f'Ваш код для сброса пароля: {code}\n\nЕсли вы не запрашивали сброс, проигнорируйте это письмо.'
    plain_message = strip_tags(html_message) + "\n\n" + text_message

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = settings.HOST_USER
    msg['To'] = email
    msg.attach(MIMEText(plain_message, 'plain', 'utf-8'))
    msg.attach(MIMEText(html_message, 'html', 'utf-8'))

    try:
        server = smtplib.SMTP(settings.HOST, settings.PORT)
        if getattr(settings, 'USE_TLS', True):
            server.starttls()
        server.login(settings.HOST_USER, settings.HOST_PASSWORD)
        server.sendmail(settings.HOST_USER, [email], msg.as_string())
        server.quit()
    except Exception as e:
        raise Exception(f'Ошибка отправки email: {e}') 