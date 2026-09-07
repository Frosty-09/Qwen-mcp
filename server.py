#!/usr/bin/env python3
"""Qwen MCP filesystem server.

This MCP server exposes controlled read/write operations for project folders.

Project sources:
1. Internal folders inside PROJECTS_DIR:
       workspace/projects/<project-name>

2. External .txt link files:
       workspace/external/<project-name>.txt
       workspace/<project-name>.txt

Each external .txt file should contain one absolute path to a project folder.
"""

import base64
import json
import os
import re
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

# pyrefly: ignore [missing-import]
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("QwenMCP")


def env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


DEFAULT_ROOT = Path(__file__).resolve().parent / "workspace"
ROOT = Path(os.getenv("QWEN_MCP_ROOT", str(DEFAULT_ROOT))).expanduser().resolve()

PROJECTS_DIR = ROOT / "projects"
EXTERNAL_DIR = ROOT / "external"


def _ensure_dirs() -> None:
    """Create workspace directories if they don't exist."""
    ROOT.mkdir(parents=True, exist_ok=True)
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
    EXTERNAL_DIR.mkdir(parents=True, exist_ok=True)

ALLOW_EXTERNAL = env_bool("QWEN_MCP_ALLOW_EXTERNAL", True)
ALLOW_CREATE_EXTERNAL_DIRS = env_bool("QWEN_MCP_ALLOW_CREATE_EXTERNAL_DIRS", True)
MAX_READ_BYTES = int(os.getenv("QWEN_MCP_MAX_READ_BYTES", str(2 * 1024 * 1024)))

NAME_INVALID = re.compile(r"[^A-Za-z0-9._-]+")


def normalize_name(name: str) -> str:
    """Normalize a project name into a safe folder/link name."""
    name = (name or "").strip().strip('"').strip("'")

    if name.lower().endswith(".txt"):
        name = name[:-4]

    name = name.replace("\\", "/").split("/")[-1]
    name = NAME_INVALID.sub("-", name).strip(" .-")

    if not name:
        raise ValueError("Project name cannot be empty.")

    if name in {".", ".."}:
        raise ValueError("Invalid project name.")

    return name


def parse_external_txt(txt: Path) -> Optional[Path]:
    """Parse a .txt project link file and return the target path."""
    try:
        raw = txt.read_text(encoding="utf-8").strip()
    except Exception:
        return None

    if not raw:
        return None

    path_str: Optional[str] = None

    # Support plain text:
    #
    #     C:\Users\you\Desktop\my-project
    #
    # Also support JSON:
    #
    #     {"path": "C:\\Users\\you\\Desktop\\my-project"}
    #
    # Also support:
    #
    #     path=C:\Users\you\Desktop\my-project
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            path_str = str(
                data.get("path")
                or data.get("location")
                or data.get("root")
                or ""
            )
        elif isinstance(data, str):
            path_str = data
    except Exception:
        first = raw.splitlines()[0].strip()
        if first.lower().startswith("path="):
            first = first[5:].strip()
        path_str = first

    if not path_str:
        return None

    path_str = path_str.strip().strip('"').strip("'")

    if path_str.startswith("file:///"):
        path_str = path_str[len("file:///"):]
    elif path_str.startswith("file://"):
        path_str = path_str[len("file://"):]

    p = Path(path_str).expanduser()

    if not p.is_absolute():
        p = (txt.parent / p).expanduser()

    try:
        return p.resolve()
    except Exception:
        return p.absolute()


def external_txt_paths(name: str) -> List[Path]:
    """Locations where an external project link file may exist."""
    safe = normalize_name(name)
    return [
        EXTERNAL_DIR / f"{safe}.txt",
        ROOT / f"{safe}.txt",
    ]


