from itertools import chain
from pymorphy2 import MorphAnalyzer
morph = MorphAnalyzer()


def inflect(msg):
    if '"' in msg:
        subj, obj, *body = msg.rstrip('.').split()
        gender = morph.parse(subj)[0].tag.gender
        for i, word in enumerate(body[:]):
            parse = morph.parse(word)[0]
            body[i] = word if not parse.tag.POS in ('VERB', 'PRTS') \
                else parse.inflect({gender}).word
        return ' '.join(chain([subj, obj], body))
