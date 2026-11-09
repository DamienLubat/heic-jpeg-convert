"""Garde-fous de confidentialité : le programme ne doit ni ouvrir de connexion réseau ni lancer de programme externe,
et le dépôt ne doit contenir ni photo ni donnée personnelle."""
import ast
import re
import subprocess
from pathlib import Path

from conftest import PROGRAM, ROOT

FORBIDDEN_IMPORTS = {"socket", "ssl", "urllib", "http", "requests", "httpx", "ftplib", "smtplib", "telnetlib", "subprocess",
                     "webbrowser", "xmlrpc", "asyncio", "aiohttp"}


def imported_modules(tree):
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            yield from (a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            yield node.module.split(".")[0]


def test_program_imports_no_network_or_process_module():
    tree = ast.parse(PROGRAM.read_text(encoding="utf-8"))
    assert FORBIDDEN_IMPORTS.isdisjoint(imported_modules(tree)), sorted(FORBIDDEN_IMPORTS & set(imported_modules(tree)))


def test_program_has_no_dynamic_execution_or_shell_call():
    tree = ast.parse(PROGRAM.read_text(encoding="utf-8"))
    calls = {n.func.id for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    attrs = {(n.func.value.id, n.func.attr) for n in ast.walk(tree)
             if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name)}
    assert not calls & {"eval", "exec", "compile", "__import__"}
    assert not attrs & {("os", "system"), ("os", "popen"), ("os", "startfile")}


def test_repository_contains_no_photo():
    photos = [p for p in ROOT.rglob("*") if p.is_file() and ".git" not in p.parts and p.suffix.lower() in
              {".heic", ".heif", ".jpg", ".jpeg", ".jpe", ".jfif", ".jxl", ".avif", ".png", ".tif", ".tiff", ".dng", ".cr2", ".nef"}]
    assert not photos, photos


def test_no_absolute_user_path_or_email_in_text_files():
    pattern = re.compile(r"[A-Za-z]:\\Users\\|/home/[a-z]|/Users/[A-Za-z]|[\w.+-]+@[\w-]+\.[\w.]+")
    allowed = {"noreply@github.com"}
    hits = []
    for p in ROOT.rglob("*"):
        if not p.is_file() or ".git" in p.parts or "__pycache__" in p.parts or p.suffix in {".pyc"}:
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for m in pattern.finditer(text):
            if m.group(0) not in allowed:
                hits.append((str(p.relative_to(ROOT)), m.group(0)))
    assert not hits, hits
