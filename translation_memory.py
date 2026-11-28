"""Opt-in local translation memory and research corpus; never uploads data."""
from __future__ import annotations
import json
import queue
import re
import sqlite3
import threading
import time
import os
import tempfile
import zipfile
from collections import OrderedDict
from pathlib import Path
from protected_chat import technical_fragments

MAX_ROWS=10000
MAX_CACHE=3000
TTL=7*86400
RETENTION=30*86400
PRIVATE=re.compile(r"https?://|www\.|(?:\d{1,3}\.){3}\d{1,3}|[\w.+-]+@[\w.-]+\.\w+|(?<!\w)@[\w.-]+|(?:\+?\d[\s().-]*){7,}|(?:password|passwd|rcon_password|ui_pwlogin|token|api[_ -]?key|парол[ьяі]|телефон|email|e-mail)\b",re.I)
def clean(text, nick=""):
    text=str(text or "").strip()
    if nick: text=re.sub(re.escape(nick), "[player]", text, flags=re.I) if len(nick)>=3 else text
    if not text or len(text)>240 or PRIVATE.search(text) or technical_fragments(text) or any(ord(c)<32 for c in text):
        return None
    return text

def initialize_schema(db):
    db.execute("CREATE TABLE IF NOT EXISTS cache(k TEXT PRIMARY KEY,v TEXT NOT NULL,ts REAL NOT NULL)")
    db.execute("""CREATE TABLE IF NOT EXISTS observations(
         id INTEGER PRIMARY KEY, direction TEXT, source TEXT, target TEXT, style TEXT,
         original TEXT, translated TEXT, outcome TEXT, provider TEXT, elapsed_ms INTEGER,
         context TEXT, last_seen INTEGER, count INTEGER DEFAULT 1,
         UNIQUE(direction,source,target,style,original,translated,outcome,provider))""")
    db.execute("CREATE TABLE IF NOT EXISTS timings(id INTEGER PRIMARY KEY,direction TEXT,provider TEXT,outcome TEXT,elapsed_ms INTEGER,ts INTEGER)")

