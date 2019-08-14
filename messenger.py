import os
from telegram import ext, Bot
import smtplib
from email.utils import formataddr
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
import logging
import codecs

logger = logging.getLogger('execution')

def format_email(names, email_list):
    formated = []
    length = len(names)
    for i in range(length):
        formated.append(formataddr((Header(names[i], 'utf-8').encode(), email_list[i])))
    return formated

def send_email(user, delivery):
    logger.info('Trying to send notification email...')
    try:
        smtp_user=os.environ['SMTP_USER']
        smtp_password=os.environ['SMTP_PASS']
        sent_from = '{} BOT 🤖'.format(os.environ['BOT_NAME'])
        names = [user['name']]
        to = [user['email']]
        subject = '[🍽️Café da Manhã] Lembrete para levar no dia {}'.format(delivery['delivery_date'])
        msg = MIMEMultipart('alternative')
        msg['Subject'] = Header(subject, 'utf-8')
        msg['From'] = sent_from
        msg['To'] = ", ".join(format_email(names, to))
        with codecs.open('email_template.html', 'r', 'utf-8') as f:
            html = f.read()
        html = html.format(delivery['delivery_date'], delivery['item'], delivery['item'], delivery['quantity'], delivery['value'])
        part2 = MIMEText(html.encode('utf-8'), 'html', 'utf-8')
        msg.attach(part2)

        server = smtplib.SMTP_SSL(os.environ['SMTP_SERVER'], os.environ['SMTP_SSL_PORT'])
        server.ehlo()
        server.login(smtp_user, smtp_password)
        server.sendmail(sent_from, to, msg.as_string())
        server.close()
        logger.info('Email sent!')
        
        return True
    except Exception as e:
        logger.error(e)
        return False

def send_message(user, delivery):
    logger.info('Trying to send telegram notification message...')
    try:
        with codecs.open('telegram_template.txt', 'r', 'utf-8') as f:
            text = f.read()
        text = text.format(user['name'],delivery['delivery_date'], delivery['item'], delivery['quantity'], delivery['value'])
        bot = Bot(token=os.environ['TELEGRAM_BOT_KEY'])
        bot.sendMessage(chat_id=user['chat_id'], text=text, parse_mode='Markdown')
        logger.info('Telegram message sent!')
        return True
    except Exception as e:
        logger.error(e)
        return False

if __name__ == '__main__':
	print('Esse arquivo não pode ser executado diretamente!')