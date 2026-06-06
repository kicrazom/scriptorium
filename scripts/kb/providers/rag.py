"""KB provider stub: remote RAG endpoint. NOT implemented in v2 (contract placeholder).

Remote by nature — the mode-guard refuses this in reviewer-mode before dispatch ever
reaches here. In author-mode it raises NotImplementedError until a real adapter lands (v3).
"""


def query(claim, path):
    raise NotImplementedError("rag backend is a v2 stub — implement in v3")
