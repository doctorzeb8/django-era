from django.conf import settings
from django.core.mail import send_mail
from django.utils.text import capfirst


class Communicator:
    display_html = True

    def __init__(self, user):
        self.user = user

    def communicate(self, text):
        raise NotImplementedError

    def send(self, request, subject, component, **props):
        return self.communicate(
            subject,
            component().as_string(request, **dict(
                {'user': self.user, 'subject': subject}, **props)))


class EmailCommunicator(Communicator):
    def communicate(self, subj, text):
        return send_mail(
            capfirst(subj),
            '' if not self.display_html else text,
            '{0} <{1}>'.format(str(settings.TITLE), settings.EMAIL_HOST_USER),
            [self.user.email],
            **({} if not self.display_html else {'html_message': text}))


class CommunicationMixin:
    @property
    def comm(self):
        if not hasattr(self, '_communicator'):
            self._communicator = self.__class__.get_communicator(user=self)
        return self._communicator

    @classmethod
    def get_communicator(cls, **kw):
        if cls.USERNAME_FIELD == 'email' and settings.EMAIL_HOST_USER:
            return EmailCommunicator(**kw)
