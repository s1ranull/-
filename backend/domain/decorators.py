class ProfileComponent:
    def render(self) -> dict:
        raise NotImplementedError


class BasicProfile(ProfileComponent):
    def __init__(self, username: str):
        self.username = username

    def render(self) -> dict:
        return {
            "username": self.username,
            "theme": "default",
            "avatar_frame": "none",
            "badges": [],
        }


class ProfileDecorator(ProfileComponent):
    def __init__(self, wrapped: ProfileComponent):
        self.wrapped = wrapped

    def render(self) -> dict:
        return self.wrapped.render()


class ThemeDecorator(ProfileDecorator):
    def __init__(self, wrapped: ProfileComponent, theme: str):
        super().__init__(wrapped)
        self.theme = theme

    def render(self) -> dict:
        data = self.wrapped.render()
        data["theme"] = self.theme
        return data


class AvatarFrameDecorator(ProfileDecorator):
    def __init__(self, wrapped: ProfileComponent, avatar_frame: str):
        super().__init__(wrapped)
        self.avatar_frame = avatar_frame

    def render(self) -> dict:
        data = self.wrapped.render()
        data["avatar_frame"] = self.avatar_frame
        return data


class BadgeDecorator(ProfileDecorator):
    def __init__(self, wrapped: ProfileComponent, badges):
        super().__init__(wrapped)
        self.badges = badges or []

    def render(self) -> dict:
        data = self.wrapped.render()
        data["badges"] = self.badges
        return data
