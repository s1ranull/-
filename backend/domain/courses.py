from dataclasses import dataclass, field
from .prototype import Prototype

@dataclass
class Course(Prototype):
    id: str
    type: str
    title: str
    description: str
    price: float = 0.0

@dataclass
class VideoCourse(Course):
    video_url: str = ""
    notes: str = ""   

@dataclass
class TextCourse(Course):
    text: str = ""    

@dataclass
class InteractiveCourse(Course):
    steps: list[str] = field(default_factory=list)
    notes: str = ""  