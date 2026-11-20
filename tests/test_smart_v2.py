"""Offline V2 behavioral tests (not independent or live-game MT quality proof)."""
import json
import queue
import tempfile
import threading
import time
import unittest
import zipfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import knowledge_v2 as knowledge
import translation_memory as memory
from provider_health import ProviderHealth
from smart_engine import SmartTranslationEngine, TranslationRequest, ContextMessage, semantic_violations
from app import ChatMessage, ControlApp, gaming_slang_transform
from outgoing_chat import OutgoingChatController, translate_outgoing_text
PACK=Path(__file__).resolve().parents[1]/"assets"/"knowledge_v2.json"

class SmartV2Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.folder=Path(self.temp.name)
        self.runtime=knowledge.KnowledgeRuntime(PACK,self.folder/"pack.json")
        self.old=knowledge.RUNTIME
        self.old_memory=memory.RUNTIME
        knowledge.configure(self.runtime)
        memory.configure(None)
        self.engine=SmartTranslationEngine()
    def tearDown(self):
        knowledge.configure(self.old)
        memory.configure(self.old_memory)
        self.temp.cleanup()
    def translate(self,text,target,source="auto",**kwargs):
        return self.engine.translate(TranslationRequest(text,target,source_lang=source,**kwargs),
          provider=lambda *_:self.fail("local route unexpectedly contacted provider"),
          legacy_transform=gaming_slang_transform)

    def test_local_bilingual_chat_both_directions(self):
        for text,target,source,expected in (
            ("hes low af","ru","auto","у него очень мало хп"),
            ("не пикай mid","en","ru","don't peek mid"),
            ("prikroi menya","en","ru","cover me"),
            ("ща зайду сзади","en","ru","i'll come around from behind"),
            ("прикрой меня я перезаряжаюсь","en","ru","cover me i'm reloading"),
            ("u laggin bro?","ru","auto","бро у тебя лагает?"),
            ("cover me plz","uk","auto","прикрий мене"),
            ("cześć wszystkim","ru","auto","привет всем"),
            ("прикрой меня","de","ru","deck mich"),
            ("don't shoot","pl","en","nie strzelaj"),
        ):
            with self.subTest(text=text,target=target):
                result=self.translate(text,target,source)
                self.assertTrue(result.safe)
                self.assertEqual(result.text.casefold(),expected.casefold())
    def test_templates_preserve_count_target_negation(self):
        for text,target,source,expected in (
            ("3 enemies at B","ru","en","3 врага на B"),
            ("21 enemies at A","uk","en","21 ворог на A"),
            ("1hp","ru","en","1 ХП"),
            ("don't go B","ru","en","Не ходи на B"),
            ("кто на B?","en","ru","Who is at B?"),
            ("держи point A","en","ru","Hold point A"),
        ):
            with self.subTest(text=text,target=target):
                result=self.translate(text,target,source)
                self.assertEqual(result.text,expected)
                self.assertFalse(semantic_violations(text,result.text,target))
    def test_context_does_not_guess_other_speaker_or_unknown_low(self):
        result=self.translate("low","ru",context=(ContextMessage("his hp","Player",1),),nickname="Player")
        self.assertEqual(result.provider,"context-v2")
        self.assertTrue(result.used_context)
        for ctx,name in [((), "Player"),((ContextMessage("his hp","Other",1),),"Player")]:
            self.assertIsNone(self.engine.fast_lookup(TranslationRequest("low","ru",context=ctx,nickname=name)))
    def test_unknown_and_negation_not_rewritten(self):
        req=TranslationRequest("don't cover the bridge yet","ru",source_lang="en")
        self.assertIsNone(self.engine.fast_lookup(req))
        self.assertIsNone(self.runtime.lookup("cover me?","ru","en"))
        self.assertIsNone(self.runtime.lookup("nonexistentword","ru"))
        self.assertIsNone(self.runtime.lookup("cover me","ru","pl"))
    def test_disable_restores_v1(self):
        self.runtime.enabled=False
        self.assertIsNone(self.engine.fast_lookup(TranslationRequest("прикрой меня","en",source_lang="ru")))
        self.assertEqual(knowledge.version(),0)
    def test_v2_uses_legacy_styles(self):
        a=self.translate("wtf","ru",style="raw")
        b=self.translate("wtf","ru",style="clear")
        self.assertNotEqual(a.text,b.text)
    def test_pack_update_atomically_and_reject_downgrade(self):
        raw=json.loads(PACK.read_text(encoding="utf-8"))
        raw["version"]=2
        def getter(content):
            class Response:
                status_code=200
                def __enter__(self):return self
                def __exit__(self,*args):pass
                def iter_content(self,*args):yield content
            return lambda url,**kwargs: Response()
        self.assertTrue(self.runtime.refresh(getter(json.dumps(raw).encode())))
        self.assertEqual(self.runtime.version,2)
        self.assertEqual(knowledge.KnowledgeRuntime(PACK,self.folder/"pack.json").version,2)
        self.assertFalse(self.runtime.refresh(getter(PACK.read_bytes())))
        with self.assertRaises(ValueError):
            self.runtime.refresh(getter(b'{"schema":99}'))
        self.assertEqual(self.runtime.version,2)
    def test_invalid_pack_and_ambiguous_alias(self):
        with self.assertRaises(ValueError): knowledge.KnowledgePack.from_bytes(b'a'*(knowledge.MAX_BYTES+1))
        raw={"schema":1,"version":1,"entries":[
            {"id":"x","forms":{"en":["abc"]},"translations":{"ru":"один"}},
            {"id":"y","forms":{"en":["abc"]},"translations":{"ru":"два"}}]}
        self.assertIsNone(knowledge.KnowledgePack(raw).lookup("abc","ru","en"))
    def test_f8_fast_path_bypasses_full_network_queue(self):
        controller=ControlApp.__new__(ControlApp)
        controller.enabled=True
        controller._f8_settings=("ru",False,True,"live",True,False)
        controller._arrival_context=__import__("collections").deque(maxlen=24)
        controller._chat_epoch=0
        controller.ui_queue=queue.Queue()
        controller.translation_jobs=queue.Queue(maxsize=1)
        controller.translation_jobs.put(ChatMessage("x","unknown"))
        controller.on_log_message(ChatMessage("Player", "enemy behind us"))
        event=controller.ui_queue.get_nowait()
        self.assertEqual(event[0],"translation")
        self.assertEqual(event[2],"враг у нас за спиной")
        self.assertEqual(controller.translation_jobs.qsize(),1)
        self.assertEqual(len(controller._arrival_context),1)
    def test_f9_offline_local_path_first(self):
        with patch("outgoing_chat.translate_with_google_fast", side_effect=AssertionError("network")) as google:
            result=translate_outgoing_text("ща зайду сзади","en","ru")
        self.assertEqual(result,"i'll come around from behind")
        google.assert_not_called()
    def test_provider_cooldown_is_bounded(self):
        health=ProviderHealth()
        with patch("provider_health.time.monotonic",return_value=100):
            health.failure(); self.assertFalse(health.prefer_backup())
            health.failure(); self.assertTrue(health.prefer_backup())
        with patch("provider_health.time.monotonic",return_value=111):
            self.assertFalse(health.prefer_backup())
        health.success()
        self.assertEqual(health.failures,0)
    def test_pack_directional_mappings_preserve_invariants(self):
        data=json.loads(PACK.read_text(encoding="utf-8"))
        failures=[]
        for entry in data["entries"]:
            for source, forms in entry["forms"].items():
                for form in forms:
                    for target, out in entry["translations"].items():
                        if target!=source:
                            errs=semantic_violations(form,out,target)
                            if errs:failures.append((entry["id"],form,target,errs))
        self.assertEqual(failures,[])

    def test_seed_pack_size_and_languages(self):
        self.assertGreaterEqual(self.runtime.pack.count,190)
        data=json.loads(PACK.read_text(encoding="utf-8"))
        self.assertGreaterEqual(sum(len(f) for e in data["entries"] for f in e["forms"].values()),950)
        self.assertTrue({"ru","uk","en","pl","de","fr","es","tr"}.issubset({l for e in data["entries"] for l in e["forms"]}))