class LocalExperience:
    """One disk thread, bounded queue, small in-memory exact cache."""
    def __init__(self, path:Path, collect=False, cache=False, exporter=None):
        self.exporter = exporter
        self.path=path
        self.collect=bool(collect)
        self.cache=bool(cache)
        self._cache=OrderedDict()
        self._lock=threading.Lock()
        self.jobs=queue.Queue(maxsize=256)
        self.closed=False
        self.error=None
        self.dropped=0
        self._generation=0
        self.thread=threading.Thread(target=self._run,daemon=True,name="LocalExperience")
        self.thread.start()
    def set_options(self, collect, cache):
        with self._lock:
            self.collect=bool(collect)
            self.cache=bool(cache)
            if not self.cache: self._cache.clear()
        if cache: self._submit(("load",))
    def _submit(self,job):
        if self.closed: return False
        try:
            self.jobs.put_nowait(job); return True
        except queue.Full:
            self.dropped+=1; return False
    def get(self,key):
        with self._lock:
            if not self.cache: return None
            row=self._cache.get(key)
            if not row: return None
            value,ts=row
            if time.time()-ts>TTL:
                self._cache.pop(key,None); return None
            self._cache.move_to_end(key)
            return value
    def save(self,key,value,nick=""):
        # Key is version/direction/source/target/style/text; exact source only.
        if not clean(key[-1]) or not clean(value): return
        if nick and len(nick)>=3 and (nick.casefold() in key[-1].casefold() or nick.casefold() in value.casefold()): return
        with self._lock:
            if not self.cache: return
            now=time.time(); self._cache[key]=(value,now); self._cache.move_to_end(key)
            while len(self._cache)>MAX_CACHE: self._cache.popitem(last=False)
            generation=self._generation
        self._submit(("save",generation,key,value,now))
    def record(self,direction,source,target,style,text,translated,outcome,provider,elapsed_ms,context=(),nick=""):
        with self._lock:
            if not self.collect: return
            generation=self._generation
        elapsed=max(0,min(120000,int(elapsed_ms)))
        metric=(direction,str(provider)[:40],outcome,elapsed,int(time.time()))
        original=clean(text,nick)
        if original is None:
            self._submit(("metric",generation,metric));return
        value=clean(translated,nick) if translated else ""
        if value is None:
            self._submit(("metric",generation,metric));return
        previous=[v for x in context[-2:] if (v:=clean(x,nick)) is not None]
        # No names, server IDs, log paths, system information or credentials.
        row=(direction,source,target,style,original,value,outcome,str(provider)[:40],
             elapsed,json.dumps(previous,ensure_ascii=False),int(time.time()))
        self._submit(("record",generation,row,metric))
    def record_ui_lag(self, elapsed_ms):
        """One cheap, content-free timing sample per UI sampling interval."""
        with self._lock:
            if not self.collect:return
            generation=self._generation
        elapsed=max(0,min(120000,int(elapsed_ms)))
        self._submit(("metric",generation,("ui","tk-main-loop","ok",elapsed,int(time.time()))))

    def export(self,path,callback, *, with_counts=False):
        return self._submit(("export",Path(path),with_counts,callback))
    def clear(self,callback):
        with self._lock:
            if self.closed:return False
            # Queue clear before accepting new rows. Already queued rows are applied
            # then removed; no generation from before clear survives afterward.
            if not self._submit(("clear",callback)):return False
            self._generation+=1; self._cache.clear()
            return True
    def stats(self,callback):
        return self._submit(("stats",callback))
    def close(self):
        self.closed=True
        # Allow the disk worker to release its SQLite handle before a caller
        # tears down a temporary or portable settings directory on Windows.
        # This runs only during shutdown, never on the translation path.
        self.thread.join(timeout=3.0)
    def _load(self,db):
        rows=db.execute("SELECT k,v,ts FROM cache WHERE ts>=? ORDER BY ts",(time.time()-TTL,)).fetchall()
        with self._lock:
            if not self.cache:return
            for k,v,ts in rows:
                try:
                    key=tuple(json.loads(k))
                    if len(key)==6 and clean(key[-1]) and clean(v): self._cache.setdefault(key,(v,ts))
                except (ValueError,TypeError): pass
            while len(self._cache)>MAX_CACHE:self._cache.popitem(last=False)
    def _prune(self,db):
        db.execute("DELETE FROM cache WHERE ts<?",(time.time()-TTL,))
        db.execute("DELETE FROM cache WHERE k IN (SELECT k FROM cache ORDER BY ts DESC LIMIT -1 OFFSET ?)",(MAX_CACHE,))
        db.execute("DELETE FROM observations WHERE last_seen<?",(time.time()-RETENTION,))
        db.execute("DELETE FROM observations WHERE id IN (SELECT id FROM observations ORDER BY last_seen DESC,id DESC LIMIT -1 OFFSET ?)",(MAX_ROWS,))
        db.execute("DELETE FROM timings WHERE ts<?",(time.time()-RETENTION,))
        db.execute("DELETE FROM timings WHERE id IN (SELECT id FROM timings ORDER BY id DESC LIMIT -1 OFFSET 4096)")
    def _run(self):
        db=None
        writes=0
        try:
            # When opt-ins are off, don't create a database until requested.
            while not self.closed or not self.jobs.empty():
                try: job=self.jobs.get(timeout=.1)
                except queue.Empty:
                    if db is not None: db.commit()
                    continue
                try:
                    op=job[0]
                    if db is None:
                        self.path.parent.mkdir(parents=True,exist_ok=True)
                        db=sqlite3.connect(self.path,timeout=1)
                        db.execute("PRAGMA journal_mode=WAL")
                        db.execute("PRAGMA synchronous=NORMAL")
                        db.execute("PRAGMA secure_delete=ON")
                        db.execute("PRAGMA max_page_count=8192")
                        db.execute("PRAGMA wal_autocheckpoint=256")
                        initialize_schema(db)
                        self._prune(db);self._load(db)
                    if op=="load": self._load(db)
                    elif op=="save":
                        _,gen,key,value,ts=job
                        if gen!=self._generation or not self.cache: continue
                        db.execute("INSERT OR REPLACE INTO cache VALUES(?,?,?)",(json.dumps(key,ensure_ascii=False),value,ts))
                        writes+=1
                    elif op=="metric":
                        _,gen,metric=job
                        if gen!=self._generation or not self.collect:continue
                        db.execute("INSERT INTO timings(direction,provider,outcome,elapsed_ms,ts) VALUES(?,?,?,?,?)",metric);writes+=1
                    elif op=="record":
                        _,gen,row,metric=job
                        if gen!=self._generation or not self.collect: continue
                        db.execute("INSERT INTO timings(direction,provider,outcome,elapsed_ms,ts) VALUES(?,?,?,?,?)",metric)
                        db.execute("""INSERT INTO observations(direction,source,target,style,original,translated,outcome,provider,elapsed_ms,context,last_seen)
                        VALUES(?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(direction,source,target,style,original,translated,outcome,provider)
                        DO UPDATE SET count=count+1, elapsed_ms=excluded.elapsed_ms, context=excluded.context, last_seen=excluded.last_seen""",row)
                        writes+=1
                    elif op=="clear":
                        db.execute("DELETE FROM observations");db.execute("DELETE FROM cache");db.execute("DELETE FROM timings");db.commit()
                        db.execute("PRAGMA wal_checkpoint(TRUNCATE)");db.execute("VACUUM")
                        job[1](True,"")
                    elif op=="stats":
                        self._prune(db);db.commit()
                        counts=db.execute("SELECT count(*),coalesce(sum(count),0) FROM observations").fetchone()
                        job[1](True,(*counts,self._metrics(db)))
                    elif op=="export":
                        _,destination,with_counts,callback=job
                        self._prune(db);db.commit()
                        count = self._export(db,destination)
                        callback(True,(str(destination),count) if with_counts else str(destination))
                    if writes>=32 or op in ("load","stats","clear","export"):
                        self._prune(db);db.commit();writes=0
                except Exception as exc:
                    self.error=type(exc).__name__
                    if job[0] in ("export","stats","clear"):
                        job[-1](False,self.error)
                    if db is not None: db.rollback()
                finally: self.jobs.task_done()
        except Exception as exc:
            self.error=type(exc).__name__
        finally:
            if db is not None:
                try:self._prune(db);db.commit()
                finally:db.close()
    def _metrics(self,db):
        grouped={}
        for direction,provider,outcome,elapsed in db.execute("SELECT direction,provider,outcome,elapsed_ms FROM timings ORDER BY id"):
            for group in (direction,direction+"/"+provider):
                slot=grouped.setdefault(group,{"values":[],"failed":0})
                slot["values"].append(elapsed)
                slot["failed"]+=int(outcome!="ok")
        result={}
        for group,slot in grouped.items():
            v=sorted(slot["values"])
            result[group]={"samples":len(v),"failed":slot["failed"],"p50_ms":v[round((len(v)-1)*.5)],"p95_ms":v[round((len(v)-1)*.95)]}
        return result

    def _export(self,db,destination):
        # Explicit manual export only. No cache, raw logs, file paths, timestamps
        # or device IDs in the archive. Free text may still contain identifiers.
        cursor=db.execute("SELECT direction,source,target,style,original,translated,outcome,provider,elapsed_ms,context,count FROM observations ORDER BY count DESC,id DESC LIMIT ?",(MAX_ROWS,))
        keys=("direction","source_language","target_language","style","original","translation","outcome","provider","elapsed_ms","context","count")
        fd, name = tempfile.mkstemp(dir=destination.parent)
        os.close(fd)
        temp = Path(name)
        try:
            count=0
            with zipfile.ZipFile(temp,"w",compression=zipfile.ZIP_DEFLATED) as archive:
                with archive.open("examples.jsonl","w") as data:
                    for row in cursor:
                        item=dict(zip(keys,row))
                        if not clean(item["original"]) or (item["translation"] and not clean(item["translation"])):continue
                        item["context"]=[x for x in json.loads(item["context"]) if clean(x)]
                        data.write((json.dumps(item,ensure_ascii=False)+"\n").encode("utf-8"));count+=1
                archive.writestr("metrics.json",json.dumps(self._metrics(db),ensure_ascii=False,indent=2))
                archive.writestr("manifest.json",json.dumps({"schema":1,"exporter":self.exporter() if self.exporter else {},"examples":count,"dropped":self.dropped,"label":"unverified translation observations; review before sharing"},ensure_ascii=False,indent=2))
            if os.name == "nt":
                os.rename(temp, destination)  # Fails if the destination already exists.
            else:
                os.link(temp, destination)
            return count
        finally:
            if temp.exists():temp.unlink()

RUNTIME:LocalExperience|None=None
def configure(runtime):
    global RUNTIME
    RUNTIME=runtime
    if runtime and (runtime.cache or runtime.path.exists()):runtime._submit(("load",))
def cache_key(version,direction,source,target,style,text):
    return (version,direction,source,target,style,text)
