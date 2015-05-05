from django.core.urlresolvers import resolve
from .library import register, Component, Tag
from .markup import Link


@register.era
class Table(Component):
    def slice(self, seq, d='h'):
        return list(seq)[slice(*getattr(self, d + 'slice', (None, None)))]

    def get_head_items(self):
        return []

    def get_body_items(self):
        raise NotImplemented

    def get_defaults(self):
        return {
            'striped': False,
            'bordered': False,
            'hover': True,
            'condensed': True,
            'responsive': True}

    def render_items(self, items, cell='td'):
        return ''.join(map(
            lambda row: self.inject(
                Tag,
                {'el': 'tr', 'class': row.get('level', '')},
                ''.join(map(
                    lambda c: self.inject(Tag, {'el': cell}, c),
                    self.slice(row['items'])))),
            items))

    def DOM(self):
        return self.inject(
            Tag,
            {'el': 'table', 'class': self.get_class_set(
                'striped',
                'bordered',
                'hover',
                'condensed',
                'responsive',
                prefix='table',
                include='table')},
            ''.join([
                    self.inject(
                        Tag,
                        {'el': 'thead'},
                        self.render_items(
                            [{'items': self.get_head_items()}],
                            cell='th')),
                    self.inject(
                        Tag,
                        {'el': 'tbody'},
                        self.render_items(self.get_body_items()))]))
