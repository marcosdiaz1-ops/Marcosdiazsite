import re, sys, json, pathlib
def build(template, out, slug_url, alt_en, alt_es, title, desc, date_iso, date_human, tag, crumbs_blog, other_link_html, article_html, lang):
    t = pathlib.Path(template).read_text()
    # head
    t = re.sub(r"<title>.*?</title>", f"<title>{title} | Marcos Diaz</title>", t, flags=re.S)
    t = re.sub(r'(<meta name="description" content=")[^"]*', lambda m: m.group(1)+desc, t)
    t = re.sub(r'(<meta property="og:title" content=")[^"]*', lambda m: m.group(1)+title+" | Marcos Diaz", t)
    t = re.sub(r'(<meta property="og:description" content=")[^"]*', lambda m: m.group(1)+desc, t)
    t = re.sub(r'(<meta property="og:url" content=")[^"]*', lambda m: m.group(1)+slug_url, t)
    t = re.sub(r'(<link rel="canonical" href=")[^"]*', lambda m: m.group(1)+slug_url, t)
    t = re.sub(r'(<link rel="alternate" hreflang="en" href=")[^"]*', lambda m: m.group(1)+alt_en, t)
    t = re.sub(r'(<link rel="alternate" hreflang="es" href=")[^"]*', lambda m: m.group(1)+alt_es, t)
    t = re.sub(r'(<link rel="alternate" hreflang="x-default" href=")[^"]*', lambda m: m.group(1)+alt_en, t)
    ld = {"@context":"https://schema.org","@type":"BlogPosting","headline":title,"description":desc,"inLanguage":lang,"datePublished":date_iso,"dateModified":date_iso,"mainEntityOfPage":slug_url,"image":"https://605homesearch.com/images/og-image.jpg","author":{"@type":"Person","name":"Marcos Diaz","url":"https://605homesearch.com/"},"publisher":{"@type":"Organization","name":"Marcos Diaz Real Estate","logo":{"@type":"ImageObject","url":"https://605homesearch.com/images/og-image.jpg"}}}
    t = re.sub(r'<script type="application/ld\+json">\{"@context": "https://schema.org", "@type": "BlogPosting".*?</script>', lambda m: '<script type="application/ld+json">'+json.dumps(ld, ensure_ascii=False)+'</script>', t, flags=re.S)
    # language switch link in header (points to other-language post)
    other = alt_es if lang=="en" else alt_en
    rel_other = other.replace("https://605homesearch.com/", "../../" if lang=="en" else "../../../")
    t = re.sub(r'(<a href=")[^"]*(" class="lang")', lambda m: m.group(1)+rel_other+m.group(2), t, count=1)
    # hero
    t = re.sub(r'<p class="post-tag">.*?</p>', f'<p class="post-tag">{tag}</p>', t, count=1, flags=re.S)
    t = re.sub(r'<h1 class="post-title">.*?</h1>', f'<h1 class="post-title">{title}</h1>', t, count=1, flags=re.S)
    t = re.sub(r'<p class="post-meta">.*?</p>', f'<p class="post-meta">{other_link_html.format(date=date_human)}</p>', t, count=1, flags=re.S)
    # article
    t = re.sub(r'<article class="prose post">.*?</article>', lambda m: '<article class="prose post">\n'+article_html.strip()+'\n        </article>', t, count=1, flags=re.S)
    pathlib.Path(out).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(out).write_text(t)
if __name__=="__main__":
    cfg = json.loads(pathlib.Path(sys.argv[1]).read_text())
    for p in cfg["posts"]:
        p["article_html"] = pathlib.Path(p.pop("article_file")).read_text()
        build(**p)
