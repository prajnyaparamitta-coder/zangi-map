"""動画IDを YouTube Data API（videos.list）で取り直し、data/videos.json に結果と日付を書く。

GitHub Actions から週1回動く。API キーは環境変数 YOUTUBE_API_KEY から読む（ファイルには書かない）。
YouTube API サービスのデベロッパー ポリシー III.E.4.d（30日ごとの削除か更新）と
III.E.4.e（YouTube 側と食い違わないようにする）に合わせるための処理。
"""
import datetime
import json
import os
import sys
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOPS = os.path.join(ROOT, "data", "shops.json")
VIDEOS = os.path.join(ROOT, "data", "videos.json")
JST = datetime.timezone(datetime.timedelta(hours=9))


def main():
    key = os.environ.get("YOUTUBE_API_KEY", "").strip()
    if not key:
        sys.exit("YOUTUBE_API_KEY が設定されていません（GitHub の Secrets を確かめてください）")
    shops = json.load(open(SHOPS, encoding="utf-8"))["shops"]
    ids = sorted({v for s in shops for v in s["videos"]})
    today = datetime.datetime.now(JST).date().isoformat()
    result = {}
    for i in range(0, len(ids), 50):          # 1回で50本まで。1回1単位
        chunk = ids[i:i + 50]
        url = "https://www.googleapis.com/youtube/v3/videos?" + urllib.parse.urlencode(
            {"part": "status", "id": ",".join(chunk), "key": key, "maxResults": 50})
        with urllib.request.urlopen(url, timeout=30) as r:
            items = json.load(r).get("items", [])
        found = {it["id"]: it["status"] for it in items}
        for vid in chunk:
            st = found.get(vid)
            if st is None:
                result[vid] = {"checked_on": today, "ok": False, "reason": "削除されたか非公開"}
                continue
            reasons = []
            if st.get("privacyStatus") != "public":
                reasons.append("公開されていない")
            if not st.get("embeddable", False):
                reasons.append("埋め込みが止められている")
            if st.get("madeForKids", False):
                reasons.append("子ども向けの動画")
            result[vid] = {"checked_on": today, "ok": not reasons, "reason": "・".join(reasons)}
    with open(VIDEOS, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")
    bad = {k: v for k, v in result.items() if not v["ok"]}
    print(f"{len(result)}本を取り直した（{today}）。使えない動画：{len(bad)}本")
    for k, v in bad.items():
        print(f"  {k}: {v['reason']}")


if __name__ == "__main__":
    main()