def get_project_root(project: str, create: bool = False) -> Path:
    """Resolve a project name to a real directory."""
    safe = normalize_name(project)
    internal = PROJECTS_DIR / safe

    if internal.is_dir():
        return internal.resolve()

    if ALLOW_EXTERNAL:
        for txt in external_txt_paths(safe):
            if txt.is_file():
                target = parse_external_txt(txt)

                if target is None:
                    raise ValueError(
                        f"External project file {txt} does not contain a valid path."
                    )

                if target.is_file():
                    target = target.parent

                if target.exists():
                    return target.resolve()

                if create and ALLOW_CREATE_EXTERNAL_DIRS:
                    target.mkdir(parents=True, exist_ok=True)
                    return target.resolve()

                raise FileNotFoundError(
                    f"External project '{safe}' points to missing path: {target}"
                )

    if create:
        internal.mkdir(parents=True, exist_ok=True)
        return internal.resolve()

    raise FileNotFoundError(
        f"Project '{safe}' not found. Use qwen_create_project or add an external .txt file."
    )


def safe_join(root: Path, rel: str) -> Path:
    """Join a relative path to a project root without allowing path traversal."""
    root = root.resolve()
    rel = (rel or "").strip().replace("\\", "/")

    while rel.startswith("/"):
        rel = rel[1:]

    if rel in ("", ".", "./"):
        return root

    candidate = (root / rel).resolve()

    try:
        candidate.relative_to(root)
    except ValueError:
        raise PermissionError(f"Path escapes project root: {rel}")

    return candidate


def relative_posix(path: Path, root: Path) -> str:
    """Return a POSIX-style relative path if possible."""
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except Exception:
        return path.as_posix()


@mcp.tool()
def qwen_status() -> Dict[str, Any]:
    """Show where Qwen MCP stores projects and whether external projects are allowed."""
    return {
        "ok": True,
        "root": str(ROOT),
        "projects_dir": str(PROJECTS_DIR),
        "external_dir": str(EXTERNAL_DIR),
        "allow_external": ALLOW_EXTERNAL,
        "allow_create_external_dirs": ALLOW_CREATE_EXTERNAL_DIRS,
        "max_read_bytes": MAX_READ_BYTES,
    }


@mcp.tool()
def qwen_create_project(name: str) -> Dict[str, Any]:
    """Create a project folder inside the Qwen MCP projects directory."""
    safe = normalize_name(name)
    path = PROJECTS_DIR / safe
    path.mkdir(parents=True, exist_ok=True)

    return {
        "ok": True,
        "project": safe,
        "path": str(path),
    }


@mcp.tool()
def qwen_register_external_project(
    name: str,
    path: str,
    create: bool = False,
) -> Dict[str, Any]:
    """Register an external project by saving its absolute path into a .txt link file."""
    safe = normalize_name(name)

    target = Path(path).expanduser()

    if not target.is_absolute():
        target = (Path.cwd() / target).expanduser()

    target = target.resolve()

    if target.parent == target:
        raise PermissionError(
            f"Refusing to register a filesystem root as a project: {target}"
        )

    if create:
        if target.is_file():
            raise FileExistsError(
                f"Target is a file, not a directory: {target}"
            )
        target.mkdir(parents=True, exist_ok=True)

    txt = EXTERNAL_DIR / f"{safe}.txt"
    txt.parent.mkdir(parents=True, exist_ok=True)
    txt.write_text(str(target), encoding="utf-8")

    return {
        "ok": True,
        "project": safe,
        "external_file": str(txt),
        "target": str(target),
        "exists": target.exists(),
    }


@mcp.tool()
def qwen_list_projects() -> Dict[str, Any]:
    """List internal projects and external .txt-linked projects."""
    items: List[Dict[str, Any]] = []
    seen = set()

    if PROJECTS_DIR.exists():
        for entry in sorted(PROJECTS_DIR.iterdir()):
            if entry.is_dir():
                items.append(
                    {
                        "name": entry.name,
                        "type": "internal",
                        "path": str(entry),
                        "exists": True,
                    }
                )
                seen.add(entry.name)

    if ALLOW_EXTERNAL:
        txt_files = sorted(EXTERNAL_DIR.glob("*.txt")) + sorted(ROOT.glob("*.txt"))

        for txt in txt_files:
            name = txt.stem

            if name in seen:
                continue

            target = parse_external_txt(txt)

            items.append(
                {
                    "name": name,
                    "type": "external",
                    "source": str(txt),
                    "path": str(target) if target else None,
                    "exists": bool(target and target.exists()),
                }
            )

            seen.add(name)

    return {
        "ok": True,
        "root": str(ROOT),
        "projects_dir": str(PROJECTS_DIR),
        "external_dir": str(EXTERNAL_DIR),
        "allow_external": ALLOW_EXTERNAL,
        "projects": items,
    }


