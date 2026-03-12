from dataclasses import dataclass, field
from .prototype import Prototype

@dataclass
class Question(Prototype):
    prompt: str
    hint: str = ""
    explanation: str = ""

@dataclass
class MultiAnswerQuestion(Question):
    options: list[str] = field(default_factory=list)
    correct_indexes: list[int] = field(default_factory=list)
    select_mode: str = "multi"   # "single" | "multi"

@dataclass
class OpenQuestion(Question):
    keywords: list[str] = field(default_factory=list)

@dataclass
class Test(Prototype):
    id: str
    test_type: str
    title: str
    course_id: str
    time_limit_sec: int | None = None
    questions: list[Question] = field(default_factory=list)

def grade_with_details(test: Test, answers: list):
    points = 0
    details = []
    max_points = len(test.questions)

    for i, q in enumerate(test.questions):
        user_ans = answers[i] if i < len(answers) else None

        if isinstance(q, MultiAnswerQuestion):
            ua = user_ans if isinstance(user_ans, list) else ([] if user_ans is None else [int(user_ans)])
            ua = sorted([int(x) for x in ua])
            ca = sorted([int(x) for x in q.correct_indexes])

            ok = ua == ca
            if ok:
                points += 1

            details.append({
                "index": i,
                "kind": "choice",
                "select_mode": q.select_mode,
                "prompt": q.prompt,
                "correct": ok,
                "your": ua,
                "correct_answer": ca,
                "explanation": q.explanation or ""
            })

        elif isinstance(q, OpenQuestion):
            text = (user_ans or "").strip()
            low = text.lower()
            ok = any(k.lower() in low for k in q.keywords)

            if ok:
                points += 1

            details.append({
                "index": i,
                "kind": "open",
                "prompt": q.prompt,
                "correct": ok,
                "your": text,
                "expected_keywords": q.keywords,
                "explanation": q.explanation or ""
            })
        else:
            details.append({
                "index": i,
                "kind": "unknown",
                "prompt": getattr(q, "prompt", "???"),
                "correct": False,
                "explanation": ""
            })

    return points, max_points, details