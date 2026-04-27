import time
import secrets
from backend.domain.factories import (
    VideoCourseCreator, TextCourseCreator, InteractiveCourseCreator
)
from backend.domain.tests import Test
from backend.domain.test_builder import TestBuilder


def uid(prefix="x"):
    return f"{prefix}_{int(time.time()*1000)}_{secrets.token_hex(3)}"


class Repo:
    def __init__(self):
        self.courses = []
        self.tests_by_course: dict[str, Test] = {}
        self.attempts = []
        self.notifications: dict[str, list[dict]] = {}
        self.profiles: dict[str, dict] = {}
        self.payments: list[dict] = []
        self.lms_syncs: list[dict] = []
        self.enrollments: dict[str, set[str]] = {}

        self._course_creators = {
            "video": VideoCourseCreator(),
            "text": TextCourseCreator(),
            "interactive": InteractiveCourseCreator(),
        }

    # Builder
    def _build_test(self, *, test_id: str, test_type: str, title: str, course_id: str,
                    time_limit_sec: int | None, questions: list[dict]) -> Test:
        b = (
            TestBuilder(test_type)
            .set_id(test_id)
            .set_title(title)
            .set_course_id(course_id)
            .set_time_limit(time_limit_sec)
        )
        for q in questions:
            b.add_question(q)
        return b.build()

    def seed(self):
        c_html = self._course_creators["video"].create(
            id=uid("c"),
            title="HTML Essentials",
            description="Структура страницы, базовые теги и как читать разметку.",
            price=49.0,
            video_url="https://www.youtube-nocookie.com/embed/UB1O30fR-EE",
            notes="<h3>Конспект</h3><p>Скелет HTML: doctype → html → head/body.</p>"
        )

        c_js = self._course_creators["text"].create(
            id=uid("c"),
            title="JavaScript Foundations",
            description="let/const, типы, строгое сравнение, объекты.",
            price=69.0,
            text="<h3>Конспект</h3><p>let/const, ===, object key:value.</p>"
        )

        
        c_patterns = self._course_creators["interactive"].create(
            id=uid("c"),
            title="Design Patterns Overview",
            description="Что за паттерны и где они в проекте.",
            price=99.0,
            notes=(
                "<h3>Что тут должно быть</h3>"
                "<p>Этот курс объясняет, где в проекте используются паттерны:</p>"
                "<ul>"
                "<li>Factory Method — создание курсов</li>"
                "<li>Abstract Factory — создание тестов</li>"
                "<li>Singleton — менеджер пользователей</li>"
                "<li>Builder — сборка теста по шагам</li>"
                "<li>Prototype — клонирование тестов/вопросов</li>"
                "</ul>"
            ),
            steps=[
                "Factory Method — создание курсов",
                "Abstract Factory — создание тестов",
                "Singleton — один UserManager",
                "Builder — конструктор теста",
                "Prototype — клонирование"
            ]
        )

        self.courses = [c_html, c_js, c_patterns]

       
        self.tests_by_course[c_html.id] = self._build_test(
            test_id=uid("t"),
            test_type="multi",
            title="Тест: HTML — базовые теги",
            course_id=c_html.id,
            time_limit_sec=10 * 60,
            questions=[
                {"prompt":"Где находится контент, который видит пользователь?","options":["<head>","<body>","<html>"],"correct_indexes":[1],"select_mode":"single","hint":"body — видимая часть","explanation":"Контент внутри <body>."},
                {"prompt":"Какой тег создаёт ссылку?","options":["<a>","<p>","<link>"],"correct_indexes":[0],"select_mode":"single","hint":"у ссылки href","explanation":"Ссылка — тег <a>."},
                {"prompt":"Где должен находиться <li>?","options":["Внутри <ul>/<ol>","Внутри <p>","Внутри <a>"],"correct_indexes":[0],"select_mode":"single","hint":"li — элемент списка","explanation":"<li> внутри <ul>/<ol>."},
                {"prompt":"Какие теги обычно блочные?","options":["<div>","<span>","<p>","<h1>"],"correct_indexes":[0,2,3],"select_mode":"multi","hint":"span обычно inline","explanation":"div/p/h1 — блоки."},
                {"prompt":"Какой атрибут у <a> задаёт адрес?","options":["src","href","alt"],"correct_indexes":[1],"select_mode":"single","hint":"href","explanation":"Адрес ссылки — href."},
            ]
        )

        self.tests_by_course[c_js.id] = self._build_test(
            test_id=uid("t"),
            test_type="multi",
            title="Тест: JS — основы",
            course_id=c_js.id,
            time_limit_sec=12 * 60,
            questions=[
                {"prompt":"Строгое сравнение в JS?","options":["==","===","="],"correct_indexes":[1],"select_mode":"single","hint":"без приведения типов","explanation":"=== сравнивает тип и значение."},
                {"prompt":"Примитивы?","options":["number","string","object","boolean"],"correct_indexes":[0,1,3],"select_mode":"multi","hint":"object — не примитив","explanation":"number/string/boolean — примитивы."},
                {"prompt":"const без значения?","options":["Да","Нет"],"correct_indexes":[1],"select_mode":"single","hint":"нужна инициализация","explanation":"const x; — ошибка."},
                {"prompt":"let позволяет…","options":["переназначать","нельзя менять","только читать"],"correct_indexes":[0],"select_mode":"single","hint":"обычная переменная","explanation":"let можно менять."},
                {"prompt":"object — это…","options":["ключ/значение","только числа","только текст"],"correct_indexes":[0],"select_mode":"single","hint":"key:value","explanation":"object хранит пары key:value."},
            ]
        )

   
    def list_courses(self):
        return self.courses

    def get_course(self, course_id: str):
        return next((c for c in self.courses if c.id == course_id), None)

    def upsert_course(self, course_id: str | None, payload: dict):
        ctype = payload.get("type")
        creator = self._course_creators.get(ctype)
        if not creator:
            raise ValueError("Unknown course type")

        cid = course_id or uid("c")

        base = {
            "id": cid,
            "title": payload.get("title", ""),
            "description": payload.get("description", ""),
            "price": float(payload.get("price", 0) or 0),
        }

        if ctype == "video":
            base["video_url"] = payload.get("video_url", "")
            base["notes"] = payload.get("notes", "")
        elif ctype == "text":
            base["text"] = payload.get("text", "")
        elif ctype == "interactive":
            base["steps"] = payload.get("steps", [])
            base["notes"] = payload.get("notes", "")

        course = creator.create(**base)

        existed = self.get_course(cid)
        if existed:
            self.courses = [course if x.id == cid else x for x in self.courses]
        else:
            self.courses.append(course)

        return course

    def delete_course(self, course_id: str):
        self.courses = [c for c in self.courses if c.id != course_id]
        self.tests_by_course.pop(course_id, None)

    
    def get_test(self, course_id: str) -> Test | None:
        return self.tests_by_course.get(course_id)

    def upsert_test(self, course_id: str, payload: dict):
        test_id = payload.get("id") or uid("t")
        test_type = payload.get("test_type")
        title = payload.get("title", "Test")
        time_limit_sec = payload.get("time_limit_sec", None)
        questions = payload.get("questions", [])

        test = self._build_test(
            test_id=test_id,
            test_type=test_type,
            title=title,
            course_id=course_id,
            time_limit_sec=time_limit_sec,
            questions=questions
        )

        self.tests_by_course[course_id] = test
        return test


    
    def record_attempt(self, user_id: str, course_id: str, points: int, max_points: int):
        self.attempts.append({
            "user_id": user_id,
            "course_id": course_id,
            "points": points,
            "max_points": max_points,
            "ts": time.time(),
        })

    def analytics(self, user_id: str, course_id: str):
        xs = [a for a in self.attempts if a["user_id"] == user_id and a["course_id"] == course_id]
        if not xs:
            return {"attempts": 0, "best": None, "avg": None, "last": None}

        def perc(a):
            return round((a["points"] / a["max_points"]) * 100) if a["max_points"] else 0

        best = max(xs, key=perc)
        last = xs[-1]
        avg = round(sum(perc(a) for a in xs) / len(xs))
        return {"attempts": len(xs), "best": perc(best), "avg": avg, "last": perc(last)}
    
  
    def clone_test(self, from_course_id: str, to_course_id: str):
        t = self.tests_by_course.get(from_course_id)
        if not t:
            raise ValueError("No test to clone")

        cloned = t.clone(
            id=uid("t"),
            course_id=to_course_id,
            title=t.title + " (copy)"
        )
        self.tests_by_course[to_course_id] = cloned
        return cloned

    def clone_question(self, from_course_id: str, question_index: int, to_course_id: str):
        src = self.tests_by_course.get(from_course_id)
        if not src:
            raise ValueError("Source course has no test")
        if question_index < 0 or question_index >= len(src.questions):
            raise ValueError("Bad question index")

        
        q = src.questions[question_index].clone()

        dst = self.tests_by_course.get(to_course_id)
        if dst is None:
            
            dst = self._build_test(
                test_id=uid("t"),
                test_type=src.test_type,
                title="Новый тест (создан при клонировании вопроса)",
                course_id=to_course_id,
                time_limit_sec=src.time_limit_sec,
                questions=[]
            )

        if dst.test_type != src.test_type:
            raise ValueError("Target test type differs from source test type")

        dst.questions.append(q)
        self.tests_by_course[to_course_id] = dst
        return dst

    def add_notification(self, user_id: str, event_type: str, message: str):
        if user_id not in self.notifications:
            self.notifications[user_id] = []
        self.notifications[user_id].insert(0, {
            "event_type": event_type,
            "message": message,
            "ts": time.time(),
        })

    def get_notifications(self, user_id: str):
        return self.notifications.get(user_id, [])

    def save_profile(self, user_id: str, profile_data: dict):
        self.profiles[user_id] = profile_data
        return profile_data

    def get_profile(self, user_id: str, username: str):
        if user_id not in self.profiles:
            self.profiles[user_id] = {
                "username": username,
                "theme": "default",
                "avatar_frame": "none",
                "badges": [],
            }
        return self.profiles[user_id]

    def save_payment(self, payment_data: dict):
        self.payments.append(payment_data)
        return payment_data

    def save_lms_sync(self, sync_data: dict):
        self.lms_syncs.append(sync_data)
        return sync_data


    def grant_course_access(self, user_id: str, course_id: str):
        if user_id not in self.enrollments:
            self.enrollments[user_id] = set()
        self.enrollments[user_id].add(course_id)

    def has_course_access(self, user_id: str, course_id: str) -> bool:
        course = self.get_course(course_id)
        if not course:
            return False
        price = float(getattr(course, "price", 0) or 0)
        if price <= 0:
            return True
        return course_id in self.enrollments.get(user_id, set())

    def get_payment_for_course(self, user_id: str, course_id: str):
        for payment in reversed(self.payments):
            if payment.get("user_id") == user_id and payment.get("course_id") == course_id:
                return payment
        return None

    def get_course_access_info(self, user_id: str, course_id: str):
        course = self.get_course(course_id)
        if not course:
            return {"has_access": False, "price": 0, "is_free": False, "payment": None}
        price = float(getattr(course, "price", 0) or 0)
        payment = self.get_payment_for_course(user_id, course_id)
        return {
            "has_access": self.has_course_access(user_id, course_id),
            "price": price,
            "is_free": price <= 0,
            "payment": payment,
        }
