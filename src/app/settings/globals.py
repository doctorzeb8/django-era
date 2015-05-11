from era.settings import *
INSTALLED_APPS += ['bootstrap_themes'] + MODULES
TITLE = 'django era'

try:
    from .locals import *
except ImportError:
    pass
