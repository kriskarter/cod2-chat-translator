"""Qt-only nickname presence: evidence from completed UDP polling rounds."""
from __future__ import annotations

from dataclasses import dataclass
from html import escape
from functools import lru_cache
import re
import unicodedata

from server_monitor import color_runs

_MARKUP=re.compile(r"\^\^|\^[0-9]")

def display_name(raw):
    raw=str(raw)
    return _MARKUP.sub(lambda m:"^" if m.group()=="^^" else "",raw).strip()

def _key(raw):
    return unicodedata.normalize("NFC",display_name(raw)).casefold()

_cached_key=lru_cache(maxsize=4096)(_key)

def friend_key(raw):
    # Parse markup once; ^^1 is a literal ^1, not a color code.
    raw=str(raw)
    return _cached_key(raw) if len(raw)<=128 else _key(raw)

def _rich(raw):
    return "".join(f'<span style="color:{color}">{escape(part)}</span>' for part,color in color_runs(raw))

_cached_rich=lru_cache(maxsize=4096)(_rich)

def rich_name(raw):
    raw=str(raw)
    return _cached_rich(raw) if len(raw)<=128 else _rich(raw)

def valid_friend(raw):
    raw = str(raw).strip()
    if len(raw)>128 or any(unicodedata.category(c)=="Cc" for c in raw):
        return ""
    return raw if friend_key(raw) else ""

def normalize_friends(raw):
    result=[];seen=set()
    for value in raw if isinstance(raw,list) else []:
        if not isinstance(value,str): continue
        label=valid_friend(value); key=friend_key(label)
        if key and key not in seen:
            seen.add(key);result.append(label)
        if len(result)>=100: break
    return result

def qt_monitor_settings(raw):
    from server_monitor import load_settings
    data = raw if isinstance(raw,dict) else {}
    result=load_settings(data)
    result["friends"]=normalize_friends(data.get("friends",[]))
    for name in ("join","leave","move"):
        result["notify_"+name]=bool(data.get("notify_"+name,True))
    result["notify_sound"]=bool(data.get("notify_sound",False))
    return result

@dataclass(frozen=True)
class PresenceEvent:
    kind: str
    name: str
    old_address: str = ""
    new_address: str = ""

