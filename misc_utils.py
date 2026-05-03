from pathlib import Path
import re
import shutil

def reset_dir(path):
    """Deletes the directory if it exists and creates a new empty one."""
    p = Path(path)
    if p.exists():
        shutil.rmtree(p)
    p.mkdir(parents=True, exist_ok=True)


TAG_RE = re.compile(r"<[^>]+>")

def remove_tags(text: str) -> str:
    """Removes HTML-like tags from the input text."""
    return TAG_RE.sub("", text)