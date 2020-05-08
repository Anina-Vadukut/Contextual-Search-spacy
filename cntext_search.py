import pandas as pd
import re
import spacy
from tkinter import ttk
from tkinter import *

from spacy.matcher import Matcher

nlp = spacy.load("en_core_web_sm")
MONEY = nlp.vocab.strings['MONEY']

class MyWindow:
    def __init__(self, win):
        self.lbl3=Label(win, text='Results', font = 'ariel 12 bold', bg='#856ff8')
        self.t1=Entry(bd=3)
        self.t3=Text(window,width=10)
        self.btn1 = Button(win, text='Search' )
        self.t1.place(x=200, y=50, width=250)
        self.b1=ttk.Button(win, text='Search', command=self.add)     
        self.b1.place(x=460, y=50)
        self.lbl3.place(x=200, y=175)
        self.t3.place(x=200, y=200,width=500)
        self.btn = ttk.Button(win, text='Delete', command=lambda: self.t3.delete(1.0,END))
        self.btn.place(x=400, y=600)

    def add_money_ent(self, matcher, doc, i, matches):
        match_id, start, end = matches[i]
        doc.ents += ((MONEY, start, end),)

    def clean_noun(self, d):    
        nouns = []
        for chunk in d.noun_chunks:
            if chunk.root.text != "rupees":
                nouns.append(chunk)
        return nouns  

    def filter_spans(self, spans):
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

    def extract_currency_relations(self, doc):
        noun_chunk = self.clean_noun(doc)
        spans = list(doc.ents) + noun_chunk
        spans = self.filter_spans(spans)
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

    def add(self):
            text=self.t1.get()
            df = pd.read_excel('Train-Data.xlsx')
            print('\n')
            text_split = text.split()
            if len(text_split) < 4:
                for sen in df["Description"]:
                    if all(map(lambda word: word in sen.lower(), text_split)):
                        result = sen
                        self.t3.insert(END, result + '\n')            
            doc = nlp(text)
            matcher = Matcher(nlp.vocab)
            matcher.add("MONEY", self.add_money_ent, [{'LIKE_NUM': True}, {'LOWER': "rupees"}])
            matcher(doc)
            relations = self.extract_currency_relations(doc)
            for r1, r2, r3 in relations:
                des = r1.orth_.split()          
                if r2.text == 'less than':
                    mon = r3.orth_.split()
                    for i in mon:
                        if i.isdigit():
                            lis = int(i)
                            d = df.query('Selling_Price <= @lis')
                            small=  d["Description"].str.findall('.*?'+'.*'.join(des)+'.*', re.I)
                            for i in small:
                                if i: 
                                    for a in i:
                                        print(a, end=', ')
                                        self.t3.insert(END, a + '\n')

window=Tk()
mywin=MyWindow(window)
window['background']='#856ff8'
window.title('Contextual Search')
window.geometry("800x800+10+10")
window.mainloop()    