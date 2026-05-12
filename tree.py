# -*- coding: utf-8 -*-
"""
Cheksiz chuqurlikdagi bolimlar daraxti.
Har bir node:
{
  "id": "abc123",
  "name": "Bolim nomi",
  "parent_id": "...yoki null",
  "order": 0,
  "content": [
    {"type": "text", "value": "matn..."},
    {"type": "photo", "file_id": "...", "caption": ""},
    {"type": "video", "file_id": "...", "caption": ""}
  ],
  "children_ids": ["id1", "id2", ...]
}
"""
import json
import os
import uuid

TREE_FILE = "tree_db.json"


def _empty_tree():
    return {"nodes": {}, "root_ids": []}


def load_tree():
    if not os.path.exists(TREE_FILE):
        return _empty_tree()
    try:
        with open(TREE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if "nodes" not in data:
            data["nodes"] = {}
        if "root_ids" not in data:
            data["root_ids"] = []
        return data
    except Exception:
        return _empty_tree()


def save_tree(tree):
    with open(TREE_FILE, "w", encoding="utf-8") as f:
        json.dump(tree, f, ensure_ascii=False, indent=2)


def new_id():
    return uuid.uuid4().hex[:10]


def get_node(tree, node_id):
    return tree["nodes"].get(node_id)


def get_children(tree, parent_id):
    if parent_id is None:
        ids = tree.get("root_ids", [])
    else:
        node = get_node(tree, parent_id)
        if not node:
            return []
        ids = node.get("children_ids", [])
    children = []
    for cid in ids:
        n = get_node(tree, cid)
        if n:
            children.append(n)
    children.sort(key=lambda x: x.get("order", 0))
    return children


def add_node(name, parent_id=None):
    tree = load_tree()
    nid = new_id()
    siblings = get_children(tree, parent_id)
    order = (max((s.get("order", 0) for s in siblings), default=-1)) + 1
    node = {
        "id": nid,
        "name": name,
        "parent_id": parent_id,
        "order": order,
        "content": [],
        "children_ids": []
    }
    tree["nodes"][nid] = node
    if parent_id is None:
        tree["root_ids"].append(nid)
    else:
        parent = tree["nodes"].get(parent_id)
        if parent is not None:
            parent.setdefault("children_ids", []).append(nid)
    save_tree(tree)
    return node


def rename_node(node_id, new_name):
    tree = load_tree()
    node = tree["nodes"].get(node_id)
    if not node:
        return False
    node["name"] = new_name
    save_tree(tree)
    return True


def _delete_recursive(tree, node_id):
    node = tree["nodes"].get(node_id)
    if not node:
        return
    for cid in list(node.get("children_ids", [])):
        _delete_recursive(tree, cid)
    if node_id in tree["nodes"]:
        del tree["nodes"][node_id]


def delete_node(node_id):
    tree = load_tree()
    node = tree["nodes"].get(node_id)
    if not node:
        return False
    parent_id = node.get("parent_id")
    _delete_recursive(tree, node_id)
    if parent_id is None:
        if node_id in tree.get("root_ids", []):
            tree["root_ids"].remove(node_id)
    else:
        parent = tree["nodes"].get(parent_id)
        if parent and node_id in parent.get("children_ids", []):
            parent["children_ids"].remove(node_id)
    save_tree(tree)
    return True


def move_node(node_id, direction):
    tree = load_tree()
    node = tree["nodes"].get(node_id)
    if not node:
        return False
    parent_id = node.get("parent_id")
    if parent_id is None:
        ids = tree.get("root_ids", [])
    else:
        parent = tree["nodes"].get(parent_id)
        if not parent:
            return False
        ids = parent.get("children_ids", [])
    siblings = sorted(
        [tree["nodes"][i] for i in ids if i in tree["nodes"]],
        key=lambda x: x.get("order", 0)
    )
    idx = next((i for i, s in enumerate(siblings) if s["id"] == node_id), -1)
    if idx < 0:
        return False
    if direction == "up" and idx > 0:
        siblings[idx], siblings[idx - 1] = siblings[idx - 1], siblings[idx]
    elif direction == "down" and idx < len(siblings) - 1:
        siblings[idx], siblings[idx + 1] = siblings[idx + 1], siblings[idx]
    else:
        return False
    for i, s in enumerate(siblings):
        s["order"] = i
    save_tree(tree)
    return True


def add_content(node_id, item):
    tree = load_tree()
    node = tree["nodes"].get(node_id)
    if not node:
        return False
    node.setdefault("content", []).append(item)
    save_tree(tree)
    return True


def remove_content(node_id, index):
    tree = load_tree()
    node = tree["nodes"].get(node_id)
    if not node:
        return False
    content = node.get("content", [])
    if 0 <= index < len(content):
        content.pop(index)
        save_tree(tree)
        return True
    return False


def move_content(node_id, index, direction):
    tree = load_tree()
    node = tree["nodes"].get(node_id)
    if not node:
        return False
    content = node.get("content", [])
    if direction == "up" and 0 < index < len(content):
        content[index], content[index - 1] = content[index - 1], content[index]
    elif direction == "down" and 0 <= index < len(content) - 1:
        content[index], content[index + 1] = content[index + 1], content[index]
    else:
        return False
    save_tree(tree)
    return True


def update_content_text(node_id, index, new_text):
    tree = load_tree()
    node = tree["nodes"].get(node_id)
    if not node:
        return False
    content = node.get("content", [])
    if 0 <= index < len(content) and content[index].get("type") == "text":
        content[index]["value"] = new_text
        save_tree(tree)
        return True
    return False


def get_path(node_id):
    tree = load_tree()
    path = []
    current = tree["nodes"].get(node_id)
    while current:
        path.insert(0, current)
        pid = current.get("parent_id")
        if pid is None:
            break
        current = tree["nodes"].get(pid)
    return path


def path_string(node_id, sep=" › "):
    return sep.join(p["name"] for p in get_path(node_id))


def has_children(node_id):
    tree = load_tree()
    node = tree["nodes"].get(node_id)
    if not node:
        return False
    return len(node.get("children_ids", [])) > 0


# ===== MIGRATSIYA: eski videos_db.json va sections_db.json dan =====

def migrate_from_old():
    tree = load_tree()
    if tree.get("nodes"):
        return  # allaqachon tolgan

    section_labels = [
        ("university", "🎓 Universitetga topshirish"),
        ("visa", "🛂 Vizaga topshirish"),
    ]
    degree_labels = [
        ("bakalavr", "Bakalavrga topshirish"),
        ("magistr", "Magistraturaga topshirish"),
        ("doktorantura", "Doktorantura"),
    ]

    old_videos = {}
    if os.path.exists("videos_db.json"):
        try:
            with open("videos_db.json", "r", encoding="utf-8") as f:
                old_videos = json.load(f)
        except Exception:
            old_videos = {}

    for sec_key, sec_label in section_labels:
        sec_node = add_node(sec_label, None)
        section_data = old_videos.get(sec_key, {})
        for country, degrees in section_data.items():
            country_node = add_node(country, sec_node["id"])
            for deg_key, deg_label in degree_labels:
                deg_node = add_node(deg_label, country_node["id"])
                file_id = ""
                if isinstance(degrees, dict):
                    file_id = degrees.get(deg_key, "")
                if file_id:
                    add_content(deg_node["id"], {"type": "video", "file_id": file_id, "caption": ""})

    # Ishga topshirish — WORK_COUNTRIES dan
    try:
        from keyboards import WORK_COUNTRIES
        work_node = add_node("💼 Ishga topshirish", None)
        for country in WORK_COUNTRIES:
            add_node(country, work_node["id"])
    except Exception:
        pass

    # Eski sections_db.json
    if os.path.exists("sections_db.json"):
        try:
            with open("sections_db.json", "r", encoding="utf-8") as f:
                old_sections = json.load(f)
            tree = load_tree()
            for sec_name, countries in old_sections.items():
                exists = any(
                    n.get("parent_id") is None and n.get("name") == sec_name
                    for n in tree["nodes"].values()
                )
                if exists:
                    continue
                sec_node = add_node(sec_name, None)
                for country, categories in (countries or {}).items():
                    c_node = add_node(country, sec_node["id"])
                    for cat, types in (categories or {}).items():
                        cat_node = add_node(cat, c_node["id"])
                        for tp, file_id in (types or {}).items():
                            tp_node = add_node(tp, cat_node["id"])
                            if file_id:
                                add_content(tp_node["id"], {"type": "video", "file_id": file_id, "caption": ""})
        except Exception:
            pass
