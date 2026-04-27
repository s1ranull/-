from datetime import datetime
from fastapi import HTTPException

from backend.domain.adapters import (
    StripePaymentAdapter,
    PayPalPaymentAdapter,
    MoodleAdapter,
    GoogleClassroomAdapter,
)
from backend.domain.strategies import DifficultyContext
from backend.domain.states import CourseStateContext
from backend.domain.tests import grade_with_details


class LearningPlatformFacade:
    def __init__(self, repo, event_subject, select_test_for_user):
        self.repo = repo
        self.event_subject = event_subject
        self.select_test_for_user = select_test_for_user

    def get_course_state(self, user_id: str, course_id: str) -> dict:
        return CourseStateContext.resolve(self.repo, user_id, course_id).serialize()

    def get_course_access_payload(self, user_id: str, course_id: str) -> dict:
        data = dict(self.repo.get_course_access_info(user_id, course_id))
        data.update(self.get_course_state(user_id, course_id))
        return data

    def pay_and_open_course(self, user: dict, course_id: str, provider: str) -> dict:
        course = self.repo.get_course(course_id)
        if not course:
            raise HTTPException(404, "Course not found")

        if self.repo.has_course_access(user["id"], course_id):
            access = self.get_course_access_payload(user["id"], course_id)
            if access.get("payment"):
                access["payment"] = dict(access["payment"])
            return {
                "provider": "already-unlocked",
                "status": "success",
                "message": f"Курс '{course.title}' уже доступен",
                "user_id": user["id"],
                "course_id": course_id,
                "amount": float(getattr(course, "price", 0) or 0),
                "access": access,
            }

        provider_key = provider.lower()
        if provider_key == "stripe":
            adapter = StripePaymentAdapter()
        elif provider_key == "paypal":
            adapter = PayPalPaymentAdapter()
        else:
            raise HTTPException(400, "Unknown payment provider")

        amount = float(getattr(course, "price", 0) or 0)
        payment_result = adapter.pay(user["id"], course_id, amount)
        self.repo.save_payment(dict(payment_result))
        self.repo.grant_course_access(user["id"], course_id)

        self.event_subject.notify(
            user["id"],
            "payment",
            f"Оплата курса '{course.title}' выполнена через {payment_result['provider']}"
        )

        access = self.get_course_access_payload(user["id"], course_id)
        if access.get("payment"):
            access["payment"] = dict(access["payment"])
        response = dict(payment_result)
        response["access"] = access
        return response

    def submit_attempt(self, user: dict, course_id: str, answers: list) -> dict:
        course = self.repo.get_course(course_id)
        if not course:
            raise HTTPException(404, "Course not found")
        if not self.repo.has_course_access(user["id"], course_id):
            raise HTTPException(403, "Course requires payment")

        test, current_strategy = self.select_test_for_user(user["id"], course_id)
        if not test:
            raise HTTPException(400, "No test for this course")

        points, max_points, details = grade_with_details(test, answers)
        self.repo.record_attempt(user["id"], course_id, points, max_points)

        percent = round((points / max_points) * 100) if max_points else 0
        stats = self.repo.analytics(user["id"], course_id)
        next_strategy = DifficultyContext.choose(stats["avg"])

        if percent >= 70:
            self.event_subject.notify(
                user["id"],
                "test_passed",
                f"Тест по курсу '{course.title}' пройден на {percent}%"
            )
        else:
            self.event_subject.notify(
                user["id"],
                "test_failed",
                f"Тест по курсу '{course.title}' не пройден. Результат: {percent}%"
            )

        return {
            "points": points,
            "max_points": max_points,
            "percent": percent,
            "details": details,
            "analytics": stats,
            "difficulty_strategy_before": current_strategy.name,
            "difficulty_strategy_after": next_strategy.name,
            "course_state_after": self.get_course_state(user["id"], course_id),
        }

    def sync_course_to_lms(self, user: dict, course_id: str, provider: str) -> dict:
        course = self.repo.get_course(course_id)
        if not course:
            raise HTTPException(404, "Course not found")
        if not self.repo.has_course_access(user["id"], course_id):
            raise HTTPException(403, "Course requires payment")

        provider_key = provider.lower()
        if provider_key == "moodle":
            adapter = MoodleAdapter()
        elif provider_key in ("googleclassroom", "google classroom"):
            adapter = GoogleClassroomAdapter()
        else:
            raise HTTPException(400, "Unknown LMS provider")

        result = adapter.sync_course(user, course)
        self.repo.save_lms_sync(dict(result))
        self.event_subject.notify(
            user["id"],
            "lms_sync",
            f"Курс '{course.title}' синхронизирован в {result['provider']}"
        )
        response = dict(result)
        response["course_state"] = self.get_course_state(user["id"], course_id)
        return response

    def issue_certificate(self, user: dict, course_id: str, threshold: int = 70) -> dict:
        course = self.repo.get_course(course_id)
        if not course:
            raise HTTPException(404, "Course not found")
        if not self.repo.has_course_access(user["id"], course_id):
            raise HTTPException(403, "Course requires payment")

        stat = self.repo.analytics(user["id"], course_id)
        if stat["attempts"] == 0:
            raise HTTPException(400, "No attempts")

        best = stat["best"] or 0
        if best < threshold:
            raise HTTPException(400, f"Need >= {threshold}%, best is {best}%")

        self.event_subject.notify(
            user["id"],
            "certificate",
            f"Сертификат по курсу '{course.title}' успешно получен"
        )

        return {
            "id": f"cert_{user['id']}_{course_id}",
            "student": user["username"],
            "course": course.title,
            "percent": best,
            "issued_at": datetime.now().isoformat(timespec="seconds"),
            "course_state": self.get_course_state(user["id"], course_id),
        }
