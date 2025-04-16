import requests
import xml.etree.ElementTree as ET
from urllib.parse import quote
import re

OC = "chetera"
BASE = "http://www.law.go.kr"

def get_law_list_from_api(query):
    exact_query = f'\"{query}\"'
    encoded_query = quote(exact_query)
    page = 1
    laws = []
    while True:
        url = f"{BASE}/DRF/lawSearch.do?OC={OC}&target=law&type=XML&display=100&page={page}&search=2&knd=A0002&query={encoded_query}"
        res = requests.get(url, timeout=10)
        res.encoding = 'utf-8'
        if res.status_code != 200:
            break
        root = ET.fromstring(res.content)
        for law in root.findall("law"):
            laws.append({
                "법령명": law.findtext("법령명한글", "").strip(),
                "MST": law.findtext("법령일련번호", ""),
                "URL": BASE + law.findtext("법령상세링크", "")
            })
        if len(root.findall("law")) < 100:
            break
        page += 1
    return laws

def get_law_text_by_mst(mst):
    url = f"{BASE}/DRF/lawService.do?OC={OC}&target=law&MST={mst}&type=XML"
    try:
        res = requests.get(url, timeout=10)
        res.encoding = 'utf-8'
        return res.content if res.status_code == 200 else None
    except:
        return None

def clean(text):
    return re.sub(r"\s+", "", text or "")

def highlight(text, keyword):
    if not text:
        return ""
    return text.replace(keyword, f"<span style='color:red'>{keyword}</span>")

def get_highlighted_articles(mst, keyword):
    xml_data = get_law_text_by_mst(mst)
    if not xml_data:
        return "⚠️ 본문을 불러올 수 없습니다.", ""

    tree = ET.fromstring(xml_data)
    articles = tree.findall(".//조문단위")
    keyword_clean = clean(keyword)
    results = []

    for article in articles:
        조제목 = article.findtext("조문제목", "") or ""
        조내용 = article.findtext("조문내용", "") or ""
        항들 = article.findall("항")
        include = False
        항출력들 = []

        for 항 in 항들:
            항내용 = 항.findtext("항내용", "") or ""
            if keyword_clean in clean(항내용):
                include = True
                항출력들.append(f"<div style='text-indent:3em;'>{highlight(항내용, keyword)}</div>")

        if keyword_clean in clean(조제목) or keyword_clean in clean(조내용) or include:
            output = f"<div><strong>{highlight(조제목, keyword)}</strong> {highlight(조내용, keyword)}</div>"
            output += "".join(항출력들)
            results.append(output)

    return "".join(results) if results else "🔍 해당 검색어를 포함한 조문이 없습니다.", ""