@mcp.tool()
def qwen_resolve_project(project: str) -> Dict[str, Any]:
    """Resolve a project name to its actual root directory."""
    root = get_project_root(project, create=False)

    return {
        "ok": True,
        "project": normalize_name(project),
        "root": str(root),
    }


@mcp.tool()
def qwen_list_files(
    project: str,
    path: str = "",
    pattern: str = "*",
    recursive: bool = False,
) -> Dict[str, Any]:
    """List files and directories inside a project."""
    root = get_project_root(project, create=False)
    base = safe_join(root, path)

    if not base.exists():
        return {
            "ok": True,
            "project": normalize_name(project),
            "root": str(root),
            "path": path or ".",
            "pattern": pattern,
            "recursive": recursive,
            "entries": [],
        }

    if base.is_file():
        return {
            "ok": True,
            "project": normalize_name(project),
            "root": str(root),
            "path": path or ".",
            "pattern": pattern,
            "recursive": recursive,
            "entries": [
                {
                    "path": relative_posix(base, root),
                    "type": "file",
                    "size": base.stat().st_size,
                }
            ],
        }

    iterator = base.rglob(pattern) if recursive else base.glob(pattern)
    entries: List[Dict[str, Any]] = []

    try:
        items = sorted(iterator)
    except PermissionError:
        items = []

    for item in items:
        try:
            if item.is_dir():
                entries.append(
                    {
                        "path": relative_posix(item, root) + "/",
                        "type": "directory",
                    }
                )
            elif item.is_file():
                entries.append(
                    {
                        "path": relative_posix(item, root),
                        "type": "file",
                        "size": item.stat().st_size,
                    }
                )
        except PermissionError:
            continue

    return {
        "ok": True,
        "project": normalize_name(project),
        "root": str(root),
        "path": path or ".",
        "pattern": pattern,
        "recursive": recursive,
        "entries": entries,
    }


@mcp.tool()
def qwen_read_file(project: str, path: str) -> Dict[str, Any]:
    """Read a file from a project. Returns UTF-8 text when possible, otherwise base64."""
    root = get_project_root(project, create=False)
    full = safe_join(root, path)

    if not full.exists():
        raise FileNotFoundError(f"File not found: {full}")

    if full.is_dir():
        raise IsADirectoryError(f"Path is a directory: {full}")

    size = full.stat().st_size

    if size <= MAX_READ_BYTES:
        data = full.read_bytes()

        try:
            content = data.decode("utf-8")

            return {
                "ok": True,
                "project": normalize_name(project),
                "path": str(full),
                "relative_path": relative_posix(full, root),
                "encoding": "utf-8",
                "content": content,
                "size": size,
                "truncated": False,
            }
        except UnicodeDecodeError:
            return {
                "ok": True,
                "project": normalize_name(project),
                "path": str(full),
                "relative_path": relative_posix(full, root),
                "encoding": "base64",
                "content": base64.b64encode(data).decode("ascii"),
                "size": size,
                "truncated": False,
            }

    with full.open("rb") as fh:
        data = fh.read(MAX_READ_BYTES)

    return {
        "ok": True,
        "project": normalize_name(project),
        "path": str(full),
        "relative_path": relative_posix(full, root),
        "encoding": "base64",
        "content": base64.b64encode(data).decode("ascii"),
        "size": size,
        "read_bytes": MAX_READ_BYTES,
        "truncated": True,
    }


@mcp.tool()
def qwen_write_file(
    project: str,
    path: str,
    content: str,
    encoding: str = "utf-8",
    create_dirs: bool = True,
) -> Dict[str, Any]:
    """Write content to a file inside a project. Use encoding='base64' for binary data."""
    root = get_project_root(project, create=True)
    full = safe_join(root, path)

    if create_dirs:
        full.parent.mkdir(parents=True, exist_ok=True)

    if encoding == "base64":
        full.write_bytes(base64.b64decode(content))
    else:
        full.write_text(content, encoding=encoding)

    return {
        "ok": True,
        "project": normalize_name(project),
        "path": str(full),
        "relative_path": relative_posix(full, root),
        "bytes": full.stat().st_size,
    }


