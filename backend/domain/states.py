from dataclasses import dataclass


@dataclass
class CourseState:
    key: str
    label: str
    message: str
    action_label: str

    def can_open(self) -> bool:
        return False

    def can_take_test(self) -> bool:
        return False

    def can_get_certificate(self) -> bool:
        return False

    def can_sync_lms(self) -> bool:
        return False

    def serialize(self) -> dict:
        return {
            "state": self.key,
            "state_label": self.label,
            "state_message": self.message,
            "action_label": self.action_label,
            "can_open": self.can_open(),
            "can_take_test": self.can_take_test(),
            "can_get_certificate": self.can_get_certificate(),
            "can_sync_lms": self.can_sync_lms(),
        }


class LockedCourseState(CourseState):
    def __init__(self):
        super().__init__(
            key="locked",
            label="Закрыт",
            message="Курс закрыт до оплаты. Сначала нужно разблокировать доступ.",
            action_label="Оплатить и открыть",
        )


class AvailableCourseState(CourseState):
    def __init__(self):
        super().__init__(
            key="available",
            label="Доступен",
            message="Курс открыт. Можно изучать материал и начинать тест.",
            action_label="Открыть курс",
        )

    def can_open(self) -> bool:
        return True

    def can_take_test(self) -> bool:
        return True

    def can_sync_lms(self) -> bool:
        return True


class InProgressCourseState(CourseState):
    def __init__(self):
        super().__init__(
            key="in_progress",
            label="В процессе",
            message="Курс уже начат. Можно продолжать тестирование и улучшать результат.",
            action_label="Продолжить курс",
        )

    def can_open(self) -> bool:
        return True

    def can_take_test(self) -> bool:
        return True

    def can_sync_lms(self) -> bool:
        return True


class CompletedCourseState(CourseState):
    def __init__(self):
        super().__init__(
            key="completed",
            label="Завершён",
            message="Курс завершён успешно. Можно просматривать материалы и получать сертификат.",
            action_label="Открыть результат",
        )

    def can_open(self) -> bool:
        return True

    def can_take_test(self) -> bool:
        return True

    def can_get_certificate(self) -> bool:
        return True

    def can_sync_lms(self) -> bool:
        return True


class CourseStateContext:
    @staticmethod
    def resolve(repo, user_id: str, course_id: str) -> CourseState:
        course = repo.get_course(course_id)
        if not course:
            return LockedCourseState()

        if not repo.has_course_access(user_id, course_id):
            return LockedCourseState()

        stat = repo.analytics(user_id, course_id)
        if stat["attempts"] == 0:
            return AvailableCourseState()

        best = stat.get("best")
        if best is not None and best >= 70:
            return CompletedCourseState()

        return InProgressCourseState()
