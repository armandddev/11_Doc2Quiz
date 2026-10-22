import html
import xml.etree.ElementTree as ET
from datetime import date

import pytest

from Doc2Quiz.service import qcm_export as ex

TODAY = date(2026, 10, 14)

# QCM 1 : distracteurs avec TOUS les caractères spéciaux GIFT
QCM_SPECIAL = {
    "questions": [{
        "enonce": "Que vaut x ? {indice} # note : voir cours ~ chap. 2 = important",
        "reponses": [
            {"texte": "x = y ~ z {w} # v : u \\ fin", "correcte": False, "feedback": "Faux : a=b # non"},
            {"texte": "x = 2", "correcte": True, "feedback": "Correct"},
            {"texte": "Aucune", "correcte": False, "feedback": ""},
        ],
    }]
}

# QCM 2 : accents / ligatures / apostrophes / retour à la ligne
QCM_ACCENTS = {
    "questions": [{
        "enonce": "Quelle est la capitale de l'Équateur ?\nIndice : cœur des Andes",
        "reponses": [
            {"texte": "Quito", "correcte": True, "feedback": "Oui, à 2 850 m d'altitude – très élevée"},
            {"texte": "Guayaquil", "correcte": False, "feedback": "Plus grande ville, pas la capitale"},
            {"texte": "Cuenca", "correcte": False, "feedback": "Ville coloniale, déjà vue en cours"},
        ],
    }]
}

# QCM 3 : réponses multiples + & < >
QCM_MULTI = {
    "questions": [
        {
            "enonce": "Quelles expressions sont vraies ? (a < b) & (b > c)",
            "reponses": [
                {"texte": "1 < 2 & 3 > 2", "correcte": True, "feedback": "Vrai : <ok> & co"},
                {"texte": "2 > 3", "correcte": False, "feedback": "Faux"},
                {"texte": "5 >= 5", "correcte": True, "feedback": "Vrai"},
                {"texte": "0 > 1", "correcte": False, "feedback": ""},
            ],
        },
        {
            "enonce": "Question simple",
            "reponses": [
                {"texte": "Oui", "correcte": True, "feedback": "ok"},
                {"texte": "Non", "correcte": False, "feedback": "ko"},
            ],
        },
    ]
}

ALL = [QCM_SPECIAL, QCM_ACCENTS, QCM_MULTI]


# Parseur GIFT (sert de "round-trip" pour prouver l'échappement)
def _first_unescaped(s, ch):
    i = 0
    while i < len(s):
        if s[i] == "\\":
            i += 2
            continue
        if s[i] == ch:
            return i
        i += 1
    return -1


def _unescape(s):
    return ex.re.sub(r"\\(.)", lambda m: "\n" if m.group(1) == "n" else m.group(1), s)


def parse_gift(gift):
    out = []
    for block in gift.strip().split("\n\n"):
        lines = block.split("\n")
        head = lines[0]
        assert head.endswith(" {") and lines[-1] == "}"
        body = head[:-2]
        start = _first_unescaped(body, ":")
        assert body[start:start + 2] == "::"
        end = start + 2 + _first_unescaped(body[start + 2:], ":")
        question = _unescape(body[end + 2:].strip())
        answers = []
        for line in lines[1:-1]:
            assert line[0] in "=~"
            rest = line[1:]
            if rest.startswith("%"):
                rest = rest[rest.index("%", 1) + 1:]
            h = _first_unescaped(rest, "#")
            text, fb = (rest, "") if h < 0 else (rest[:h], rest[h + 1:])
            answers.append((_unescape(text), _unescape(fb), line[0]))
        out.append((question, answers))
    return out


@pytest.mark.parametrize("qcm", ALL)
def test_gift_roundtrip(qcm):
    parsed = parse_gift(ex.build_gift(qcm))
    assert len(parsed) == len(qcm["questions"])
    for (q, answers), src in zip(parsed, qcm["questions"]):
        assert q == src["enonce"]
        assert [a[0] for a in answers] == [r["texte"] for r in src["reponses"]]
        assert [a[1] for a in answers] == [r["feedback"] for r in src["reponses"]]


def test_gift_special_chars_escaped():
    gift = ex.build_gift(QCM_SPECIAL)
    assert r"x \= y \~ z \{w\} \# v \: u \\ fin" in gift
    assert "=x \\= 2" in gift  


def test_gift_multi_weights_and_feedback():
    gift = ex.build_gift(QCM_MULTI)
    assert "~%50%" in gift and "~%-50%" in gift
    assert "#Vrai" in gift


@pytest.mark.parametrize("qcm", ALL)
def test_xml_valid_and_roundtrip(qcm):
    data = ex.build_moodle_xml(qcm)
    ex.validate_moodle_xml(data)
    root = ET.fromstring(data)
    for qe, src in zip(root.findall("question"), qcm["questions"]):
        text = qe.findtext("questiontext/text")
        assert html.unescape(text).replace("<br>", "\n") == src["enonce"]
        answers = qe.findall("answer")
        assert [html.unescape(a.findtext("text")) for a in answers] == [r["texte"] for r in src["reponses"]]
        assert [html.unescape(a.findtext("feedback/text")) for a in answers] == [r["feedback"] for r in src["reponses"]]


