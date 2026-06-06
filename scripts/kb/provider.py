"""KB provider registry + dispatch. Maps a backend name to its query(claim, path) callable."""
from scripts.kb.providers import folder, obsidian, rag, cag

REGISTRY = {
    "folder": folder.query,
    "obsidian": obsidian.query,
    "rag": rag.query,
    "cag": cag.query,
}


def get_provider(backend):
    if backend not in REGISTRY:
        raise ValueError(f"unknown KB backend: {backend!r} (have {sorted(REGISTRY)})")
    return REGISTRY[backend]
