#!/usr/bin/env python3
"""Build the factfile site from the Markdown notes in content/.

    python build.py

writes the finished website into dist/. GitHub runs this automatically every
time you save a change (see .github/workflows/pages.yml), so you normally
never need to run it yourself.

Folder layout (all under content/):
    notes/         one .md file per factfile
    specialties/   one .md file per specialty (title, description, colour)
    categories/    one .md file per category (title, colour, order)
    site.yml       optional: site title, tagline, disclaimer, footer
"""
import html as htmllib
import json
import os
import re
import shutil
import sys
from pathlib import Path

import yaml
from markdown_it import MarkdownIt

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content"
TEMPLATES = ROOT / "templates"
DIST = ROOT / "dist"

# The five standard sections, in order: (field name in the note, heading shown on the page)
SECTIONS = [
    ("background", "Background and pathophysiology"),
    ("diagnosis", "Diagnosis and clinical signs"),
    ("investigations", "Investigations"),
    ("treatment", "Treatment"),
    ("protocols", "Emergency protocols and red flags"),
]

NEUTRAL = "#7b8794"
FALLBACK_COLOURS = ["#2f80c9", "#c4478a", "#5b9a3f", "#e0702b", "#12a0a0", "#8b6fd6", "#d9962b", "#d1453b"]

DEFAULT_SITE = {
    "title": "Ward round factfiles",
    "tagline": "Quick-reference notes for each rotation. Open a specialty to search and sort its conditions, or jump straight to one.",
    "disclaimer": "**Study aid, not a prescribing guide.** Doses and thresholds are for orientation. Always check the BNF and your trust's guidelines, and take your seniors' advice before acting on anything here.",
    "footer": "**Reminder.** These notes are a revision aid and simplify complex guidance. Doses, thresholds and pathways change and vary between hospitals. Check the BNF, current NICE, BTS/SIGN, Resuscitation Council UK and JBDS guidance, and your trust's protocols. Cross-check against your textbooks through your university library.",
}

errors, warnings = [], []
E = htmllib.escape
md = MarkdownIt("commonmark", {"html": False}).enable("table")


# ----------------------------------------------------------------- helpers
def err(msg):
    errors.append(msg)


def warn(msg):
    warnings.append(msg)


def rel(path):
    return str(Path(path).relative_to(ROOT))


def s(value):
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        return " ".join(str(v) for v in value)
    return str(value)


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", s(text).lower()).strip("-")


def truthy(value):
    return str(value).strip().lower() in ("true", "yes", "1", "on")


def to_number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def valid_colour(value):
    return bool(re.fullmatch(r"#[0-9a-fA-F]{3}|#[0-9a-fA-F]{6}", s(value).strip()))


def inline_md(text):
    """Inline Markdown (bold, italic) to HTML, for short texts such as descriptions."""
    return md.renderInline(s(text).strip())


def plain(text):
    return re.sub(r"[*_`]", "", s(text)).strip()


def read_md(path):
    """Return (front matter dict, body text) for a Markdown file."""
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^\ufeff?---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n(.*))?$", text, re.S)
    if not m:
        return {}, text
    try:
        meta = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError as exc:
        mark = getattr(exc, "problem_mark", None)
        where = f" near line {mark.line + 2}" if mark is not None else ""
        problem = getattr(exc, "problem", None) or "invalid formatting"
        raise ValueError(f"the header at the top of the file could not be read{where} ({problem}). "
                         "Check for a missing quote or an incorrectly indented line")
    if not isinstance(meta, dict):
        raise ValueError("the header at the top of the file is not in the expected format")
    return meta, (m.group(2) or "")


def load_collection(name, recursive=False):
    items = {}
    folder = CONTENT / name
    if not folder.exists():
        return items
    paths = folder.rglob("*.md") if recursive else folder.glob("*.md")
    for path in sorted(paths):
        if path.name.startswith("_") or path.name.lower() == "readme.md":
            continue
        try:
            meta, body = read_md(path)
        except ValueError as exc:
            err(f"{rel(path)}: {exc}")
            continue
        if path.stem in items:
            err(f"{rel(path)}: another note already uses the file name '{path.stem}'")
            continue
        items[path.stem] = {"slug": path.stem, "meta": meta, "body": body, "path": path}
    return items


