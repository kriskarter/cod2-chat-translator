"""Deterministic offline comparison with simulated 50 ms MT, NOT live/game accuracy."""
from pathlib import Path
import json
import sys
import tempfile
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import knowledge_v2
from smart_engine import SmartTranslationEngine, TranslationRequest
from app import gaming_slang_transform
ROOT=Path(__file__).resolve().parents[1]
# Authored reference cases. The same ideal mocked provider is used in all modes,
# therefore correctness is a regression on these examples, not online MT accuracy.
CASES=[
("gg","ru","en","хорошая игра",("хорошая игра","отличная игра")),
("cover me","ru","en","прикрой меня",("прикрой меня",)),
("gg wp","ru","en","хорошая игра, хорошо сыграно",("хорошая игра, хорошо сыграно",)),
("hes low af","ru","en","у него очень мало хп",("у него очень мало хп",)),
("u laggin bro?","ru","en","бро у тебя лагает?",("бро у тебя лагает?",)),
("enemy on the roof","ru","en","враг на крыше",("враг на крыше",)),
("prikroi menya","en","ru","cover me",("cover me",)),
("ща зайду сзади","en","ru","i'll come around from behind",("i'll come around from behind",)),
("прикрой меня я перезаряжаюсь","en","ru","cover me i'm reloading",("cover me i'm reloading",)),
("не пикай mid","en","ru","don't peek mid",("don't peek mid",)),
("где bomb?","en","ru","where is the bomb?",("where is the bomb?",)),
("3 enemies at B","ru","en","3 врага на B",("3 врага на b",)),
("21 enemies at A","uk","en","21 ворог на A",("21 ворог на a",)),
("кто на B?","en","ru","Who is at B?",("who is at b?",)),
("don't go B","ru","en","Не ходи на B",("не ходи на b",)),
("cześć wszystkim","ru","pl","привет всем",("привет всем",)),
("прикрой меня","de","ru","deck mich",("deck mich",)),
("watch the window","uk","en","стеж за вікном",("стеж за вікном",)),
("проверь углы","en","ru","check the corners",("check the corners",)),
("i think that player has a very strange connection","ru","en","думаю, у того игрока очень странное соединение",("думаю, у того игрока очень странное соединение",)),
("мы сегодня играем намного лучше чем вчера","en","ru","we are playing much better today than yesterday",("we are playing much better today than yesterday",)),
("please come back after the next match","ru","en","пожалуйста, вернись после следующего матча",("пожалуйста, вернись после следующего матча",)),
]
def pctl(v,p):
    v=sorted(v);return round(v[min(len(v)-1,round((len(v)-1)*p))],3)
def run(mode,runtime):
    engine=SmartTranslationEngine()
    knowledge_v2.configure(runtime if mode=="V2" else None)
    latencies=[];network=0;correct=0;local=0;unsafe=0
    for original,target,source,ref,accepted in CASES:
        def fake(*args):
            nonlocal network
            network+=1
            time.sleep(.05)
            return ref
        started=time.perf_counter()
        if mode=="Classic":
            prepared,direct=gaming_slang_transform(original,target,"live")
            output=direct if direct is not None else fake(prepared,target,source)
            is_local=direct is not None
            safe=True
        else:
            result=engine.translate(TranslationRequest(original,target,source_lang=source,direction="outgoing"),fake,gaming_slang_transform)
            output=result.text;safe=result.safe;is_local=result.provider!="online" and safe
        latencies.append((time.perf_counter()-started)*1000)
        correct+=int(safe and output.casefold() in accepted)
        unsafe+=int(not safe)
        local+=int(is_local)
    return {"cases":len(CASES),"reference_matches":correct,"local":local,"provider_calls":network,"abstained":unsafe,"p50_ms":pctl(latencies,.5),"p95_ms":pctl(latencies,.95)}
def main():
    with tempfile.TemporaryDirectory() as tmp:
        runtime=knowledge_v2.KnowledgeRuntime(ROOT/"assets/knowledge_v2.json",Path(tmp)/"pack.json")
        data={mode:run(mode,runtime) for mode in ("Classic","V1","V2")}
        knowledge_v2.configure(None)
        print(json.dumps(data,ensure_ascii=False,indent=2))
        print("Synthetic hand-authored reference set, ideal simulated provider, no game or live network measurement.")
        # V2 must not regress exact reference correctness against V1.
        if data["V2"]["reference_matches"]<data["V1"]["reference_matches"] or data["V2"]["local"]<=data["V1"]["local"] or data["V2"]["provider_calls"]>=data["V1"]["provider_calls"]:
            return 1
    return 0
if __name__=="__main__":raise SystemExit(main())
