"""Review a voluntarily exported experience ZIP offline. No network/upload."""
import argparse
import collections
import json
from pathlib import Path
import zipfile

def analyze(path):
    with zipfile.ZipFile(path) as archive:
        expected=("manifest.json","examples.jsonl","metrics.json")
        if set(archive.namelist())!=set(expected) or len(archive.namelist())!=len(expected):
            raise ValueError("Unexpected archive layout")
        for name in expected:
            if archive.getinfo(name).file_size>12*1024*1024:raise ValueError("Archive member too large")
        manifest=json.loads(archive.read("manifest.json").decode("utf-8"))
        if manifest.get("schema")!=1:raise ValueError("Unsupported schema")
        data=archive.read("examples.jsonl").decode("utf-8")
        rows=[json.loads(line) for line in data.splitlines() if line.strip()]
        if len(rows)>10000:raise ValueError("Too many records")
        metrics=json.loads(archive.read("metrics.json").decode("utf-8"))
    outcomes=collections.Counter()
    unknown=collections.Counter()
    for row in rows:
        count=row["count"]
        if type(count) is not int or not 1<=count<=100000000:raise ValueError("Invalid observation count")
        outcomes[row["direction"]+"/"+row["outcome"]]+=count
        if row["outcome"]!="ok":
            unknown[row["original"]]+=count
    return {"unique_records":len(rows),"outcomes":dict(outcomes),
            "timing_sample_summary":metrics,
            "repeat_failures":[{"phrase":phrase,"observations":n} for phrase,n in unknown.most_common(30)],
            "caveat":"Observed provider outputs are not verified translations. Review privacy and meaning before curating knowledge."}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("zip",type=Path)
    args=parser.parse_args()
    print(json.dumps(analyze(args.zip),ensure_ascii=False,indent=2))
if __name__=="__main__":main()
