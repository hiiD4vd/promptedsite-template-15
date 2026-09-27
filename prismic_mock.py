import os
import json
import re
from urllib.parse import parse_qs, unquote

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "prismic_data")

ROOT_FILE = os.path.join(DATA_DIR, "api_v2_root.json")
DOCS_FILE = os.path.join(DATA_DIR, "all_rebranded_docs.json")

def load_root():
    with open(ROOT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    if "forms" in data and "everything" in data["forms"]:
        data["forms"]["everything"]["action"] = "/prismic-api/v2/documents/search"
    return data

def load_docs():
    with open(DOCS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

ALL_DOCS = load_docs()
ROOT_DATA = load_root()

def filter_documents(q_list, lang, page=1, page_size=20):
    results = list(ALL_DOCS)

    if lang and lang != "*":
        results = [d for d in results if d.get("lang") == lang]

    for q in q_list:
        q_str = unquote(q)
        # Match type
        m_type = re.search(r'at\(document\.type,\s*["\']([^"\']+)["\']\)', q_str)
        if m_type:
            doc_type = m_type.group(1)
            results = [d for d in results if d.get("type") == doc_type]

        # Match UID
        m_uid = re.search(r'at\(my\.product\.uid,\s*["\']([^"\']+)["\']\)', q_str)
        if m_uid:
            doc_uid = m_uid.group(1)
            results = [d for d in results if d.get("uid") == doc_uid]

        # Match ID
        m_id = re.search(r'at\(document\.id,\s*["\']([^"\']+)["\']\)', q_str)
        if m_id:
            doc_id = m_id.group(1)
            results = [d for d in results if d.get("id") == doc_id]

    # Pagination
    total_size = len(results)
    start = (page - 1) * page_size
    end = start + page_size
    paged_results = results[start:end]

    return {
        "page": page,
        "results_per_page": page_size,
        "results_size": len(paged_results),
        "total_results_size": total_size,
        "total_pages": (total_size + page_size - 1) // page_size if page_size else 1,
        "next_page": None,
        "prev_page": None,
        "results": paged_results
    }

def handle_prismic_query(path, query_string):
    clean_path = path.rstrip("/")
    if clean_path in ("/prismic-api/v2", "/api/v2"):
        return 200, "application/json", json.dumps(ROOT_DATA).encode("utf-8")
    
    if clean_path in ("/prismic-api/v2/documents/search", "/api/v2/documents/search"):
        params = parse_qs(query_string)
        q_list = params.get("q", [])
        lang = params.get("lang", ["*"])[0]
        try:
            page = int(params.get("page", ["1"])[0])
        except ValueError:
            page = 1
        try:
            page_size = int(params.get("pageSize", ["20"])[0])
        except ValueError:
            page_size = 20

        data = filter_documents(q_list, lang, page, page_size)
        return 200, "application/json", json.dumps(data, ensure_ascii=False).encode("utf-8")

    return None, None, None
