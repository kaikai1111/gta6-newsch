#!/usr/bin/env python3
"""GTA6ニュース速報まとめ サイト生成スクリプト

使い方:  python3 _build.py
  _articles.txt（記事）と _page_*.html（固定ページ）から、
  トップ・記事・カテゴリ・固定ページ・sitemap.xml を作り直す。
  ※ファイル名が _ で始まるものは GitHub Pages では公開されない。
"""
import html, json, os, re

SITE = "https://gta6-newsch.com"
NAME = "GTA6ニュース速報まとめ"
CH = "https://www.youtube.com/@%E3%81%82%E3%81%A4%E3%81%BE%E3%82%8C%E3%82%B2%E3%83%BC%E3%83%A0%E5%A4%A9%E5%9B%BD"
ADS = False  # AdSense に合格したら True にして、下の ad() に広告コードを入れる

CATS = [("news", "最新情報"), ("release", "発売日・価格"), ("spec", "対応機種"),
        ("trivia", "雑学"), ("origin", "元ネタ解説")]
CATNAME = dict(CATS)
CATCLS = {"news": "c-news", "release": "", "spec": "c-spec", "trivia": "c-trivia", "origin": "c-trivia"}

ROOT = os.path.dirname(os.path.abspath(__file__))
esc = html.escape


# ---------- 記事ファイルの読み込み ----------
def load_articles():
    src = open(os.path.join(ROOT, "_articles.txt"), encoding="utf-8").read()
    posts = []
    for chunk in re.split(r"^=== ", src, flags=re.M)[1:]:
        head, body = chunk.split("\n---\n", 1)
        p = {"points": []}
        lines = head.strip().split("\n")
        p["slug"] = lines[0].strip()
        for ln in lines[1:]:
            if ln.startswith("- "):
                p["points"].append(ln[2:].strip())
            elif ":" in ln:
                k, v = ln.split(":", 1)
                p[k.strip()] = v.strip()
        p["body"] = body.strip()
        p["views"] = int(p.get("views", 0))
        posts.append(p)
    posts.sort(key=lambda x: x["date"], reverse=True)
    return posts


def jdate(d):
    y, m, dd = d.split("-")
    return f"{int(y)}年{int(m)}月{int(dd)}日"


def thumb(vid):
    return f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"


# ---------- かんたんMarkdown ----------
def inline(s, bymap):
    s = esc(s, quote=False)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"\[\[([\w-]+)\]\]",
               lambda m: f'<a href="{m.group(1)}.html">{esc(bymap[m.group(1)]["title"])}</a>', s)
    s = re.sub(r"\[(.+?)\]\((https?://[^)]+)\)", r'<a href="\2" target="_blank" rel="noopener">\1</a>', s)
    return s


def md(text, bymap):
    out, para, lst = [], [], []

    def flush():
        if para:
            out.append("<p>" + "<br>".join(inline(x, bymap) for x in para) + "</p>")
            para.clear()
        if lst:
            out.append('<ul class="list">' + "".join(f"<li>{inline(x, bymap)}</li>" for x in lst) + "</ul>")
            lst.clear()

    for ln in text.split("\n"):
        ln = ln.rstrip()
        if not ln:
            flush()
        elif ln.startswith("## "):
            flush(); out.append(f"<h2>{inline(ln[3:], bymap)}</h2>")
        elif ln.startswith("### "):
            flush(); out.append(f"<h3>{inline(ln[4:], bymap)}</h3>")
        elif ln.startswith("- "):
            if para: flush()
            lst.append(ln[2:])
        elif ln.startswith("> "):
            flush(); out.append(f'<p class="note">{inline(ln[2:], bymap)}</p>')
        elif ln.startswith("<"):
            flush(); out.append(ln)
        else:
            if lst: flush()
            para.append(ln)
    flush()
    return "\n      ".join(out)


# ---------- 共通パーツ ----------
def ad(kind, label):
    if not ADS:
        return f"<!-- 広告枠: {label} -->"
    return (f'<div class="ad"><span class="ad-label">スポンサーリンク</span>'
            f'<div class="ad-slot {kind}">{label}</div></div>')


def head(title, desc, path, cur=None, og_image=None, og_type="website"):
    nav = [("index.html", "トップ")] + [(f"{k}.html", v) for k, v in CATS] + [("contact.html", "お問い合わせ")]
    ac = ' aria-current="page"'
    navh = "".join(f'<li><a href="{h}"{ac if h == cur else ""}>{t}</a></li>' for h, t in nav)
    full = title if title == NAME else f"{title}｜{NAME}"
    url = f"{SITE}/{'' if path == 'index.html' else path}"
    img = og_image or f"{SITE}/apple-touch-icon.png"
    return f'''<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(full)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="{og_type}">
<meta property="og:title" content="{esc(full)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{img}">
<meta property="og:site_name" content="{NAME}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="favicon.ico" sizes="32x32">
<link rel="icon" href="favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<link rel="stylesheet" href="style.css">
<!-- AdSense: 審査・配信時はここに AdSense のコードを入れる -->
</head>
<body id="top">
<div class="topbar">GTA6の最新情報を毎日ショートでお届け！</div>
<header class="hero">
  <a class="logo" href="index.html">GTA6ニュース速報</a>
</header>
<nav class="gnav"><ul class="wrap">{navh}</ul></nav>
'''


