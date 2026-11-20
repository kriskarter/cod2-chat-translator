"""Bounded, versioned data-only gaming phrases. No remote code or paid LLM."""
from __future__ import annotations
import json
import re
import threading
from pathlib import Path
import requests

UPDATE_URL = "https://raw.githubusercontent.com/kriskarter/cod2-chat-translator/knowledge-v2/assets/knowledge_v2.json"
MAX_BYTES = 1024 * 1024
LANGS = frozenset(("ru","uk","en","pl","de","fr","es","tr","cs","sk","it","pt"))
_CONTROL = re.compile(r"[\x00-\x1f\x7f]")
def key(text):
    return re.sub(r"\s+", " ", text.strip().casefold().replace("’", "'")).rstrip(".!")

def text_field(v):
    if not isinstance(v,str) or not v.strip() or len(v)>240 or _CONTROL.search(v):
        raise ValueError("invalid phrase")
    return v.strip()

class KnowledgePack:
    def __init__(self, raw):
        if not isinstance(raw,dict) or set(raw)!={"schema","version","entries"} or raw["schema"]!=1 or type(raw["version"]) is not int or not 1<=raw["version"]<=100000:
            raise ValueError("bad knowledge schema")
        entries=raw["entries"]
        if not isinstance(entries,list) or not 1<=len(entries)<=10000:
            raise ValueError("invalid entries")
        self.version=raw["version"]
        self.count=len(entries)
        self.index={}
        ids=set()
        for e in entries:
            if not isinstance(e,dict) or set(e)!={"id","forms","translations"} or not isinstance(e["id"],str) or not re.fullmatch(r"[a-z0-9_-]{1,80}",e["id"]) or e["id"] in ids:
                raise ValueError("invalid entry")
            ids.add(e["id"])
            forms,trans=e["forms"],e["translations"]
            if not isinstance(forms,dict) or not isinstance(trans,dict) or not forms or not trans or not set(forms).issubset(LANGS) or not set(trans).issubset(LANGS):
                raise ValueError("invalid languages")
            translations={l:text_field(t) for l,t in trans.items()}
            for l, variants in forms.items():
                if not isinstance(variants,list) or not 1<=len(variants)<=100:
                    raise ValueError("invalid forms")
                for v in variants:
                    k=key(text_field(v))
                    if not k: raise ValueError("empty key")
                    bucket=self.index.setdefault(k,[])
                    row=(l,translations)
                    if row not in bucket: bucket.append(row)
    @classmethod
    def from_bytes(cls, data):
        if len(data)>MAX_BYTES: raise ValueError("pack too large")
        return cls(json.loads(data.decode("utf-8")))
    def lookup(self,text,target,source="auto"):
        entries=self.index.get(key(text),())
        found={t[target] for l,t in entries if target in t and l!=target and (source=="auto" or l==source)}
        if source=="auto" and any(l==target for l,_ in entries): return None
        if len(found)!=1: return None
        return next(iter(found))

