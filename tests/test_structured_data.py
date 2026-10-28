"""JSON-LD on mechanicallygifted.rs, read from the served HTML: valid JSON, the business, and an FAQ that matches the page.

Google only shows FAQ data that is also visible on the page, so every question in the JSON-LD must exist in the HTML.
"""
import json
import re

import pytest

from helpers import http

PAGES = {"/": "sr", "/en/": "en"}


def _graph(path):
    html = http.get("https://mechanicallygifted.rs" + path, timeout=20).text
    blocks = [json.loads(b) for b in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)]
    return html, [node for b in blocks for node in b.get("@graph", [b])]


def _node(graph, kind):
    return next(n for n in graph if n["@type"] == kind)


@pytest.mark.parametrize("path", PAGES)
def test_business_node(path):
    business = _node(_graph(path)[1], "ProfessionalService")
    assert business["name"] == "Mechanically Gifted"
    assert business["telephone"].startswith("+381")
    assert "@" in business["email"]
    assert business["url"].startswith("https://mechanicallygifted.rs")


@pytest.mark.parametrize("path,lang", PAGES.items())
def test_faq_is_in_the_page_language(path, lang):
    faq = _node(_graph(path)[1], "FAQPage")
    assert faq["inLanguage"] == lang
    assert len(faq["mainEntity"]) >= 3


@pytest.mark.parametrize("path", PAGES)
def test_every_faq_question_is_visible_on_the_page(path):
    html, graph = _graph(path)
    for item in _node(graph, "FAQPage")["mainEntity"]:
        assert item["@type"] == "Question"
        assert item["acceptedAnswer"]["text"].strip()
        assert item["name"] in html.replace("&#x27;", "'").replace("&#39;", "'"), item["name"]


@pytest.mark.parametrize("path", PAGES)
def test_faq_count_matches_the_visible_questions(path):
    html, graph = _graph(path)
    assert len(_node(graph, "FAQPage")["mainEntity"]) == len(re.findall(r"<summary", html))
