from backend.domain.factories import MultiAnswerTestFactory, OpenQuestionTestFactory
from backend.domain.tests import Test

class TestBuilder:
    def __init__(self, test_type: str):
        self.test_type = test_type
        self.test_id: str | None = None
        self.title: str = "Test"
        self.course_id: str = ""
        self.time_limit_sec: int | None = None
        self.questions_data: list[dict] = []

        if test_type == "multi":
            self.factory = MultiAnswerTestFactory()
        elif test_type == "open":
            self.factory = OpenQuestionTestFactory()
        else:
            raise ValueError("Unknown test_type")

    def set_id(self, test_id: str):
        self.test_id = test_id
        return self

    def set_title(self, title: str):
        self.title = title
        return self

    def set_course_id(self, course_id: str):
        self.course_id = course_id
        return self

    def set_time_limit(self, seconds: int | None):
        self.time_limit_sec = seconds
        return self

    def add_question(self, q: dict):
        self.questions_data.append(q)
        return self

    def build(self) -> Test:
        if not self.test_id:
            raise ValueError("test_id required")
        if not self.course_id:
            raise ValueError("course_id required")

        test = self.factory.create_test(
            id=self.test_id,
            title=self.title,
            course_id=self.course_id,
            questions_data=self.questions_data
        )
        test.time_limit_sec = self.time_limit_sec
        return test