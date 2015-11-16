from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from era.utils.functools import unidec, omit


@unidec
def role_required(method, req, *args, **kw):
    if req.user.role in kw.get('allow', []):
        return method(req, *args, **omit(kw, 'allow'))
    raise PermissionDenied()
