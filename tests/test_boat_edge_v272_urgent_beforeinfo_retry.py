#!/usr/bin/env python3
"""V272: offline pre-result urgent retry; no HTTP, result or payout access."""
import ast
import datetime as dt
from pathlib import Path
s=Path(".github/workflows/auto-update.yml").read_text(encoding="utf-8")
a=s.index("          urgent_beforeinfo={(j,rno)")
b=s.index("\n          before={}",a)
code="\n".join(line[10:] for line in s[a:b].splitlines())
ast.parse(code)
class Resp:
    def __init__(self, content): self.content=content; self.text=content.decode()
class FakeSoup:
    def __init__(self, text, parser): self.text=text
def parse_before(soup):
    return {"racers":[{"exhibition_time":6.5 if soup.text=="ready" else None}],"start_exhibition":[]}
class File:
    def __init__(self): self.data=None
    def write_bytes(self,b): self.data=b
class Raw:
    def __init__(self): self.files={}
    def __truediv__(self,name):
        if name not in self.files: self.files[name]=File()
        return self.files[name]
def scenario(targets,responses,protected=False):
    calls=[]; sleeps=[]; raw=Raw()
    def fetch(url,attempts):
        calls.append(url)
        return Resp(responses.pop(0))
    env={"targets":targets,"ymd":"20261012","BASE":"https://www.boatrace.jp",
         "fetch":fetch,"RAW":raw,"BeautifulSoup":FakeSoup,"parse_before":parse_before,
         "sha":lambda b:"sha:"+b.decode(),
         "time":type("Time",(),{"sleep":lambda _,sec:sleeps.append(sec)})(),
         "protected_site_snapshot":lambda data,key:protected,"DATA":object(),
         "datetime":dt.datetime,"JST":dt.timezone(dt.timedelta(hours=9))}
    exec(compile(code,"<V272_OFFLINE>","exec"),env,env)
    return env["before_task"],calls,sleeps,raw
task,calls,sleeps,raw=scenario([("19",8,8)],[b"wait",b"ready"])
key,doc=task("19",8)
assert key=="20261012-19-08" and doc["status"]=="ok"
assert doc["urgent_retried"] is True and len(calls)==2 and sleeps==[2.0]
assert raw.files["19_08_beforeinfo.html"].data==b"ready"
assert doc["sha256"]=="sha:ready"
task,calls,sleeps,raw=scenario([("19",8,8)],[b"wait",b"wait"])
_,doc=task("19",8)
assert doc["status"]=="published_wait" and doc["urgent_retried"] is True
assert len(calls)==2 and raw.files["19_08_beforeinfo.html"].data==b"wait"
task,calls,sleeps,raw=scenario([("19",8,35)],[b"wait"])
_,doc=task("19",8)
assert doc["status"]=="published_wait" and doc["urgent_retried"] is False
assert len(calls)==1 and not sleeps
task,calls,sleeps,raw=scenario([("19",8,8)],[b"ready"])
_,doc=task("19",8)
assert doc["status"]=="ok" and doc["urgent_retried"] is False and len(calls)==1
# A frozen immutable source may be observed to decide readiness, but
# PRE_RESULT collection must not rewrite the original beforeinfo HTML.
task,calls,sleeps,raw=scenario([("19",8,8)],[b"wait",b"ready"],protected=True)
key,doc=task("19",8)
assert key=="20261012-19-08" and doc["status"]=="ok"
assert doc["urgent_retried"] is True and len(calls)==2 and sleeps==[2.0]
assert not raw.files, "Frozen source HTML must remain byte-identical"
assert '"beforeinfo_urgent_15m_retried"' in s
assert '"results_seen":False,"unlock":False,"scoring":False' in s
assert "race/result" not in code and "odds3t" not in code
print("V272_URGENT_BEFOREINFO_ONE_RETRY_NO_RESULT_PASS")
