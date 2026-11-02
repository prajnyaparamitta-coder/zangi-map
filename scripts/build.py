"""data/ の JSON と templates/ の HTML から、公開用のページを docs/ に書き出す。

使い方：python3 scripts/build.py
（GitHub Actions でも同じコマンドが動く。Python の標準ライブラリだけで動く。）
"""
import datetime
import html
import json
import os
import shutil
import sys
from string import Template

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs")
JST = datetime.timezone(datetime.timedelta(hours=9))
MAX_AGE_DAYS = 30   # YouTube API のデータは30日を超えて持たない（デベロッパー ポリシー III.E.4.d）

e = html.escape


def load(name):
    with open(os.path.join(ROOT, "data", name), encoding="utf-8") as f:
        return json.load(f)


def template(name):
    with open(os.path.join(ROOT, "templates", name), encoding="utf-8") as f:
        return Template(f.read())


def write(path, text):
    full = os.path.join(OUT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(text)


def jdate(iso):
    y, m, d = iso.split("-")
    return f"{int(y)}年{int(m)}月{int(d)}日"


def json_for_script(obj):
    # <script type="application/json"> の中に安全に入れる
    return json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")


def main():
    site = load("site.json")
    areas = load("areas.json")["subprefectures"]
    shops = load("shops.json")["shops"]
    videos = load("videos.json") if os.path.exists(os.path.join(ROOT, "data", "videos.json")) else {}
    today = datetime.datetime.now(JST).date()

    sub_by_slug = {a["slug"]: a for a in areas}
    town_slug = {t["name"]: (a["slug"], t["slug"]) for a in areas for t in a["towns"]}

    # 使える動画だけを残す：週1回の取り直しで「使える」と確かめられ、確かめてから30日以内のもの
    warnings = []
    live = []
    for s in shops:
        ok = []
        for vid in s["videos"]:
            v = videos.get(vid)
            if not v:
                warnings.append(f"{s['name']}：動画 {vid} はまだ取り直していないので載せない")
                continue
            age = (today - datetime.date.fromisoformat(v["checked_on"])).days
            if not v["ok"]:
                warnings.append(f"{s['name']}：動画 {vid} は {v['reason']} なので外した")
            elif age > MAX_AGE_DAYS:
                warnings.append(f"{s['name']}：動画 {vid} は {age} 日取り直されていないので外した")
            else:
                ok.append(vid)
        if not ok:
            continue   # 動画が0本の店は、店ページごと外す
        if s["town"] not in town_slug or town_slug[s["town"]][0] != s["subprefecture"]:
            sys.exit(f"{s['name']} の市町村「{s['town']}」が data/areas.json にありません")
        s = dict(s, videos=ok)
        s["path"] = f"areas/{s['subprefecture']}/{s['town_slug']}/{s['slug']}/"
        live.append(s)

    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    shutil.copytree(os.path.join(ROOT, "assets"), os.path.join(OUT, "assets"))
    open(os.path.join(OUT, ".nojekyll"), "w").close()

    layout = template("layout.html")
    title = site["title"]

    def page(path, depth, page_title, body, *, nav="", description=None, maps=False, body_class=""):
        root = "../" * depth if depth else "./"
        head = ""
        scripts = ""
        if maps:
            head = f'<link rel="stylesheet" href="{root}assets/vendor/leaflet/leaflet.css">'
            scripts = (f'<script src="{root}assets/vendor/leaflet/leaflet.js"></script>\n'
                       f'<script src="{root}assets/js/map.js"></script>')
        navs = {k: "" for k in ("nav_top", "nav_areas", "nav_zangi", "nav_about")}
        if nav:
            navs[nav] = 'aria-current="page"'
        text = layout.substitute(
            page_title=e(page_title), description=e(description or site["tagline"]), root=root,
            site_title=e(title), body=Template(body).safe_substitute(root=root),
            head_extra=head, scripts=scripts, body_class=body_class, **navs)
        write(path, text)

    def map_data(items):
        return json_for_script([{
            "id": s["id"], "name": s["name"], "town": s["town"], "sub": sub_by_slug[s["subprefecture"]]["name"],
            "addr": s["address"], "lat": s["lat"], "lon": s["lon"], "video": s["videos"][0], "path": s["path"]}
            for s in items])

    # トップ
    body = template("top.html").safe_substitute(shop_count=len(live), shops_json=map_data(live))
    page("index.html", 0, f"{title}｜{site['tagline']}", body, nav="nav_top", maps=True, body_class="is-top")

    # 地域から探す（14の振興局）
    count_sub = {}
    for s in live:
        count_sub[s["subprefecture"]] = count_sub.get(s["subprefecture"], 0) + 1
    items = []
    for a in areas:
        n = count_sub.get(a["slug"], 0)
        if n:
            items.append(f'    <li><a href="{a["slug"]}/">{e(a["name"])}<b>{n}</b></a></li>')
        else:
            items.append(f'    <li><span class="area-empty">{e(a["name"])}<b>0</b></span></li>')
    body = template("areas.html").safe_substitute(items="\n".join(items))
    page("areas/index.html", 1, f"地域から探す｜{title}", body, nav="nav_areas")

    # 振興局・市町村・店のページ
    for a in areas:
        in_sub = [s for s in live if s["subprefecture"] == a["slug"]]
        if not in_sub:
            continue
        towns = []
        for t in a["towns"]:
            in_town = [s for s in in_sub if s["town"] == t["name"]]
            if not in_town:
                continue
            towns.append(f'    <li><a href="{t["slug"]}/"><span class="list__name">{e(t["name"])}</span><span class="list__meta">{len(in_town)}店</span></a></li>')
            shop_items = "\n".join(
                f'    <li><a href="{s["slug"]}/"><span class="list__name">{e(s["name"])}</span><span class="list__meta">{e(s["address"])}</span></a></li>'
                for s in in_town)
            body = template("town.html").safe_substitute(
                sub_name=e(a["name"]), name=e(t["name"]), count=len(in_town), items=shop_items, shops_json=map_data(in_town))
            page(f"areas/{a['slug']}/{t['slug']}/index.html", 3, f"{t['name']}のザンギ｜{title}", body, nav="nav_areas", maps=True)
            for s in in_town:
                shop_page(page, a, t, s, map_data)
        body = template("subprefecture.html").safe_substitute(name=e(a["name"]), items="\n".join(towns))
        page(f"areas/{a['slug']}/index.html", 2, f"{a['name']}｜{title}", body, nav="nav_areas")

    # ザンギについて・このサイトについて
    page("about-zangi/index.html", 1, f"ザンギについて｜{title}", template("about-zangi.html").template, nav="nav_zangi")
    contact = []
    if site.get("contact_email"):
        contact.append(f'メール：<a href="mailto:{e(site["contact_email"])}">{e(site["contact_email"])}</a>')
    if site.get("repo_url"):
        contact.append(f'GitHub：<a href="{e(site["repo_url"].rstrip("/"))}/issues">このサイトの Issues</a>')
    if not contact:
        warnings.append("連絡先がありません。data/site.json の contact_email か repo_url を書いてください")
        contact.append("（準備中）")
    body = template("about.html").safe_substitute(
        site_title=e(title), shop_count=len(live), policy_date=jdate(site.get("policy_date", today.isoformat())),
        contact_html='<p class="contact">' + "<br>".join(contact) + "</p>")
    page("about/index.html", 1, f"このサイトについて｜{title}", body, nav="nav_about")

    write("404.html", layout.substitute(
        page_title=f"ページが見つかりません｜{title}", description=e(site["tagline"]), root=(site.get("site_url") or "/").rstrip("/") + "/",
        site_title=e(title), body='<div class="page"><h1 class="page__title">ページが見つかりません</h1><p>店のページは、閉店や動画の削除で外したことがあります。<a href="' + e((site.get("site_url") or "/").rstrip("/") + "/") + '">地図</a>から探してください。</p></div>',
        head_extra="", scripts="", body_class="", nav_top="", nav_areas="", nav_zangi="", nav_about=""))

    print(f"{len(live)}店のページを docs/ に書き出しました")
    for w in warnings:
        print("  注意：" + w)


def shop_page(page, a, t, s, map_data):
    def or_empty(label, value):
        return f'<div><dt>{label}</dt><dd>{e(value)}</dd></div>' if value else ""
    vids = []
    for vid in s["videos"]:
        vids.append(
            f'    <div class="player__frame"><iframe src="https://www.youtube-nocookie.com/embed/{e(vid)}?rel=0&amp;playsinline=1" '
            f'title="YouTube の動画プレーヤー" loading="lazy" referrerpolicy="strict-origin-when-cross-origin" '
            f'allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe></div>\n'
            f'    <a class="shop__yt" href="https://www.youtube.com/watch?v={e(vid)}">YouTubeで見る</a>')
    links = ""
    if s.get("official_links"):
        lis = "".join(f'<li><a href="{e(l["url"])}">{e(l["label"])}</a></li>' for l in s["official_links"])
        links = f'<div><dt>公式リンク</dt><dd><ul>{lis}</ul></dd></div>'
    body = template("shop.html").safe_substitute(
        sub_name=e(a["name"]), town=e(t["name"]), name=e(s["name"]),
        reading_html=f'<p class="shop__reading">{e(s["reading"])}</p>' if s.get("reading") else "",
        videos_html="\n".join(vids), address=e(s["address"]),
        menu_html=or_empty("店での呼び方", s.get("menu_name")),
        features_html=or_empty("ザンギの特徴", s.get("features")),
        official_html=links, checked_on=jdate(s["checked_on"]),
        position_method=e(s["position_method"]), shops_json=map_data([s]))
    page(s["path"] + "index.html", 4, f"{s['name']}（{t['name']}）のザンギ｜{load('site.json')['title']}", body,
         nav="nav_areas", maps=True, description=f"{t['name']}の{s['name']}のザンギの動画と店の情報")


if __name__ == "__main__":
    main()