def resolve(ref, collection):
    """Find an entry from a reference such as 'content/categories/cardiovascular.md', 'Cardiovascular' or 'cardiovascular'."""
    ref = s(ref).strip()
    if not ref:
        return None
    stem = Path(ref.replace("\\", "/")).stem
    for key in (stem, slugify(ref)):
        if key in collection:
            return key
    for key, item in collection.items():
        if s(item["meta"].get("title")).strip().lower() == ref.lower():
            return key
    return None


def load_site():
    site = dict(DEFAULT_SITE)
    path = CONTENT / "site.yml"
    if path.exists():
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as exc:
            err(f"content/site.yml: could not be read ({exc})")
            data = {}
        for key in site:
            if s(data.get(key)).strip():
                site[key] = s(data[key]).strip()
    return site


# ------------------------------------------------------------ markdown
RED_START = re.compile(r"^\s*(\*\*|__)?\s*(red flags?|warning|danger)\b", re.I)
ALERT_START = re.compile(r"^\s*\[!(warning|danger|caution)\]\s*", re.I)


def prepare(tokens):
    """Adjust markdown-it tokens: headings inside a section become small headings,
    and blockquotes become the blue 'key facts' box (or the red box for warnings)."""
    for i, tok in enumerate(tokens):
        if tok.type in ("heading_open", "heading_close"):
            tok.tag = "h4"
        elif tok.type == "blockquote_open":
            depth, j = 0, i
            for j in range(i, len(tokens)):
                if tokens[j].type == "blockquote_open":
                    depth += 1
                elif tokens[j].type == "blockquote_close":
                    depth -= 1
                    if depth == 0:
                        break
            red = False
            for k in range(i + 1, j):
                if tokens[k].type == "inline":
                    first = tokens[k]
                    m = ALERT_START.match(first.content)
                    if m:
                        red = True
                        first.content = first.content[m.end():]
                        first.children = md.parseInline(first.content, {})[0].children
                    elif RED_START.match(first.content):
                        red = True
                    break
            tok.tag = "div"
            tok.attrSet("class", "w" if red else "k")
            tokens[j].tag = "div"


def render_tokens(tokens):
    prepare(tokens)
    out = md.renderer.render(tokens, md.options, {})
    return out.replace("<table>", '<div class="tbl"><table>').replace("</table>", "</table></div>")


def render_field(text):
    return render_tokens(md.parse(text))


def split_body(text):
    """Split a note's body into sections at '##' headings: [(title or None, html)]."""
    tokens = md.parse(text)
    parts = [{"title": None, "tokens": []}]
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok.type == "heading_open" and tok.tag in ("h1", "h2"):
            parts.append({"title": plain(tokens[i + 1].content), "tokens": []})
            i += 3
            continue
        parts[-1]["tokens"].append(tok)
        i += 1
    out = []
    for part in parts:
        if not part["tokens"] and not part["title"]:
            continue
        out.append((part["title"], render_tokens(part["tokens"])))
    return out


# ------------------------------------------------------------ building
def section_html(title, inner, prot=False):
    cls = ' class="prot"' if prot else ""
    heading = f"<h3>{E(title)}</h3>\n" if title else ""
    return f"<section{cls}>\n{heading}{inner}</section>\n"


def card_html(n):
    classes = "cond pinned" if n["pinned"] else "cond"
    attrs = f'class="{classes}" id="{E(n["id"])}" style="--c:{n["colour"]}"'
    if not n["pinned"]:
        attrs += f' data-cat="{E(n["cat_title"])}"'
    attrs += f' data-short="{E(n["short"])}" data-k="{E(n["keywords"])}"'
    if n["pinned"] and n["open"]:
    label = "Read first" if n["pinned"] else n["cat_title"]
    body = "".join(section_html(t, h, p) for t, h, p in n["sections"])
    return (f'<details {attrs}>\n<summary><span class="cn">{E(n["title"])}</span>'
            f'<span class="cs">{E(label)}</span></summary>\n<div class="cb">\n{body}</div>\n</details>\n')


