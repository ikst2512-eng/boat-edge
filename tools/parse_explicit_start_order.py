#!/usr/bin/env python3
"""Extract a six-boat start-exhibition order ONLY when official HTML exposes
six explicit numeric boat labels in the start-exhibition table. Never infer
boat identity from lane colors, image order, ST, roster order, or frame number.
Read-only; callers must independently verify the source capture first.
"""
from html.parser import HTMLParser
import re

class Tables(HTMLParser):
    def __init__(self):
        super().__init__()
        self.depth=0
        self.current=None
        self.tables=[]
        self.row=None
        self.cell=None
    def handle_starttag(self,tag,attrs):
        if tag=="table":
            self.depth+=1
            if self.depth==1:self.current=[]
        if self.current is None:return
        if tag=="tr" and self.depth==1:self.row=[]
        if tag in ("th","td") and self.row is not None and self.depth==1:self.cell=[]
    def handle_data(self,data):
        if self.cell is not None:self.cell.append(data)
    def handle_endtag(self,tag):
        if tag in ("th","td") and self.cell is not None:
            self.row.append(" ".join("".join(self.cell).split()))
            self.cell=None
        if tag=="tr" and self.row is not None:
            self.current.append(self.row)
            self.row=None
        if tag=="table":
            if self.depth==1 and self.current is not None:
                self.tables.append(self.current)
                self.current=None
            self.depth=max(0,self.depth-1)

def parse_explicit_start_order(raw):
    try:
        html=raw.decode("utf-8")
    except (UnicodeDecodeError,AttributeError):
        return None
    tables=Tables()
    tables.feed(html)
    candidates=[]
    for rows in tables.tables:
        headings=[i for i,row in enumerate(rows) if len(row)>=3 and
                  row[:3]==["コース","並び","ST"]]
        for idx in headings:
            entries=rows[idx+1:idx+7]
            if len(entries)!=6:continue
            boats=[]
            for expected,row in enumerate(entries,1):
                if len(row)<3 or row[0]!=str(expected) or not re.fullmatch("[1-6]",row[1]):
                    break
                boats.append(int(row[1]))
            if len(boats)==6 and set(boats)==set(range(1,7)):
                candidates.append(boats)
    return candidates[0] if len(candidates)==1 else None