class PresenceTracker:
    """Track each nickname/server independently; do not infer departures from timeouts.

    Two consecutive successful rounds confirm changes. Initial/recovered observations
    silently establish a baseline. Simultaneous unambiguous removal/addition is a
    move; otherwise report only observed per-server changes, never player identity.
    """
    def __init__(self):
        self.baseline={}
        self.pending={}
        self.ambiguous=set()
        self.deferred={}
        self.latest={}
        self.addresses=set()
        self.friends={}
        self._cached_rows=None

    def configure(self, friends, addresses, *, reset=False):
        keys={friend_key(n):n for n in friends}
        addresses=set(addresses)
        if not reset and keys==self.friends and addresses==self.addresses: return
        self._cached_rows=None
        if reset:
            self.baseline.clear();self.pending.clear();self.ambiguous.clear();self.deferred.clear()
        self.baseline={k:v for k,v in self.baseline.items() if k[0] in keys and k[1] in addresses}
        self.pending={k:v for k,v in self.pending.items() if k[0] in keys and k[1] in addresses}
        self.ambiguous={k for k in self.ambiguous if k[0] in keys and k[1] in addresses}
        self.deferred={k:e for k,e in self.deferred.items() if k in keys and (e.old_address or e.new_address) in addresses}
        self.latest={a:s for a,s in self.latest.items() if a in addresses}
        for key in keys.keys()-self.friends.keys():
            for address,snapshot in self.latest.items():
                if snapshot.state=="online":
                    count=sum(friend_key(p.raw_name)==key for p in snapshot.players)
                    self.baseline[(key,address)] = bool(count)
                    if count>1: self.ambiguous.add((key,address))
        self.friends=keys; self.addresses=addresses

    def observe(self,snapshots):
        current={s.address:s for s in snapshots}
        if set(current)!=self.addresses: return []
        self.latest=current
        self._cached_rows=None
        # Index once per server, not once per nickname.
        from collections import Counter
        observed={a:(Counter(friend_key(p.raw_name) for p in s.players) if s.state=="online" else None)
                  for a,s in current.items()}
        events=[]
        for key,name in self.friends.items():
            before={a for a in self.addresses if self.baseline.get((key,a)) is True}
            was_ambiguous=any((key,a) in self.ambiguous for a in before)
            added=set();removed=set();unknown=set()
            for address,names in observed.items():
                pair=(key,address)
                if names is None:
                    self.baseline.pop(pair,None);self.pending.pop(pair,None);self.ambiguous.discard(pair);unknown.add(address)
                    continue
                present=key in names
                if names.get(key,0)>1: self.ambiguous.add(pair)
                if pair not in self.baseline:
                    self.baseline[pair]=present;self.pending.pop(pair,None)
                    continue
                if self.baseline[pair]==present:
                    self.pending.pop(pair,None);continue
                candidate,count=self.pending.get(pair,(present,0))
                count=count+1 if candidate==present else 1
                if count<2:
                    self.pending[pair]=(present,count);continue
                self.baseline[pair]=present;self.pending.pop(pair,None)
                if not present: self.ambiguous.discard(pair)
                (added if present else removed).add(address)
            after={a for a in self.addresses if self.baseline.get((key,a)) is True}
            # Only claim a move when the complete round shows one matching name
            # at a time and both source departure and destination arrival are confirmed.
            matching=sum(names.get(key,0) for names in observed.values() if names is not None)
            deferred=self.deferred.pop(key,None)
            if deferred:
                # Sequential server polls can place the two halves of a move
                # in adjacent rounds. Hold only when the opposite half was
                # already observed, and combine only on fresh confirmation.
                if not unknown and not was_ambiguous and matching==1:
                    if deferred.kind=="leave" and len(added)==1 and not removed:
                        destination=next(iter(added))
                        if destination!=deferred.old_address and len(after)==1:
                            events.append(PresenceEvent("move",name,deferred.old_address,destination))
                            continue
                    if deferred.kind=="join" and len(removed)==1 and not added:
                        origin=next(iter(removed))
                        if origin!=deferred.new_address and after=={deferred.new_address}:
                            events.append(PresenceEvent("move",name,origin,deferred.new_address))
                            continue
                events.append(deferred)
            if not unknown and not was_ambiguous and matching==1:
                if len(before)==len(after)==len(added)==len(removed)==1:
                    events.append(PresenceEvent("move",name,next(iter(removed)),next(iter(added))))
                    continue
                # Avoid a redundant leave+join if the other half is already
                # pending in the same round (one successful confirmation).
                candidates={a:v[0] for (k,a),v in self.pending.items() if k==key}
                if len(before)==1 and len(removed)==1 and not after and not added and sum(v is True for v in candidates.values())==1:
                    self.deferred[key]=PresenceEvent("leave",name,next(iter(removed)))
                    continue
                if len(before)==1 and len(added)==1 and len(after)==2 and not removed and sum(v is False for v in candidates.values())==1:
                    self.deferred[key]=PresenceEvent("join",name,"",next(iter(added)))
                    continue
            events.extend(PresenceEvent("leave",name,a) for a in sorted(removed))
            events.extend(PresenceEvent("join",name,"",a) for a in sorted(added))
        return events

    def rows(self):
        if self._cached_rows is not None: return self._cached_rows
        full=bool(self.addresses) and set(self.latest)==self.addresses and all(s.state=="online" for s in self.latest.values())
        by_name={key:[] for key in self.friends}
        for a,s in self.latest.items():
            if s.state!="online": continue
            for p in s.players:
                key=friend_key(p.raw_name)
                if key in by_name: by_name[key].append((s,p))
        result=[]
        for key,name in self.friends.items():
            hits=by_name[key]
            if hits:
                for s,p in hits:
                    result.append(dict(name=display_name(p.raw_name),rawName=p.raw_name,richName=rich_name(p.raw_name),
                        state="online",address=s.address,server=s.name or s.address,map=s.map_name or "—",
                        population=f"{s.clients}/{s.max_clients}" if s.clients is not None and s.max_clients is not None else "—",
                        ambiguous=len(hits)>1))
            else:
                result.append(dict(name=display_name(name),rawName=name,richName=rich_name(name),state="offline" if full else "unknown",
                    address="",server="—",map="—",population="—",ambiguous=False))
        self._cached_rows=sorted(result,key=lambda r:({"online":0,"unknown":1,"offline":2}[r["state"]],r["name"].casefold(),r["address"]))
        return self._cached_rows


def dump_qt_monitor_settings(settings):
    from server_monitor import dump_settings
    data=dump_settings(settings)
    data.update({key:bool(settings[key]) for key in ("notify_join","notify_leave","notify_move","notify_sound")})
    return data
