#!/usr/bin/env python3
"""
extract_tree.py

Extrai a estrutura de pastas do projeto e salva:
 - uma representação em texto "tree"
 - uma representação em JSON (lista/arvore)

Uso:
  python extract_tree.py            # imprime a tree no stdout
  python extract_tree.py --json out.json
  python extract_tree.py --depth 3 --exclude ".venv,node_modules" --follow-symlinks
"""

from __future__ import annotations
import os
import json
import argparse
import fnmatch
import sys
from typing import List, Dict, Any, Optional, Tuple

DEFAULT_EXCLUDES = ["dermasync-db", "storage", "htmlcov", "node_modules", ".git", ".venv", "venv", "__pycache__", ".pytest_cache", ".idea", ".eggs", "postgres"]

def parse_args():
    p = argparse.ArgumentParser(description="Extrai estrutura de pastas (tree + json).")
    p.add_argument("--root", "-r", default=".", help="Diret�rio raiz do projeto (default: .)")
    p.add_argument("--depth", "-d", type=int, default=9999, help="M�xima profundidade (default: ilimitado)")
    p.add_argument("--exclude", "-e", default=",".join(DEFAULT_EXCLUDES),
                   help=f"Lista separada por v�rgula de nomes ou padr�es a excluir (default: {','.join(DEFAULT_EXCLUDES)})")
    p.add_argument("--follow-symlinks", action="store_true", help="Seguir symlinks (cuidado com loops)")
    p.add_argument("--json", "-j", metavar="OUT", help="Salvar a �rvore em JSON no arquivo indicado")
    p.add_argument("--text", "-t", metavar="OUT", help="Salvar a �rvore texto (ASCII) no arquivo indicado")
    p.add_argument("--show-sizes", action="store_true", help="Incluir tamanhos de arquivo em bytes no JSON")
    p.add_argument("--hidden", action="store_true", help="Incluir arquivos/dirs ocultos (come�ando com .)")
    return p.parse_args()

def build_exclude_patterns(exclude_csv: str) -> List[str]:
    patterns = [p.strip() for p in exclude_csv.split(",") if p.strip()]
    return patterns

def matches_any(name: str, patterns: List[str]) -> bool:
    for pat in patterns:
        # se o padr�o cont�m wildcard usa fnmatch, caso contr�rio compara nome exato
        if any(c in pat for c in "*?[]"):
            if fnmatch.fnmatch(name, pat):
                return True
        else:
            if name == pat:
                return True
    return False

def safe_listdir(path: str) -> List[str]:
    try:
        return os.listdir(path)
    except PermissionError:
        return []

def get_file_size(path: str) -> int:
    try:
        return os.path.getsize(path)
    except OSError:
        return 0

def build_tree(root: str, max_depth: int, exclude_patterns: List[str], follow_symlinks: bool,
               include_hidden: bool, show_sizes: bool) -> Dict[str, Any]:
    root = os.path.abspath(root)
    seen_inodes = set()

    def _recurse(path: str, depth: int) -> Dict[str, Any]:
        nonlocal seen_inodes
        name = os.path.basename(path) or path
        try:
            stat = os.stat(path, follow_symlinks=follow_symlinks)
            inode = (stat.st_dev, stat.st_ino)
        except OSError:
            inode = None

        if inode and inode in seen_inodes:
            return {"name": name, "path": path, "type": "cycle", "children": []}
        if inode:
            seen_inodes.add(inode)

        node: Dict[str, Any] = {"name": name, "path": path}
        if os.path.isdir(path):
            node["type"] = "dir"
            node["children"] = []
            
            if name == "dermasync_db":
                node["truncated"] = True
                return node

            if depth >= max_depth:
                node["truncated"] = True
                return node
            for entry in sorted(safe_listdir(path)):
                if not include_hidden and entry.startswith("."):
                    continue
                if matches_any(entry, exclude_patterns):
                    continue
                child_path = os.path.join(path, entry)
                # preven��o simples de loop se n�o seguir symlinks
                if os.path.islink(child_path) and not follow_symlinks:
                    node["children"].append({
                        "name": entry,
                        "path": child_path,
                        "type": "symlink"
                    })
                    continue
                node["children"].append(_recurse(child_path, depth + 1))
        else:
            node["type"] = "file"
            if show_sizes:
                node["size"] = get_file_size(path)
        return node

    return _recurse(root, 0)

def tree_to_ascii(node: Dict[str, Any], prefix: str = "", is_last: bool = True) -> List[str]:
    lines = []

    connector = "+-- " if is_last else "+-- "
    name = node.get("name", "")
    typ = node.get("type", "")

    extra = ""
    if typ == "dir":
        extra = "/"
    elif typ == "symlink":
        extra = " -> symlink"
    elif typ == "cycle":
        extra = " [cycle]"

    lines.append(prefix + connector + name + extra)

    children = node.get("children", [])

    if children:
        new_prefix = prefix + ("    " if is_last else "�   ")
        for i, c in enumerate(children):
            lines.extend(tree_to_ascii(c, new_prefix, i == len(children) - 1))
    elif node.get("truncated"):
        new_prefix = prefix + ("    " if is_last else "�   ")
        lines.append(new_prefix + "+-- ...")

    return lines

def main():
    args = parse_args()
    if not args.text:
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except (TypeError, AttributeError):
            # Fallback for environments where reconfigure is not available
            pass
    exclude_patterns = build_exclude_patterns(args.exclude)
    tree = build_tree(args.root, args.depth, exclude_patterns, args.follow_symlinks, args.hidden, args.show_sizes)

    ascii_lines = []
    # root line
    ascii_lines.append(tree.get("name", args.root) + "/")
    children = tree.get("children", [])
    for i, c in enumerate(children):
        ascii_lines.extend(tree_to_ascii(c, "", i == (len(children) - 1)))

    ascii_text = "\n".join(ascii_lines)

    if args.text:
        with open(args.text, "w", encoding="utf-8") as f:
            f.write(ascii_text)
    else:
        print(ascii_text)

    if args.json:
        with open(args.json, "w", encoding="utf-8") as jf:
            json.dump(tree, jf, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
