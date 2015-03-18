from era.settings import *
INSTALLED_APPS += ['bootstrap_themes'] + MODULES

try:
    from .locals import *
except ImportError:
    pass
