class Definitions:

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
        return self.texts[lang][key].format(**kwargs)
