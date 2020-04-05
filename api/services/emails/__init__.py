from api.utils.constants import APP_EMAIL
from celery_config import celery_app
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import os
import codecs
import logging


class EmailUtil:
    SEND_CLIENT = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))

    @staticmethod
    @celery_app.task(name='send-email-to-user-as-html')
    def send_mail_as_html(subject, receivers, html, blind_copies=None):
        """Sends mail as html

        Args:
            subject(str): The subject of the email
            receivers(list):  A list of emails of the receivers
            html(str): The html to be sent as a mail

        Returns:
            (str): Returns 'success' if the mail is sent successfully
        """

        message = Mail(from_email=APP_EMAIL,
                       to_emails=receivers,
                       subject=subject,
                       html_content=html)
        blind_copies = blind_copies if blind_copies else []
        for bcc in blind_copies:
            message.add_bcc(bcc)
        try:
            EmailUtil.SEND_CLIENT.send(message)
        except Exception as e:
            logging.exception(e)
            return 'Failure'
        return 'Success'

    @classmethod
    def send_email_from_template(cls, subject, template_name, emails,
                                 **template_kwargs):
        emails = emails if isinstance(emails, list) else [emails]
        html = cls.extract_html_from_template(template_name, **template_kwargs)
        cls.send_mail_as_html.delay(
            subject,
            emails,
            html,
        )

    @staticmethod
    def extract_html_from_template(template_name, **kwargs):
        """Extracts HTML text from template file

        Reads the HTML file, replaces the arguments with the value in kwargs and
        Returns the resulting html as string

        Args:
            template_name: The name of a file in api/utils/emails/templates
            **kwargs:

        Returns:
            (str): The HTML that was read and parsed from the template file

        """
        with codecs.open(f'api/services/emails/templates/{template_name}.html',
                         'r', 'utf-8') as f:
            text = ''.join(f.readlines())

            for key, value in kwargs.items():
                print(value)
                text = text.replace("{{" + key + '}}', value)
            return text
