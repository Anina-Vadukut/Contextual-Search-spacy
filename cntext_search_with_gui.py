import pandas as pd
import re
import spacy
from tkinter import ttk
import tkinter
import en_core_web_md
from spacy.pipeline import EntityRuler

nlp = spacy.load('en_core_web_md')
MONEY = nlp.vocab.strings['MONEY']

class MyWindow:
    def __init__(self, win):
        self.lbl = Label(win, text='Results', font='ariel 12 bold', bg='#856ff8')
        self.t1 = Entry(bd=3)
        self.t2 = Text(window, width=10)
        self.b1 = ttk.Button(win, text='Search', command=self.add)
        self.btn = ttk.Button(win, text='Delete', command=lambda: self.t2.delete(1.0, END))
        self.t1.place(x=200, y=50, width=250)   
        self.b1.place(x=460, y=50)
        self.lbl.place(x=200, y=175)
        self.t2.place(x=200, y=200, width=500)      
        self.btn.place(x=400, y=600)

    def clean_noun(self, doc):    
        nouns = []
        for chunk in doc.noun_chunks:
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
            if money.children:
                for child in money.children:
                    if money.dep_ in ("appos", "npadvmod", "nsubj", "conj"):
                        relations.append((money.head, child, money))
                    elif money.dep_ in ("pobj", "dobj"):
                        relations.append((money.head.head, money.head, money))
            if money.dep_ in "pobj":
                relations.append((money.head.head, money.head, money))
        return relations    

    def add(self):
        """Searches for input text from table 
        """
        text = self.t1.get()
        df = pd.read_excel('Train-Data.xlsx')
        text_split = text.split()
        if len(text_split) < 4:
            for sen in df["Description"]:
                if all(map(lambda word: word in sen.lower(), text_split)):
                    self.t2.insert(END, sen + '\n')   
            
        if 'entity_ruler' not in nlp.pipe_names:
            ruler = EntityRuler(nlp, overwrite_ents="True")
            patterns = [{"label": "MONEY", "pattern": [{'LIKE_NUM': True}, {"LOWER": "rupees"}]}]
            ruler.add_patterns(patterns)
            nlp.add_pipe(ruler, after="ner")
            
        doc = nlp(text)
        relations = self.extract_currency_relations(doc)
        for r1, r2, r3 in relations:
            des = r1.orth_.split()
            mon = r3.orth_.split()  
            lis = next(int(val) for val in mon if val.isdigit())
            less_list = ['less', 'under', 'below']
            if r2.text in less_list:
                df_new = df.query('Selling_Price < @lis')
                small = df_new["Description"].str.findall('.*?'+'.*'.join(des)+'.*', re.I)
                for line in small:
                    if line: 
                        self.t2.insert(END, *line)
                        self.t2.insert(END, '\n')

window = Tk()
mywin = MyWindow(window)
window['background'] = '#856ff8'
window.title('Contextual Search')
window.geometry("800x800+10+10")
window.mainloop()    