def template(text,target,source="auto"):
    t=key(text)
    if target not in ("en","ru","uk"): return None
    for lang, pattern in (
        ("en",r"(enemy|enemies) at ([ab])"),
        ("ru",r"(враг|враги) на ([ab])"),
        ("uk",r"(ворог|вороги) на ([ab])"),
    ):
        if source not in ("auto",lang) or target==lang: continue
        m=re.fullmatch(pattern,t)
        if m:
            plural=m[1] in ("enemies","враги","вороги")
            out={"en":("Enemies at " if plural else "Enemy at "),"ru":("Враги на " if plural else "Враг на "),"uk":("Вороги на " if plural else "Ворог на ")}[target]
            return out+m[2].upper()
    m=re.fullmatch(r"(\d{1,3})\s*(hp|хп)",t)
    if m and ((m[2]=="hp" and source in ("auto","en")) or (m[2]=="хп" and source in ("auto","ru","uk"))):
        return m[1]+(" HP" if target=="en" else " ХП")
    for lang,pattern in (
        ("ru",r"(?:kto na|кто на) ([ab])\?"),
        ("uk",r"(?:khto na|хто на) ([ab])\?"),
        ("en",r"(?:who is at|who's at) ([ab])\?"),
    ):
        if source not in ("auto",lang) or target==lang: continue
        m=re.fullmatch(pattern,t)
        if m: return {"en":"Who is at ","ru":"Кто на ","uk":"Хто на "}[target]+m[1].upper()+"?"
    # Commands and counts: exact grammar with a validated slot, not
    # arbitrary fuzzy replacements. Distinguish enemy count and direction.
    mappings=(
        ("en",r"hold ([ab])",{"ru":"Держи ","uk":"Тримай "}),
        ("en",r"rush ([ab])",{"ru":"Атакуй ","uk":"Атакуй "}),
        ("en",r"go ([ab])",{"ru":"Иди на ","uk":"Іди на "}),
        ("en",r"don'?t go ([ab])",{"ru":"Не ходи на ","uk":"Не йди на "}),
        ("ru",r"держи ([ab])",{"en":"Hold ","uk":"Тримай "}),
        ("uk",r"тримай ([ab])",{"en":"Hold ","ru":"Держи "}),
        ("ru",r"(?:иди|беги) на ([ab])",{"en":"Go to ","uk":"Іди на "}),
        ("uk",r"іди на ([ab])",{"en":"Go to ","ru":"Иди на "}),
        ("ru",r"не ходи на ([ab])",{"en":"Don't go to ","uk":"Не йди на "}),
        ("uk",r"не йди на ([ab])",{"en":"Don't go to ","ru":"Не ходи на "}),
        ("ru",r"prikroi ([ab])",{"en":"Cover ","uk":"Прикрий "}),
        ("ru",r"держи point ([ab])",{"en":"Hold point ","uk":"Тримай точку "}),
        ("en",r"cover ([ab])",{"ru":"Прикрой ","uk":"Прикрий "}),
    )
    for lang,pattern,results in mappings:
        if source not in ("auto",lang) or target not in results:continue
        m=re.fullmatch(pattern,t)
        if m:return results[target]+m[1].upper()
    m=re.fullmatch(r"([1-9]\d?) (enemy|enemies) at ([ab])",t)
    if m and source in ("en","auto") and target in ("ru","uk"):
        n=int(m[1])
        if (n==1)!=(m[2]=="enemy"):return None
        if target=="ru":
            noun="враг" if n%10==1 and n%100!=11 else ("врага" if n%10 in (2,3,4) and n%100 not in (12,13,14) else "врагов")
        else:
            noun="ворог" if n%10==1 and n%100!=11 else ("вороги" if n%10 in (2,3,4) and n%100 not in (12,13,14) else "ворогів")
        return f"{n} {noun} на {m[3].upper()}"
    return None

class KnowledgeRuntime:
    def __init__(self,bundled:Path,installed:Path):
        self.bundled=bundled
        self.installed=installed
        self._lock=threading.Lock()
        self.pack=KnowledgePack.from_bytes(bundled.read_bytes())
        self.enabled=True
        if installed.exists():
            try:
                if installed.stat().st_size>MAX_BYTES: raise ValueError("pack too large")
                candidate=KnowledgePack.from_bytes(installed.read_bytes())
                if candidate.version>self.pack.version: self.pack=candidate
            except (OSError,ValueError,TypeError,KeyError,RecursionError): pass
    @property
    def version(self): return self.pack.version
    def lookup(self,text,target,source="auto",style="live"):
        if not self.enabled: return None
        result=self.pack.lookup(text,target,source) or template(text,target,source)
        if result and text.rstrip().endswith("!") and not result.endswith("!"): result+="!"
        return result
    def refresh(self, getter=None):
        getter=getter or requests.get
        with getter(UPDATE_URL,timeout=(2,4),stream=True,allow_redirects=False) as response:
            if response.status_code!=200: raise RuntimeError("knowledge HTTP "+str(response.status_code))
            data=bytearray()
            for block in response.iter_content(16384):
                data.extend(block)
                if len(data)>MAX_BYTES: raise ValueError("pack too large")
        candidate=KnowledgePack.from_bytes(bytes(data))
        with self._lock:
            if candidate.version<=self.pack.version: return False
            self.installed.parent.mkdir(parents=True,exist_ok=True)
            temp=self.installed.with_suffix(".tmp")
            temp.write_bytes(data)
            temp.replace(self.installed)
            self.pack=candidate
        return True

RUNTIME: KnowledgeRuntime|None=None
def configure(runtime):
    global RUNTIME
    RUNTIME=runtime
def version():
    return RUNTIME.version if RUNTIME and RUNTIME.enabled else 0
def lookup(text,target,source="auto",style="live"):
    return RUNTIME.lookup(text,target,source,style) if RUNTIME else None