@mcp.tool()
def qwen_append_file(
    project: str,
    path: str,
    content: str,
    encoding: str = "utf-8",
    create_dirs: bool = True,
) -> Dict[str, Any]:
    """Append content to a file inside a project. Creates the file if missing."""
    root = get_project_root(project, create=True)
    full = safe_join(root, path)

    if create_dirs:
        full.parent.mkdir(parents=True, exist_ok=True)

    if encoding == "base64":
        with full.open("ab") as fh:
            fh.write(base64.b64decode(content))
    else:
        with full.open("a", encoding=encoding) as fh:
            fh.write(content)

    return {
        "ok": True,
        "project": normalize_name(project),
        "path": str(full),
        "relative_path": relative_posix(full, root),
        "bytes": full.stat().st_size,
    }


@mcp.tool()
def qwen_delete_file(
    project: str,
    path: str,
    recursive: bool = False,
) -> Dict[str, Any]:
    """Delete a file or directory inside a project. Set recursive=true to delete directories."""
    root = get_project_root(project, create=False)
    full = safe_join(root, path)

    if not full.exists():
        raise FileNotFoundError(f"Path not found: {full}")

    if full == root:
        raise PermissionError("Cannot delete the project root directory.")

    if full.is_dir():
        if not recursive:
            raise IsADirectoryError(
                f"Path is a directory. Set recursive=true to delete: {full}"
            )
        shutil.rmtree(full)
    else:
        full.unlink()

    return {
        "ok": True,
        "project": normalize_name(project),
        "deleted": str(full),
        "relative_path": relative_posix(full, root),
    }


@mcp.tool()
def qwen_rename_file(
    project: str,
    old_path: str,
    new_path: str,
) -> Dict[str, Any]:
    """Rename or move a file or directory inside a project."""
    root = get_project_root(project, create=False)
    src = safe_join(root, old_path)
    dst = safe_join(root, new_path)

    if not src.exists():
        raise FileNotFoundError(f"Source not found: {src}")

    if dst.exists():
        raise FileExistsError(f"Destination already exists: {dst}")

    dst.parent.mkdir(parents=True, exist_ok=True)
    src.rename(dst)

    return {
        "ok": True,
        "project": normalize_name(project),
        "old_path": relative_posix(src, root),
        "new_path": relative_posix(dst, root),
    }


@mcp.tool()
def qwen_search_files(
    project: str,
    query: str,
    path: str = "",
    pattern: str = "*",
    case_sensitive: bool = False,
    max_results: int = 100,
) -> Dict[str, Any]:
    """Search for text inside project files. Returns matching lines with file paths and line numbers."""
    root = get_project_root(project, create=False)
    base = safe_join(root, path)

    if not base.exists():
        return {
            "ok": True,
            "project": normalize_name(project),
            "query": query,
            "matches": [],
            "total": 0,
            "truncated": False,
        }

    flags = 0 if case_sensitive else re.IGNORECASE
    compiled = re.compile(re.escape(query), flags)

    matches: List[Dict[str, Any]] = []
    files = [base] if base.is_file() else sorted(base.rglob(pattern))

    for f in files:
        if not f.is_file():
            continue

        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except (PermissionError, OSError):
            continue

        for i, line in enumerate(text.splitlines(), start=1):
            if compiled.search(line):
                matches.append({
                    "file": relative_posix(f, root),
                    "line": i,
                    "content": line.rstrip(),
                })

                if len(matches) >= max_results:
                    return {
                        "ok": True,
                        "project": normalize_name(project),
                        "query": query,
                        "matches": matches,
                        "total": len(matches),
                        "truncated": True,
                    }

    return {
        "ok": True,
        "project": normalize_name(project),
        "query": query,
        "matches": matches,
        "total": len(matches),
        "truncated": False,
    }


def main():
    _ensure_dirs()
    mcp.run()


if __name__ == "__main__":
    main()