from abc import ABC, abstractmethod
from .courses import VideoCourse, TextCourse, InteractiveCourse
from .tests import Test, MultiAnswerQuestion, OpenQuestion

# Factory Method 
class CourseCreator(ABC):
    def create(self, **data):
        return self.factory_method(**data)

    @abstractmethod
    def factory_method(self, **data):
        ...

class VideoCourseCreator(CourseCreator):
    def factory_method(self, **data):
        return VideoCourse(type="video", **data)

class TextCourseCreator(CourseCreator):
    def factory_method(self, **data):
        return TextCourse(type="text", **data)

class InteractiveCourseCreator(CourseCreator):
    def factory_method(self, **data):
        return InteractiveCourse(type="interactive", **data)

# Abstract Factory 
class TestFactory(ABC):
    @abstractmethod
    def create_test(self, *, id: str, title: str, course_id: str, questions_data: list[dict]) -> Test:
        ...

class MultiAnswerTestFactory(TestFactory):
    def create_test(self, *, id: str, title: str, course_id: str, questions_data: list[dict]) -> Test:
        qs = [MultiAnswerQuestion(**q) for q in questions_data]
        return Test(id=id, test_type="multi", title=title, course_id=course_id, questions=qs)

class OpenQuestionTestFactory(TestFactory):
    def create_test(self, *, id: str, title: str, course_id: str, questions_data: list[dict]) -> Test:
        qs = [OpenQuestion(**q) for q in questions_data]
        return Test(id=id, test_type="open", title=title, course_id=course_id, questions=qs)