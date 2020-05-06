import pandas as pd
import re
import spacy

from spacy.matcher import Matcher

TEXTS = ["chocolate lip balm less than 500 rupees", 
        "DETERGENT POWDER with price less than 10 rupees", 
        "Gold Massage less than 150 rupees"]
nlp = spacy.load("en_core_web_lg")
MONEY = nlp.vocab.strings['MONEY']

def add_money_ent(matcher, doc, i, matches):
    match_id, start, end = matches[i]
    doc.ents += ((MONEY, start, end),)
    
def print_results(small):
    for i in small:
        if i: 
            for a in i:
                print(a, end=', ')
                    
def clean_noun(d):    
    nouns = []
    for chunk in d.noun_chunks:
        if chunk.root.text != "rupees":
            nouns.append(chunk)
    return nouns  

def filter_spans(spans):
    # Filter a sequence of spans so they don't contain overlaps
    get_sort_key = lambda span: (span.end - span.start, -span.start)
    sorted_spans = sorted(spans, key=get_sort_key, reverse=True)
    result = []
    seen_tokens = set()
    for span in sorted_spans:
        # Check for end - 1 here because boundaries are inclusive
        if span.start not in seen_tokens and span.end - 1 not in seen_tokens:
            result.append(span)
        seen_tokens.update(range(span.start, span.end))
    result = sorted(result, key=lambda span: span.start)
    return result

def extract_currency_relations(doc):
    noun_chunk = clean_noun(doc)
    spans = list(doc.ents) + noun_chunk
    spans = filter_spans(spans)
    with doc.retokenize() as retokenizer:
        for span in spans:
            retokenizer.merge(span)
    relations = []
    for money in filter(lambda w: w.ent_type_ == "MONEY", doc):
        for i in money.children:
            if money.dep_ in ("appos", "npadvmod", "nsubj", "conj"):
                relations.append((money.head, i, money))
            elif money.dep_ in ("pobj", "dobj"):
                relations.append((money.head, i, money))
    return relations    

def main():
    print("Processing %d texts" % len(TEXTS))
    df = pd.read_excel('Train-Data.xlsx')
    for text in TEXTS:
        print('\n')
        print(text)
        text_split = text.split()
        if len(text_split) < 4:
            for sen in df["Description"]:
                if all(map(lambda word: word in sen.lower(), text_split)):
                    print(sen)
        doc = nlp(text)
        matcher = Matcher(nlp.vocab)
        matcher.add("MONEY", add_money_ent, [{'LIKE_NUM': True}, {'LOWER': "rupees"}])
        matcher(doc)
        relations = extract_currency_relations(doc)
        for r1, r2, r3 in relations:
            des = r1.orth_.split()  
            print(des)          
            if r2.text == 'less than':
                mon = r3.orth_.split()
                for i in mon:
                    if i.isdigit():
                        lis = int(i)
                        d = df.query('Selling_Price <= @lis')
                        small=  d["Description"].str.findall('.*?'+'.*'.join(des)+'.*', re.I)
                        print_results(small)

if __name__ == "__main__":
    main()
    