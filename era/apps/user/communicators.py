from django.conf import settings
from django.core.mail import send_mail
from django.utils.text import capfirst


class Communicator:
    display_html = True

    def __init__(self, user):
        self.user = user

    def communicate(self, subj, text):
        raise NotImplementedError

    def send(self, request, subject, component, **props):
        self.request = request
        return self.communicate(
            subject,
            component().as_string(request, **dict(
                {'user': self.user, 'subject': subject}, **props)))


class EmailCommunicator(Communicator):
    def get_from(self):
        return '{0} <{1}>'.format(str(settings.TITLE), settings.EMAIL_HOST_USER)

    def get_connection(self):
        return {}

    def communicate(self, subj, text):
        return send_mail(
            capfirst(subj),
            '' if not self.display_html else text,
            self.get_from(),
            [self.user.email],
            **dict(
                {} if not self.display_html else {'html_message': text},
                **self.get_connection()))


class CommunicationMixin:
    @property
    def comm(self):
        if not hasattr(self, '_communicator'):
            self._communicator = self.__class__.get_communicator(user=self)
        return self._communicator

    @classmethod
    def get_communicator(cls, **kw):
        if cls.USERNAME_FIELD == 'email':
            return EmailCommunicator(**kw)