def fill(template, values):
    def repl(match):
        key = match.group(1)
        if key not in values:
            raise KeyError(f"template placeholder {{{{{key}}}}} has no value")
        return values[key]
    return re.sub(r"\{\{(\w+)\}\}", repl, template)


def main():
    site = load_site()
    categories = load_collection("categories")
    specialties = load_collection("specialties")
    notes_raw = load_collection("notes", recursive=True)

    # ---- categories
    cats = {}
    for i, (slug, item) in enumerate(sorted(categories.items())):
        meta = item["meta"]
        colour = s(meta.get("colour")).strip()
        if not valid_colour(colour):
            if colour:
                warn(f"{rel(item['path'])}: '{colour}' is not a colour like #1c5d99, so a default colour was used")
            colour = FALLBACK_COLOURS[i % len(FALLBACK_COLOURS)]
        order = to_number(meta.get("order"))
        cats[slug] = {"title": s(meta.get("title")).strip() or slug.replace("-", " ").title(),
                      "colour": colour, "order": order if order is not None else 1000}
    cats["uncategorised"] = {"title": "Uncategorised", "colour": NEUTRAL, "order": 9999}

    # ---- specialties
    specs = {}
    for i, (slug, item) in enumerate(sorted(specialties.items())):
        meta = item["meta"]
        colour = s(meta.get("colour")).strip()
        if not valid_colour(colour):
            if colour:
                warn(f"{rel(item['path'])}: '{colour}' is not a colour like #1c5d99, so a default colour was used")
            colour = FALLBACK_COLOURS[i % len(FALLBACK_COLOURS)]
        order = to_number(meta.get("order"))
        specs[slug] = {"slug": slug, "title": s(meta.get("title")).strip() or slug.replace("-", " ").title(),
                       "description": s(meta.get("description")).strip(), "colour": colour,
                       "order": order if order is not None else 1000, "notes": []}

    # ---- notes
    for slug, item in notes_raw.items():
        meta, where = item["meta"], rel(item["path"])
        if truthy(meta.get("draft")):
            continue
        title = s(meta.get("title")).strip()
        if not title:
            err(f"{where}: the note needs a title")
            continue
        spec_key = resolve(meta.get("specialty"), specialties)
        if not spec_key:
            avail = ", ".join(sorted(specialties)) or "none yet"
            err(f"{where}: the specialty '{s(meta.get('specialty'))}' was not found (available: {avail})")
            continue
        pinned = truthy(meta.get("pinned"))
        cat_key = resolve(meta.get("category"), categories)
        if not cat_key and not pinned:
            warn(f"{where}: no matching category ('{s(meta.get('category'))}'), so it is listed under Uncategorised")
            cat_key = "uncategorised"
        cat = cats.get(cat_key) if cat_key else None

        sections = []
        try:
            for field, heading in SECTIONS:
                text = s(meta.get(field))
                if text.strip():
                    sections.append((heading, render_field(text), field == "protocols"))
            if item["body"].strip():
                for heading, inner in split_body(item["body"]):
                    is_prot = bool(heading and re.match(r"emergency protocols", heading, re.I))
                    sections.append((heading, inner, is_prot))
        except Exception as exc:  # a broken note should never be silent
            err(f"{where}: could not be converted ({exc})")
            continue
        if not sections:
            warn(f"{where}: has no content yet, so it was skipped (add text, or mark it as a draft)")
            continue

        order = to_number(meta.get("order"))
        specs[spec_key]["notes"].append({
            "id": slug, "title": title, "short": s(meta.get("short")).strip() or title,
            "keywords": s(meta.get("keywords")).strip(), "order": order, "pinned": pinned,
            "open": not str(meta.get("open", "true")).strip().lower() in ("false", "no", "0", "off"),
            "cat_title": cat["title"] if cat else "", "cat_order": cat["order"] if cat else 0,
            "colour": cat["colour"] if cat else NEUTRAL, "sections": sections,
        })

    live = [sp for sp in specs.values() if sp["notes"]]
    if not live and not errors:
        err("No notes were found to publish. Add a note in content/notes/ and point it at a specialty.")

    if errors:
        report(errors, warnings)
        sys.exit(1)

    live.sort(key=lambda sp: (sp["order"], sp["title"].lower()))

    # ---- write the site
    if DIST.exists():
        shutil.rmtree(DIST)
    (DIST / "assets").mkdir(parents=True)
    shutil.copy(TEMPLATES / "site.css", DIST / "assets" / "site.css")
    shutil.copy(TEMPLATES / "factfile.js", DIST / "assets" / "factfile.js")
    (DIST / ".nojekyll").write_text("", encoding="utf-8")

    page_tpl = (TEMPLATES / "page.html").read_text(encoding="utf-8")
    index_tpl = (TEMPLATES / "index.html").read_text(encoding="utf-8")
    disclaimer = inline_md(site["disclaimer"])
    footer = inline_md(site["footer"])

    def note_order(n):
        return (0 if n["order"] is not None else 1, n["order"] or 0, n["title"].lower())

    spec_cards = []
    for sp in live:
        notes = sorted(sp["notes"], key=lambda n: (0 if n["pinned"] else 1,) + note_order(n))
        regular = [n for n in notes if not n["pinned"]]
        present = {}
        for n in regular:
            present[n["cat_title"]] = (n["cat_order"], n["colour"])
        ordered_cats = sorted(present.items(), key=lambda kv: (kv[1][0], kv[0].lower()))
        legend = "".join(f'<span style="--c:{colour}"><i></i>{E(title)}</span>' for title, (_, colour) in ordered_cats)

        page = fill(page_tpl, {
            "page_title": E(f"{sp['title']} factfiles"),
            "spec_description": inline_md(sp["description"]) if sp["description"] else "",
            "spec_description_attr": E(plain(sp["description"]) or site["tagline"], quote=True),
            "disclaimer": disclaimer, "footer": footer, "legend": legend,
            "cats_json": E(json.dumps([t for t, _ in ordered_cats]), quote=True),
            "cards": "\n".join(card_html(n) for n in notes),
        })
        (DIST / f"{sp['slug']}.html").write_text(page, encoding="utf-8")

        jump = "".join(f'<li><a href="{E(sp["slug"])}.html#{E(n["id"])}">{E(n["short"])}</a></li>'
                       for n in regular)
        pinned_n = len(notes) - len(regular)
        count = f"{len(regular)} factfile" + ("" if len(regular) == 1 else "s")
        if pinned_n:
            count += ", plus a read-first guide" if pinned_n == 1 else f", plus {pinned_n} read-first guides"
        desc = f"<p>{inline_md(sp['description'])}</p>\n    " if sp["description"] else ""
        spec_cards.append(
            f'  <li class="spec" style="--c:{sp["colour"]}">\n    <h2>{E(sp["title"])}</h2>\n    {desc}'
            f'<p class="meta">{E(count)}</p>\n'
            f'    <a class="open" href="{E(sp["slug"])}.html">Open {E(sp["title"].lower())}</a>\n'
            f'    <details class="jump">\n      <summary>Jump to a condition</summary>\n      <ul>{jump}</ul>\n    </details>\n  </li>')

    index = fill(index_tpl, {
        "site_title": E(site["title"]), "tagline": inline_md(site["tagline"]),
        "tagline_attr": E(plain(site["tagline"]), quote=True),
        "specialties": "\n".join(spec_cards), "disclaimer": disclaimer,
    })
    (DIST / "index.html").write_text(index, encoding="utf-8")

    report(errors, warnings)
    total = sum(len(sp["notes"]) for sp in live)
    print(f"Built {len(live)} specialt{'y' if len(live) == 1 else 'ies'} and {total} notes into {rel(DIST)}/")
    for sp in live:
        print(f"  {sp['slug']}.html  ({len(sp['notes'])} notes)")


def report(errs, warns):
    on_github = bool(os.environ.get("GITHUB_ACTIONS"))
    for w in warns:
        print(f"::warning::{w}" if on_github else f"Warning: {w}")
    for e in errs:
        print(f"::error::{e}" if on_github else f"Error: {e}")
    if errs:
        print("\nThe site was not updated. Fix the problem above and save again.")


if __name__ == "__main__":
    main()
