from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from era.utils.functools import unidec, omit


@unidec
def role_required(method, req, *args, **kw):
    if req.user.role in kw.get('allow', []):
        return method(req, *args, **omit(kw, 'allow'))
    raise PermissionDenied()


@unidec
def anonymous_required(method, req, *args, **kw):
    if req.user.is_authenticated():
        if kw.get('logout', False):
            auth.logout(req)
            return redirect(req.get_full_path())
        else:
            return redirect('/')
    return method(req, *args, **omit(kw, 'logout'))
