class Definitions:

    READABLE_DICT = {
        'gender': {
            'm': {'ru': 'мужской'},
            'f': {'ru': 'женский'},
        },
        'preference': {
            'm': {'ru': 'мужчины'},
            'f': {'ru': 'девушки'},
            'b': {'ru': 'все'},
        },
    }

    def __init__(self):
        self.langs = ['ru']
        self.texts = Definitions.load_texts(self.langs)

    @staticmethod
    def load_texts(langs):
        texts = {}
        for lang in langs:
            texts[lang] = {}
            with open('definitions/{lang}.txt'.format(lang=lang)) as f:
                for line in f:
                    if line:
                        key, text = line.split('=')
                        texts[lang][key] = text.replace(r'\n', '\n')

        return texts

    def get_text(self, key, lang='ru', **kwargs):
        for k in kwargs:
            if k in self.READABLE_DICT:
                kwargs[k] = self.READABLE_DICT[k][kwargs[k]][lang]

        return self.texts[lang][key].format(**kwargs)
