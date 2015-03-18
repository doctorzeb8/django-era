from django.conf.urls import url


def short_url(name, *args):
    return url(r'^{0}/?$'.format('/'.join([name] + list(args))), name, name=name)