def side(posts):
    rank = sorted(posts, key=lambda x: -x["views"])[:5]
    rk = "".join(
        f'      <li><a class="rt" href="{p["slug"]}.html"><img src="{thumb(p["id"])}" alt="" width="90" height="56" loading="lazy" decoding="async"></a>'
        f'<a href="{p["slug"]}.html">{esc(p["title"])}<span class="v">{p["views"]:,}回視聴（ショート）</span></a></li>\n' for p in rank)
    cats = "".join(
        f'      <a href="{k}.html"><span>{v}</span><span class="n">({sum(1 for p in posts if p["cat"] == k)})</span></a>\n'
        for k, v in CATS)
    return f'''<aside class="side">
  <section class="box">
    <h2 class="ttl">運営チャンネル</h2>
    <div class="prof"><div class="prof-ico">GTA6<br>速報</div><div><b>GTA6ニュース速報【毎日投稿】</b>発売日・価格・対応機種をショートで解説しています。</div></div>
    <a class="btn" href="{CH}" target="_blank" rel="noopener">▶ YouTubeでチャンネル登録</a>
  </section>
  {ad("ad-300", "サイド上 300×250")}
  <section class="box">
    <h2 class="ttl">人気記事ランキング</h2>
    <ol class="rank">
{rk}    </ol>
  </section>
  <section class="box">
    <h2 class="ttl">カテゴリー</h2>
    <nav class="cats">
{cats}    </nav>
  </section>
  {ad("ad-300", "サイド下 300×250")}
</aside>'''


FOOT = '''<footer class="footer">
  <ul><li><a href="index.html">トップ</a></li><li><a href="about.html">運営者情報</a></li><li><a href="privacy.html">プライバシーポリシー</a></li><li><a href="privacy.html#disclaimer">免責事項</a></li><li><a href="contact.html">お問い合わせ</a></li></ul>
  <p>当サイトはRockstar Gamesとは無関係のファンサイトです。<br>© 2026 GTA6ニュース速報まとめ All Rights Reserved.</p>
</footer>
<a class="totop" href="#top" aria-label="ページトップへ">▲</a>
'''


def card(p, first=False):
    load = 'fetchpriority="high"' if first else 'loading="lazy"'
    return f'''      <article class="post">
        <a class="thumb" href="{p["slug"]}.html"><img src="{thumb(p["id"])}" alt="" width="200" height="125" {load} decoding="async"><span class="play">▶ Shorts</span></a>
        <div><a class="cat {CATCLS[p["cat"]]}" href="{p["cat"]}.html">{CATNAME[p["cat"]]}</a>
          <h3 class="post-t"><a href="{p["slug"]}.html">{esc(p["title"])}</a></h3>
          <p class="post-ex">{esc(p["desc"])}</p>
          <p class="date"><time datetime="{p["date"]}">{jdate(p["date"])}</time></p></div>
      </article>
'''


def listing(posts, items, heading, path, title, desc, cur):
    cards = ""
    for i, p in enumerate(items):
        cards += card(p, i == 0)
        if i == 4:
            cards += "      " + ad("ad-in", "インフィード") + "\n"
    return head(title, desc, path, cur) + f'''<div class="wrap layout">
  <main>
    {ad("ad-728", "ヘッダー下 728×90")}
    <section class="box">
      <h2 class="ttl">{heading}</h2>
{cards}    </section>
  </main>
{side(posts)}
</div>
{FOOT}</body>
</html>
'''


