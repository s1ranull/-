from dataclasses import dataclass, field
from .prototype import Prototype

@dataclass
class Course(Prototype):
    id: str
    type: str
    title: str
    description: str

@dataclass
class VideoCourse(Course):
    video_url: str = ""
    notes: str = ""   # HTML-конспект на странице

@dataclass
class TextCourse(Course):
    text: str = ""    # HTML-текст

@dataclass
class InteractiveCourse(Course):
    steps: list[str] = field(default_factory=list)
    notes: str = ""   # HTML-конспект для интерактива