class ExperienceTests(unittest.TestCase):
    def test_disabled_does_not_create_database(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"experience.sqlite3"
            store=memory.LocalExperience(path)
            store.record("incoming","en","ru","live","hello","привет","ok","Google",20)
            store.close()
            self.assertFalse(path.exists())
    def test_export_dedup_filter_and_persistent_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"experience.sqlite3"; out=Path(tmp)/"export.zip"
            store=memory.LocalExperience(path,collect=True,cache=True)
            key=memory.cache_key(1,"outgoing","ru","en","live","привет всем")
            store.save(key,"hello everybody")
            for i in range(2):
                store.record("incoming","en","ru","live","cover me, Player","прикрой меня","ok","Google",250,("where are you?",),nick="Player")
            store.record("incoming","en","ru","live","connect 127.0.0.1","no","ok","Google",1)
            store.record("incoming","en","ru","live","contact a@b.com","no","ok","Google",1)
            store.record("outgoing","ru","en","live","неизвестная фраза","","failed","offline",2100)
            done=threading.Event();result=[]
            self.assertTrue(store.export(out,lambda ok,data:(result.append(ok),done.set())))
            self.assertTrue(done.wait(3));self.assertEqual(result,[True])
            store.close()
            with zipfile.ZipFile(out) as z:
                self.assertEqual(set(z.namelist()),{"examples.jsonl","manifest.json","metrics.json"})
                raw=z.read("examples.jsonl").decode()
                rows=[json.loads(x) for x in raw.splitlines()]
                metrics=json.loads(z.read("metrics.json"))
                self.assertEqual(metrics["incoming"]["samples"],4)
                self.assertEqual(metrics["outgoing"]["failed"],1)
                self.assertEqual(len(rows),2)
                self.assertNotIn("Player",raw)
                self.assertNotIn("127.0.0.1",raw)
                self.assertNotIn("a@b.com",raw)
                self.assertEqual(next(r for r in rows if r["outcome"]=="ok")["count"],2)
            reopened=memory.LocalExperience(path,cache=True)
            try:
                reopened._submit(("load",));reopened.jobs.join()
                self.assertEqual(reopened.get(key),"hello everybody")
                done.clear();reopened.clear(lambda *_:done.set())
                self.assertTrue(done.wait(3)); self.assertIsNone(reopened.get(key))
            finally:reopened.close()
    def test_exact_cache_never_uses_other_language_or_style(self):
        with tempfile.TemporaryDirectory() as tmp:
            s=memory.LocalExperience(Path(tmp)/"db",cache=True)
            try:
                k=memory.cache_key(1,"incoming","auto","ru","live","hey team")
                s.save(k,"привет команда")
                self.assertIsNone(s.get(memory.cache_key(1,"incoming","auto","uk","live","hey team")))
                self.assertIsNone(s.get(memory.cache_key(2,"incoming","auto","ru","live","hey team")))
                self.assertIsNone(s.get(memory.cache_key(1,"incoming","auto","ru","raw","hey team")))
            finally:s.close()
