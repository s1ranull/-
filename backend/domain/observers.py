class Observer:
    def update(self, user_id: str, event_type: str, message: str):
        raise NotImplementedError


class NotificationObserver(Observer):
    def __init__(self, save_callback):
        self.save_callback = save_callback

    def update(self, user_id: str, event_type: str, message: str):
        self.save_callback(user_id, event_type, message)


class CourseEventSubject:
    def __init__(self):
        self._observers = []

    def subscribe(self, observer: Observer):
        self._observers.append(observer)

    def notify(self, user_id: str, event_type: str, message: str):
        for observer in self._observers:
            observer.update(user_id, event_type, message)
