"""QRU Automatic Knowledge Extraction™ (MO-043) — deterministic, $0 AI, Knowledge-First.

Structures an imported Founder document's OWN verified text into Knowledge Record fields.
It never invents facts: every populated field is a verbatim excerpt or a direct, structural
derivation from the source. Fields that cannot be found in the source are left EMPTY for the
Founder to complete in the Promotion Pipeline™ — the factory does not hallucinate them.

Escalates (returns sufficient=False) when the source is unreadable or too thin to extract.
"""
import re

_MIN_CHARS = 200
_MIN_SENTENCES = 2

_WHY = ("matters", "important", "because", "helps", "impact", "so that", "essential", "crucial", "benefit")
_EXAMPLE = ("for example", "for instance", "e.g.", "such as", "imagine", "consider", "case in point")
_ANALOGY = ("like ", "as if", "similar to", "think of", "just as", "analogous", "resembles", "akin to")
_STOP = set("the a an and or but of to in on for with is are was were be been being this that these those it "
            "as at by from into over under again more most such no not only own same so than too very can will "
            "just should now their there here what which who whom whose when where why how you your they them we our"
            .split())


def _clean(t):
    return re.sub(r"[ \t]+", " ", (t or "").replace("\r", "")).strip()


def _sentences(text):
    parts = re.split(r"(?<=[.!?])\s+", _clean(text).replace("\n", " "))
    return [s.strip() for s in parts if len(s.strip()) >= 12]


def _paragraphs(text):
    return [p.strip() for p in re.split(r"\n\s*\n", text or "") if len(p.strip()) >= 40]


def _first_match(sentences, needles):
    low = [s.lower() for s in sentences]
    for i, s in enumerate(low):
        if any(n in s for n in needles):
            return sentences[i]
    return None


_QWORDS = {"what", "why", "how", "which", "when", "where", "who", "whom", "whose", "this", "that", "it", "there", "these", "those"}


def _vocabulary(text):
    """Detect explicit definitions: 'Term: definition', 'Term - definition', 'Term means ...'."""
    vocab, seen = [], set()
    for line in (text or "").splitlines():
        line = line.strip().lstrip("-*• ").strip()
        if not line or len(line) > 200 or line.endswith("?"):
            continue
        m = re.match(r"^([A-Z][\w \-/]{1,40}?)\s*[:\u2013\u2014]\s+(.{15,180})$", line)
        if not m:
            m = re.match(r"^([A-Z][\w \-/]{1,40}?)\s+(?:is|means|refers to|are)\s+(.{15,150})$", line)
        if m:
            term = m.group(1).strip()
            if term.lower() in _QWORDS or term.lower() in seen or len(term.split()) > 5:
                continue
            seen.add(term.lower())
            vocab.append({"term": term, "definition": m.group(2).strip().rstrip(".")})
        if len(vocab) >= 8:
            break
    return vocab


def _memory_sentence(sentences, title):
    cands = [s for s in sentences if 6 <= len(s.split()) <= 18 and s.endswith(".")]
    tl = (title or "").lower()
    for s in cands:
        if any(w in s.lower() for w in tl.split() if len(w) > 3):
            return s
    return cands[0] if cands else (sentences[0] if sentences else "")


def _tags(text, title):
    words = re.findall(r"[A-Za-z][A-Za-z\-]{3,}", (text or "").lower())
    freq = {}
    for w in words:
        if w in _STOP:
            continue
        freq[w] = freq.get(w, 0) + 1
    top = sorted(freq.items(), key=lambda x: -x[1])[:8]
    tags = [t for t, _c in top]
    for w in re.findall(r"[A-Za-z]{4,}", (title or "").lower()):
        if w not in tags and w not in _STOP:
            tags.insert(0, w)
    return tags[:10]


def extract_fields(text, title=""):
    """Deterministically structure the source text into GUS fields. Returns a dict:
    {sufficient, reason, fields, extracted_count, required_complete}."""
    text = _clean(text)
    sentences = _sentences(text)
    if len(text) < _MIN_CHARS or len(sentences) < _MIN_SENTENCES:
        return {"sufficient": False,
                "reason": "The source has too little readable text to extract a Knowledge Record.",
                "fields": {}, "extracted_count": 0, "required_complete": False}

    question = None
    qm = re.search(r"\b((?:What|Why|How|Which|When|Where|Who)\b[^?]{3,160}\?)", text)
    if qm:
        question = qm.group(1).strip()
    else:
        question = next((s for s in sentences if s.rstrip().endswith("?")), None)
    if not question:
        question = f"What is {(title or 'this topic')}?"

    # Simple answer = the first substantive paragraph (verbatim), capped.
    paras = _paragraphs(text)
    body = paras[0] if paras else " ".join(sentences[:3])
    # If the first paragraph is just the title/heading, use the next.
    if title and body.strip().lower() == title.strip().lower() and len(paras) > 1:
        body = paras[1]
    simple_answer = body[:400].strip()

    verified_truth = " ".join(sentences[:3])[:600].strip()
    why = _first_match(sentences, _WHY)
    example = _first_match(sentences, _EXAMPLE)
    analogy = _first_match(sentences, _ANALOGY)
    memory = _memory_sentence(sentences, title)
    vocab = _vocabulary(text)

    fields = {
        "the_question": question,
        "simple_answer": simple_answer,
        "verified_truth": verified_truth,
        "why_it_matters": why or "",
        "real_world_example": example or "",
        "everyday_analogy": analogy or "",
        "memory_sentence": memory or "",
        "qru_translation": "",   # faithful re-translation is a Founder/structuring step — never invented
        "deep_roots": "",
        "key_vocabulary": vocab,
        "tags": _tags(text, title),
    }
    extracted = sum(1 for k in ("the_question", "simple_answer", "verified_truth", "why_it_matters",
                                "real_world_example", "everyday_analogy", "memory_sentence") if fields.get(k))
    extracted += 1 if vocab else 0
    required_complete = bool(fields["the_question"] and fields["simple_answer"] and fields["why_it_matters"])
    return {"sufficient": True, "reason": None, "fields": fields,
            "extracted_count": extracted, "required_complete": required_complete}
