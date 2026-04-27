from dataclasses import is_dataclass, asdict
from datetime import datetime
from typing import Optional, Any

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.storage.repo import Repo
from backend.domain.user_manager import UserManager
from backend.domain.tests import Test, MultiAnswerQuestion, OpenQuestion, grade_with_details
from backend.domain.adapters import (
    StripePaymentAdapter,
    PayPalPaymentAdapter,
    MoodleAdapter,
    GoogleClassroomAdapter,
)
from backend.domain.observers import CourseEventSubject, NotificationObserver
from backend.domain.strategies import DifficultyContext
from backend.domain.decorators import (
    BasicProfile,
    ThemeDecorator,
    AvatarFrameDecorator,
    BadgeDecorator,
)
from backend.domain.facade import LearningPlatformFacade
from backend.domain.states import CourseStateContext


def dump(obj):
    if is_dataclass(obj):
        return asdict(obj)
    if isinstance(obj, list):
        return [dump(x) for x in obj]
    if isinstance(obj, dict):
        return {k: dump(v) for k, v in obj.items()}
    return obj


app = FastAPI(title="Courses Platform API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

repo = Repo()
repo.seed()

users = UserManager.get_instance()

event_subject = CourseEventSubject()
event_subject.subscribe(NotificationObserver(repo.add_notification))
platform_facade = LearningPlatformFacade(repo, event_subject, select_test_for_user=None)


def select_test_for_user(user_id: str, course_id: str):
    """
    Strategy:
    Beginner     -> первые 3 вопроса
    Intermediate -> первые 4 вопроса
    Advanced     -> все вопросы
    """
    base_test = repo.get_test(course_id)
    if not base_test:
        return None, DifficultyContext.choose(None)

    stats = repo.analytics(user_id, course_id)
    strategy = DifficultyContext.choose(stats["avg"])

    if strategy.name == "Beginner":
        limit = min(3, len(base_test.questions))
    elif strategy.name == "Intermediate":
        limit = min(4, len(base_test.questions))
    else:
        limit = len(base_test.questions)

    selected_questions = [q.clone() for q in base_test.questions[:limit]]

    selected_test = Test(
        id=base_test.id,
        test_type=base_test.test_type,
        title=base_test.title,
        course_id=base_test.course_id,
        time_limit_sec=base_test.time_limit_sec,
        questions=selected_questions,
    )

    return selected_test, strategy


platform_facade.select_test_for_user = select_test_for_user


def _get_token_from_auth(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None
    if authorization.lower().startswith("bearer "):
        return authorization.split(" ", 1)[1].strip()
    return None


def get_current_user(authorization: Optional[str] = Header(None)):
    token = _get_token_from_auth(authorization)
    u = users.get_user_by_token(token)
    if not u:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return u


def require_admin(u=Depends(get_current_user)):
    if u["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return u


def ensure_course_access(user_id: str, course_id: str):
    course = repo.get_course(course_id)
    if not course:
        raise HTTPException(404, "Course not found")
    if not repo.has_course_access(user_id, course_id):
        raise HTTPException(403, "Course requires payment")
    return course


class RegisterIn(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=4, max_length=128)


class LoginIn(BaseModel):
    username: str
    password: str


class AttemptIn(BaseModel):
    course_id: str
    answers: list[Any]

class CourseUpsertIn(BaseModel):
    type: str
    title: str
    description: str
    price: float = 0
    video_url: str = ""
    notes: str = ""
    text: str = ""
    steps: list[str] = []

class TestUpsertIn(BaseModel):
    id: Optional[str] = None
    test_type: str
    title: str
    time_limit_sec: Optional[int] = None
    questions: list[dict] = []


class CloneTestIn(BaseModel):
    from_course_id: str
    to_course_id: str


class CloneQuestionIn(BaseModel):
    from_course_id: str
    question_index: int
    to_course_id: str


class PaymentIn(BaseModel):
    course_id: str
    provider: str
    amount: float | None = None


class LMSSyncIn(BaseModel):
    course_id: str
    provider: str


class ProfileCustomizeIn(BaseModel):
    theme: str = "default"
    avatar_frame: str = "none"
    badges: list[str] = []


@app.post("/api/register")
def register(payload: RegisterIn):
    try:
        user = users.register(payload.username, payload.password, role="student")
        return {"ok": True, "user": user}
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/login")
def login(payload: LoginIn):
    token, user = users.login(payload.username, payload.password)
    if not token:
        raise HTTPException(401, "Invalid credentials")
    return {"token": token, "user": user}


@app.get("/api/me")
def me(u=Depends(get_current_user)):
    return u



@app.get("/api/courses")
def list_courses(u=Depends(get_current_user)):
    items = []
    for c in repo.list_courses():
        row = dump(c)
        row.update(platform_facade.get_course_access_payload(u["id"], c.id))
        items.append(row)
    return items


@app.get("/api/courses/{course_id}")
def get_course(course_id: str, u=Depends(get_current_user)):
    c = repo.get_course(course_id)
    if not c:
        raise HTTPException(404, "Course not found")
    row = dump(c)
    row.update(platform_facade.get_course_access_payload(u["id"], course_id))
    return row


@app.get("/api/courses/{course_id}/access")
def get_course_access(course_id: str, u=Depends(get_current_user)):
    c = repo.get_course(course_id)
    if not c:
        raise HTTPException(404, "Course not found")
    return platform_facade.get_course_access_payload(u["id"], course_id)


@app.get("/api/courses/{course_id}/state")
def get_course_state(course_id: str, u=Depends(get_current_user)):
    c = repo.get_course(course_id)
    if not c:
        raise HTTPException(404, "Course not found")
    return platform_facade.get_course_state(u["id"], course_id)



@app.get("/api/courses/{course_id}/test")
def get_test_for_student(course_id: str, u=Depends(get_current_user)):
    ensure_course_access(u["id"], course_id)
    t, strategy = select_test_for_user(u["id"], course_id)
    if not t:
        return None

    qs_out = []
    for q in t.questions:
        if isinstance(q, MultiAnswerQuestion):
            qs_out.append({
                "kind": "choice",
                "prompt": q.prompt,
                "options": q.options,
                "select_mode": q.select_mode,
                "has_hint": bool(getattr(q, "hint", "")),
            })
        elif isinstance(q, OpenQuestion):
            qs_out.append({
                "kind": "open",
                "prompt": q.prompt,
                "has_hint": bool(getattr(q, "hint", "")),
            })
        else:
            qs_out.append({"kind": "unknown", "prompt": getattr(q, "prompt", "???"), "has_hint": False})

    return {
        "id": t.id,
        "test_type": t.test_type,
        "title": t.title,
        "course_id": t.course_id,
        "time_limit_sec": t.time_limit_sec,
        "strategy": strategy.name,
        "strategy_message": strategy.get_message(),
        "questions": qs_out,
    }


@app.get("/api/courses/{course_id}/test/hint/{q_index}")
def get_hint(course_id: str, q_index: int, u=Depends(get_current_user)):
    ensure_course_access(u["id"], course_id)
    t, _ = select_test_for_user(u["id"], course_id)
    if not t:
        raise HTTPException(404, "No test")
    if q_index < 0 or q_index >= len(t.questions):
        raise HTTPException(404, "Bad question index")

    q = t.questions[q_index]
    hint = getattr(q, "hint", "") or ""
    if not hint:
        raise HTTPException(404, "No hint")
    return {"hint": hint}


@app.post("/api/attempts")
def submit_attempt(payload: AttemptIn, u=Depends(get_current_user)):
    return platform_facade.submit_attempt(u, payload.course_id, payload.answers)


@app.get("/api/analytics")
def analytics(course_id: str, u=Depends(get_current_user)):
    return repo.analytics(u["id"], course_id)


@app.get("/api/courses/{course_id}/difficulty")
def get_difficulty(course_id: str, u=Depends(get_current_user)):
    ensure_course_access(u["id"], course_id)
    stat = repo.analytics(u["id"], course_id)
    strategy = DifficultyContext.choose(stat["avg"])
    question_count = 3 if strategy.name == "Beginner" else 4 if strategy.name == "Intermediate" else len(repo.get_test(course_id).questions) if repo.get_test(course_id) else 0
    return {
        "strategy": strategy.name,
        "message": strategy.get_message(),
        "avg_percent": stat["avg"],
        "question_count": question_count,
    }


@app.get("/api/profile")
def get_profile(u=Depends(get_current_user)):
    return repo.get_profile(u["id"], u["username"])


@app.post("/api/profile/customize")
def customize_profile(payload: ProfileCustomizeIn, u=Depends(get_current_user)):
    profile = BasicProfile(u["username"])
    profile = ThemeDecorator(profile, payload.theme)
    profile = AvatarFrameDecorator(profile, payload.avatar_frame)
    profile = BadgeDecorator(profile, payload.badges)
    rendered = profile.render()
    repo.save_profile(u["id"], rendered)

    event_subject.notify(
        u["id"],
        "profile",
        "Профиль был успешно кастомизирован"
    )

    return rendered


@app.get("/api/notifications")
def get_notifications(u=Depends(get_current_user)):
    return repo.get_notifications(u["id"])


@app.post("/api/payments")
def create_payment(payload: PaymentIn, u=Depends(get_current_user)):
    return platform_facade.pay_and_open_course(u, payload.course_id, payload.provider)


@app.post("/api/lms/sync")
def sync_lms(payload: LMSSyncIn, u=Depends(get_current_user)):
    return platform_facade.sync_course_to_lms(u, payload.course_id, payload.provider)


@app.post("/api/certificates")
def certificate(course_id: str, threshold: int = 70, u=Depends(get_current_user)):
    return platform_facade.issue_certificate(u, course_id, threshold)



@app.get("/api/admin/summary")
def admin_summary(a=Depends(require_admin)):
    return {
        "courses": len(repo.courses),
        "tests": len(repo.tests_by_course),
        "attempts": len(repo.attempts),
    }


@app.get("/api/admin/tests/{course_id}")
def admin_get_test(course_id: str, a=Depends(require_admin)):
    t = repo.get_test(course_id)
    return dump(t) if t else None


@app.put("/api/admin/tests/{course_id}")
def admin_upsert_test(course_id: str, payload: TestUpsertIn, a=Depends(require_admin)):
    t = repo.upsert_test(course_id, payload.model_dump())
    return dump(t)


@app.post("/api/admin/clone-test")
def admin_clone_test(payload: CloneTestIn, a=Depends(require_admin)):
    t = repo.clone_test(payload.from_course_id, payload.to_course_id)
    return dump(t)

@app.post("/api/admin/courses")
def admin_create_course(payload: CourseUpsertIn, a=Depends(require_admin)):
    c = repo.upsert_course(None, payload.model_dump())
    return dump(c)

@app.put("/api/admin/courses/{course_id}")
def admin_update_course(course_id: str, payload: CourseUpsertIn, a=Depends(require_admin)):
    c = repo.upsert_course(course_id, payload.model_dump())
    return dump(c)

@app.delete("/api/admin/courses/{course_id}")
def admin_delete_course(course_id: str, a=Depends(require_admin)):
    repo.delete_course(course_id)
    return {"ok": True}

@app.post("/api/admin/clone-question")
def admin_clone_question(payload: CloneQuestionIn, a=Depends(require_admin)):
    try:
        t = repo.clone_question(payload.from_course_id, payload.question_index, payload.to_course_id)
        return dump(t)
    except ValueError as e:
        raise HTTPException(400, str(e))
    
    