def test_xml_single_flag_and_fractions():
    root = ET.fromstring(ex.build_moodle_xml(QCM_MULTI))
    q1, q2 = root.findall("question")
    assert q1.findtext("single") == "false"
    assert [a.get("fraction") for a in q1.findall("answer")] == ["50", "-50", "50", "-50"]
    assert q2.findtext("single") == "true"
    assert [a.get("fraction") for a in q2.findall("answer")] == ["100", "0"]


def test_xml_control_chars_stripped():
    qcm = {"questions": [{"enonce": "Q\x00\x0b?", "reponses": [
        {"texte": "A\x1f", "correcte": True}, {"texte": "B", "correcte": False}]}]}
    ex.validate_moodle_xml(ex.build_moodle_xml(qcm))


def test_validation_rejects_broken_xml():
    with pytest.raises(ex.ExportError):
        ex.validate_moodle_xml(b"<quiz><question></quiz>")
    with pytest.raises(ex.ExportError):
        ex.validate_moodle_xml(b"<quiz/>")


def test_failsafe_no_invalid_file_written(tmp_path, monkeypatch):
    monkeypatch.setattr(ex, "build_moodle_xml", lambda q: b"<quiz><oops>")
    res = ex.export_all(QCM_ACCENTS, "Cours", out_dir=tmp_path, today=TODAY)
    assert res.xml_path is None and "xml" in res.errors
    assert not list(tmp_path.glob("*.xml"))
    assert res.gift_path is not None  


@pytest.mark.parametrize("bad", [
    {"questions": []},
    {"questions": [{"enonce": "Q", "reponses": [{"texte": "A", "correcte": True}]}]},
    {"questions": [{"enonce": "Q", "reponses": [{"texte": "A", "correcte": False}, {"texte": "B", "correcte": False}]}]},
])
def test_invalid_input_reports_errors_for_both_formats(tmp_path, bad):
    res = ex.export_all(bad, "x", out_dir=tmp_path, today=TODAY)
    assert set(res.errors) == {"gift", "xml"}
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("name,expected", [
    ("Cours d'Algo & Structures (L2) — v2.0 !", "cours-d-algo-structures-l2-v2-0"),
    ("Économie générale : Cœur & Âme", "economie-generale-coeur-ame"),
    ("   ", "qcm"),
    ("!!!", "qcm"),
    ("../../etc/passwd", "etc-passwd"),
])
def test_slugify(name, expected):
    assert ex.slugify(name) == expected


def test_export_filename_and_files(tmp_path):
    res = ex.export_all(QCM_MULTI, "Cours d'Algo & Structures (L2)", out_dir=tmp_path, today=TODAY)
    assert not res.errors
    assert res.gift_path.name == "cours-d-algo-structures-l2_2026-10-14.txt"
    assert res.xml_path.name == "cours-d-algo-structures-l2_2026-10-14.xml"
    assert res.gift_path.read_text(encoding="utf-8").startswith("::Q1")
    ET.parse(res.xml_path)  # relisible par le parseur standard


# Format réel de l'application : liste de {"type","question","options","bonne_reponse"}

QCM_APP = [
    {"type": "qcm", "question": "Capitale de la France ?",
     "options": ["A) Paris", "B) Lyon", "C) Nice", "D) Lille"],
     "bonne_reponse": "A", "explication": "Paris est la capitale."},
    {"type": "exercice", "question": "Démontrez que 1+1=2."},
    {"type": "qcm", "question": "2 + 2 = ?", "options": ["3", "4", "5"], "bonne_reponse": "4"},
    {"type": "qcm", "question": "Quel opérateur ? {a} ~ b",
     "options": ["x = y", "c ~ d", "e # f"], "bonne_reponse": "B) c ~ d",
     "feedbacks": {"A": "Non, affectation", "B": "Oui", "C": "Commentaire"}},
]


def test_app_format_skips_non_qcm_and_strips_prefixes():
    qs = ex._normalize(QCM_APP)
    assert len(qs) == 3  # l'exercice est ignoré
    assert [a.text for a in qs[0].answers] == ["Paris", "Lyon", "Nice", "Lille"]
    assert [a.correct for a in qs[0].answers] == [True, False, False, False]
    assert [a.correct for a in qs[1].answers] == [False, True, False]
    assert [a.correct for a in qs[2].answers] == [False, True, False]


def test_app_format_feedbacks():
    qs = ex._normalize(QCM_APP)
    assert qs[0].answers[0].feedback == "Paris est la capitale."  # explication globale -> bonne réponse
    assert qs[0].answers[1].feedback == ""
    assert [a.feedback for a in qs[2].answers] == ["Non, affectation", "Oui", "Commentaire"]


def test_app_format_exports_valid_gift_and_xml(tmp_path):
    res = ex.export_all(QCM_APP, "Cours d'Algo & Structures", out_dir=tmp_path, today=TODAY)
    assert not res.errors
    assert len(parse_gift(res.gift_path.read_text(encoding="utf-8"))) == 3
    assert len(ET.parse(res.xml_path).getroot().findall("question")) == 3