def article(p, posts, bymap):
    same = [x for x in posts if x["cat"] == p["cat"] and x is not p]
    other = [x for x in posts if x["cat"] != p["cat"]]
    rel = (same + other)[:6]
    relh = "".join(
        f'<a href="{x["slug"]}.html"><div class="thumb"><img src="{thumb(x["id"])}" alt="" width="200" height="125" loading="lazy" decoding="async"></div>{esc(x["title"])}</a>'
        for x in rel)
    pts = "".join(f"<li>{inline(x, bymap)}</li>" for x in p["points"])
    url = f'{SITE}/{p["slug"]}.html'
    from urllib.parse import quote
    share_x = f'https://twitter.com/intent/tweet?url={quote(url)}&text={quote(p["title"])}'
    share_line = f'https://social-plugins.line.me/lineit/share?url={quote(url)}'
    ld = json.dumps({"@context": "https://schema.org", "@type": "Article", "headline": p["title"],
                     "datePublished": p["date"], "image": thumb(p["id"]),
                     "author": {"@type": "Person", "name": "田中一人", "url": f"{SITE}/about.html"}},
                    ensure_ascii=False)
    return head(p["title"], p["desc"], f'{p["slug"]}.html', f'{p["cat"]}.html', thumb(p["id"]), "article") + f'''<div class="wrap layout">
  <main>
    <p class="crumb"><a href="index.html">トップ</a> › <a href="{p["cat"]}.html">{CATNAME[p["cat"]]}</a> › 記事</p>
    <article class="article">
      <a class="cat {CATCLS[p["cat"]]}" href="{p["cat"]}.html">{CATNAME[p["cat"]]}</a>
      <h1>{esc(p["title"])}</h1>
      <p class="meta"><time datetime="{p["date"]}">{jdate(p["date"])}</time> 公開 ／ 文：田中一人</p>
      {ad("ad-in", "記事上")}
      <div class="yt" data-id="{p["id"]}" role="button" tabindex="0" aria-label="動画を再生"><img src="{thumb(p["id"])}" alt="" width="340" height="604" fetchpriority="high"></div>
      <div class="point"><b>この記事のポイント</b>
        <ul>{pts}</ul>
      </div>
      {md(p["body"], bymap)}
      {ad("ad-300", "記事下 300×250")}
      <div class="share">
        <a class="x" href="{share_x}" target="_blank" rel="noopener">Xでシェア</a><a class="line" href="{share_line}" target="_blank" rel="noopener">LINEで送る</a><a class="yt-ch" href="{CH}" target="_blank" rel="noopener">チャンネル登録</a>
      </div>
    </article>
    <section class="box" style="margin-top:24px">
      <h2 class="ttl">関連記事</h2>
      <div class="related">{relh}</div>
    </section>
  </main>
{side(posts)}
</div>
{FOOT}<script type="application/ld+json">{ld}</script>
<script>
document.querySelectorAll('.yt').forEach(function(el){{
  function play(){{if(el.classList.contains('on'))return;el.classList.add('on');
    el.innerHTML='<iframe src="https://www.youtube-nocookie.com/embed/'+el.dataset.id+'?autoplay=1" allow="autoplay;encrypted-media;picture-in-picture" allowfullscreen title="YouTube"></iframe>';}}
  el.addEventListener('click',play);
  el.addEventListener('keydown',function(e){{if(e.key==='Enter')play();}});
}});
</script>
</body>
</html>
'''


def static_page(name, title, desc, posts):
    body = open(os.path.join(ROOT, f"_page_{name}.html"), encoding="utf-8").read().rstrip()
    cur = "contact.html" if name == "contact" else None
    return head(title, desc, f"{name}.html", cur) + f'''<div class="wrap layout">
  <main>
    <p class="crumb"><a href="index.html">トップ</a> › {title}</p>
    <article class="article">
      {body}
    </article>
  </main>
{side(posts)}
</div>
{FOOT}</body>
</html>
'''


def write(name, s):
    open(os.path.join(ROOT, name), "w", encoding="utf-8").write(s)


def main():
    posts = load_articles()
    bymap = {p["slug"]: p for p in posts}
    write("index.html", listing(posts, posts, "新着記事", "index.html", NAME,
                                "GTA6（グラセフ6）の発売日・価格・対応機種・最新情報を、YouTubeショートと一緒に文章でわかりやすくまとめています。",
                                "index.html"))
    for k, v in CATS:
        items = [p for p in posts if p["cat"] == k]
        write(f"{k}.html", listing(posts, items, f"{v}の記事一覧", f"{k}.html", f"{v}の記事一覧",
                                   f"GTA6の「{v}」に関する記事の一覧です。", f"{k}.html"))
    for p in posts:
        write(f'{p["slug"]}.html', article(p, posts, bymap))
    write("about.html", static_page("about", "運営者情報", "GTA6ニュース速報まとめの運営者情報です。", posts))
    write("privacy.html", static_page("privacy", "プライバシーポリシー・免責事項", "GTA6ニュース速報まとめのプライバシーポリシーと免責事項です。", posts))
    write("contact.html", static_page("contact", "お問い合わせ", "GTA6ニュース速報まとめへのお問い合わせはこちらから。", posts))
    # 旧テンプレの article.html はトップへ転送
    write("article.html", '<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=index.html"><link rel="canonical" href="https://gta6-newsch.com/"><title>移動しました</title>\n')
    # sitemap
    urls = [("", posts[0]["date"])] + [(f"{k}.html", posts[0]["date"]) for k, _ in CATS] + \
           [(f'{p["slug"]}.html', p["date"]) for p in posts] + \
           [("about.html", "2026-11-12"), ("privacy.html", "2026-11-12"), ("contact.html", "2026-11-12")]
    sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + \
         "".join(f"  <url><loc>{SITE}/{u}</loc><lastmod>{d}</lastmod></url>\n" for u, d in urls) + "</urlset>\n"
    write("sitemap.xml", sm)
    print(f"OK: {len(posts)} articles, {len(CATS)} categories")


if __name__ == "__main__":
    main()
