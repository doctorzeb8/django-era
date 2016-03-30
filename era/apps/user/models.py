from django.conf import settings
from django.contrib.auth.hashers import get_hasher
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.core.validators import RegexValidator
from django.db import models
from era import random_str
from era.utils.translation import _, verbose_choices
from .communicators import CommunicationMixin


class Confirm(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    key = models.CharField(max_length=30)
    code = models.CharField(max_length=128, verbose_name=_('code'), unique=True)
    sign = models.CharField(max_length=128, verbose_name=_('confirmation'))

    @classmethod
    def gen_code(cls, salt=None):
        hasher = get_hasher()
        generate = True
        while generate:
            code = random_str()
            encoded = hasher.encode(code, salt or hasher.salt())
            generate = bool(cls.objects.filter(code=encoded).count())
        return code, encoded


class BaseUser(CommunicationMixin, AbstractBaseUser):
    class Meta:
        abstract = True
        verbose_name = _('user')
        verbose_name_plural = _('users')

    USERNAME_FIELD = 'email'
    objects = BaseUserManager()
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('date joined'))
    access = models.BooleanField(_('access'), default=True)

    email = models.EmailField(verbose_name=_('email'), unique=True, null=True)
    name = models.CharField(verbose_name=_('username'), max_length=20, null=True)
    role = models.CharField(
        verbose_name=_('role'),
        max_length=10,
        choices=verbose_choices(*settings.USER_ROLES))

    @property
    def username_value(self):
        return getattr(self, self.USERNAME_FIELD)

    @property
    def username_dict(self):
        return {self.USERNAME_FIELD: self.username_value}

    def __str__(self):
        return '{0} <{1}>'.format(self.name, self.username_value)

    def get_short_name(self):
        return self.name