@pytest.mark.parametrize("bonne", ["B", "b", "B)", "B. Lyon", "Lyon", 1, ["Lyon"]])
def test_bonne_reponse_variants(bonne):
    q = [{"type": "qcm", "question": "Q", "options": ["A) Paris", "B) Lyon"], "bonne_reponse": bonne}]
    assert [a.correct for a in ex._normalize(q)[0].answers] == [False, True]


def test_bonne_reponse_unknown_is_an_error():
    q = [{"type": "qcm", "question": "Q", "options": ["Paris", "Lyon"], "bonne_reponse": "Marseille"}]
    with pytest.raises(ex.ExportError):
        ex._normalize(q)
    with pytest.raises(ex.ExportError):
        ex._normalize([{"type": "qcm", "question": "Q", "options": ["Paris", "Lyon"], "bonne_reponse": ""}])


def test_only_non_qcm_questions_is_an_error():
    with pytest.raises(ex.ExportError):
        ex._normalize([{"type": "exercice", "question": "Q"}])


def test_prefixes_kept_when_not_a_full_abc_sequence():
    q = [{"type": "qcm", "question": "Q", "options": ["A. fin de phrase", "autre"], "bonne_reponse": "autre"}]
    assert [a.text for a in ex._normalize(q)[0].answers] == ["A. fin de phrase", "autre"]


# Format réel produit par core.generation_qcm :
# {"question","options":["A. …"],"correct":"A","type":"qcm","section":{…}, ("feedbacks")}

QCM_CORE = [
    {"question": "Que fait RSA ?", "options": ["A. Chiffre", "B. Hache", "C. Compresse", "D. Trie"],
     "correct": "A", "type": "qcm", "section": {"title": "RSA", "text": "…"},
     "feedbacks": ["Oui, chiffrement asymétrique", "Non, ce n'est pas un hash", "Non", "Non"]},
    # sortie LLM non-JSON conservée par core.py : options vides, correct vide
    {"question": "texte brut du LLM", "options": [], "correct": "", "type": "qcm"},
    {"question": "a ~ b {c}", "options": ["A. x = 1", "B. y # 2", "C. z : 3", "D. w"],
     "correct": "C", "type": "qcm"},
]


def test_core_format_strict_mode_raises_on_bad_question():
    with pytest.raises(ex.ExportError, match="Question 2"):
        ex._normalize(QCM_CORE)


def test_core_format_tolerant_export_skips_bad_question(tmp_path):
    res = ex.export_all(QCM_CORE, "RSA — cours", out_dir=tmp_path, today=TODAY)
    assert not res.errors
    assert len(res.warnings) == 1 and "Question 2" in res.warnings[0]
    parsed = parse_gift(res.gift_path.read_text(encoding="utf-8"))
    assert len(parsed) == 2
    assert [a[0] for a in parsed[1][1]] == ["x = 1", "y # 2", "z : 3", "w"]
    assert [a[2] for a in parsed[1][1]] == ["~", "~", "=", "~"]
    assert [a[1] for a in parsed[0][1]][0] == "Oui, chiffrement asymétrique"
    assert len(ET.parse(res.xml_path).getroot().findall("question")) == 2


def test_core_format_feedback_in_xml():
    root = ET.fromstring(ex.build_moodle_xml(ex._normalize(QCM_CORE, [])))
    fbs = [a.findtext("feedback/text") for a in root.find("question").findall("answer")]
    assert fbs[0] == "Oui, chiffrement asymétrique" and fbs[1].startswith("Non")


def test_all_questions_bad_gives_error_for_each_format(tmp_path):
    bad = [{"question": "brut", "options": [], "correct": "", "type": "qcm"}]
    res = ex.export_all(bad, "x", out_dir=tmp_path, today=TODAY)
    assert set(res.errors) == {"gift", "xml"}
    assert not list(tmp_path.iterdir())


def test_formats_parameter(tmp_path):
    res = ex.export_all(QCM_ACCENTS, "x", out_dir=tmp_path, today=TODAY, formats=("gift",))
    assert res.gift_path and res.xml_path is None and not res.errors
    assert [p.suffix for p in tmp_path.iterdir()] == [".txt"]


def test_edited_bonne_reponse_wins_over_correct():
    q = [{"type": "qcm", "question": "Q", "options": ["A. a", "B. b"], "correct": "A", "bonne_reponse": "B"}]
    assert [a.correct for a in ex._normalize(q)[0].answers] == [False, True]


class _Upload:
    name = "/tmp/gradio/abc123/Cours d'Algo (L2).pdf"


@pytest.mark.parametrize("f,expected", [
    ("/tmp/gradio/x/cours_algo.pdf", "cours_algo"),
    (_Upload(), "Cours d'Algo (L2)"),
    ([_Upload()], "Cours d'Algo (L2)"),
    (None, "qcm"),
    ([], "qcm"),
])
def test_support_name_from_file(f, expected):
    assert ex.support_name_from_file(f) == expected