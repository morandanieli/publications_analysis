import spacy
import logging
nlp = spacy.load("en_core_web_sm")


def analyze_title(title, queries, res):
    # analyze title
    doc = nlp(title)
    sub_toks = [tok for tok in doc if (tok.dep_ == "nsubj")]
    chunks = []
    for chunk in doc.noun_chunks:
        out = {}
        root = chunk.root
        out[root.pos_] = root
        for tok in chunk:
            if tok != root:
                out[tok.pos_] = tok
        chunks.append(out)
    if sub_toks:
        nouns = list(map(lambda x: x['NOUN'], filter(lambda x: 'NOUN' in x, chunks)))
        sub_toks = list(set(nouns).intersection(sub_toks))
    else:
        logging.warning("no subject found for title '{}'".format(title))

    sub_count = 0
    tokens = []
    tokens_lower = []
    for sub in sub_toks:
        tokens.append(str(sub))
        tokens_lower.append(str(sub).lower())
        sub2 = str(sub).lower()
        if sub2 in queries:
            # we want it highest
            sub_count += 1

    res['sub_toks'] = tokens
    res['sub_toks_l'] = tokens_lower
    res['sub_count'] = sub_count

    # we want it lowest
    remaining_sub_count = len(sub_toks) - sub_count
    res['remaining_sub_count'] = remaining_sub_count
    res['weighted_sub_count'] = sub_count - remaining_sub_count


def analyze_doc():
    #TODO
    # lines = text.split("\n")
    # lines = list(filter(None, lines))
    #
    # limit = 10
    # for i, line in enumerate(lines):
    #     if i > limit:
    #         break
    #     doc = nlp(line)
    #     sub_toks = [tok for tok in doc if (tok.dep_ == "nsubj")]
    #     print(line, sub_toks)
    pass


if __name__ == '__main__':
    #analyze_title('Cybersecurity could offer a way for underrepresented groups to break into tech – TechCrunch', 'ads', {})
    pass
