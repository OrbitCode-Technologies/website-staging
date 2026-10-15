"""Refresh previews from public PRs without executing proposed code."""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

SOURCE = "OrbitCode-Technologies/OrbitCode-Technologies.github.io"
ROOT = Path(__file__).resolve().parents[2]


def run(*args, **kwargs):
    return subprocess.check_output(args, text=True, **kwargs).strip()


EXTENSIONS = {
    ".html", ".css", ".js", ".mjs", ".json", ".svg", ".png", ".jpg",
    ".jpeg", ".webp", ".gif", ".ico", ".avif", ".woff", ".woff2",
    ".ttf", ".otf", ".pdf", ".webmanifest", ".mp4", ".webm",
}
def copy_site(source, destination):
    if not (source / "index.html").is_file():
        raise ValueError("A static index.html is required")
    destination.mkdir(parents=True)
    total = 0
    for item in source.rglob("*"):
        relative = item.relative_to(source)
        if any(part.startswith(".") or part in {"node_modules", "docs"}
               for part in relative.parts):
            continue
        if item.is_symlink():
            raise ValueError(f"Symlinks are not allowed: {relative}")
        if not item.is_file() or item.suffix.lower() not in EXTENSIONS:
            continue
        total += item.stat().st_size
        if total > 100 * 1024 * 1024:
            raise ValueError("Preview exceeds the 100 MiB size limit")
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(item, target)
        if target.suffix.lower() == ".html":
            html = target.read_text(encoding="utf-8")
            tag = '<meta name="robots" content="noindex, nofollow">'
            if re.search(r"<head(?:\s[^>]*)?>", html, re.I):
                html = re.sub(r"(<head(?:\s[^>]*)?>)",
                              lambda match: match[0] + tag, html, count=1, flags=re.I)
            else:
                html = tag + html
            target.write_text(html, encoding="utf-8")


def main():
    pages = json.loads(run("gh", "api", f"repos/{SOURCE}/pulls?state=open&base=main&per_page=100",
                           "--paginate", "--slurp"))
    prs = [pr for page in pages for pr in page
           if pr["head"]["repo"] and pr["head"]["repo"]["full_name"] == SOURCE]
    state_path = ROOT / ".preview-state.json"
    previous = json.loads(state_path.read_text()) if state_path.exists() else {}
    current = {}
    public = ROOT / "public"
    for pr in prs:
        number = str(int(pr["number"]))
        sha = pr["head"]["sha"]
        target = public / f"pr-{number}"
        if previous.get(number) == sha and target.exists():
            current[number] = sha
            continue
        with tempfile.TemporaryDirectory(prefix="website-preview-") as temporary:
            source = Path(temporary) / "source"
            run("git", "init", "-q", str(source))
            run("git", "-C", str(source), "fetch", "--depth=1",
                f"https://github.com/{SOURCE}.git", sha)
            run("git", "-C", str(source), "-c", "core.hooksPath=/dev/null",
                "checkout", "--detach", "FETCH_HEAD")
            prepared = Path(temporary) / "prepared"
            copy_site(source, prepared)
            if target.exists():
                shutil.rmtree(target)
            shutil.move(str(prepared), str(target))
        current[number] = sha
    for target in public.glob("pr-*"):
        if target.is_dir() and target.name[3:] not in current:
            shutil.rmtree(target)
    state_path.write_text(json.dumps(current, indent=2, sort_keys=True) + "\n")
    print(f"Prepared {len(current)} open PR preview(s)")


if __name__ == "__main__":
    main()
