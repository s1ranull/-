from passlib.context import CryptContext
import secrets
import time

def uid(prefix="u"):
    return f"{prefix}_{int(time.time()*1000)}_{secrets.token_hex(3)}"

class UserManager:
    _instance = None

    @staticmethod
    def get_instance():
        if UserManager._instance is None:
            UserManager._instance = UserManager()
        return UserManager._instance

    def __init__(self):
        self._pwd = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
        self._users_by_username = {} 
        self._sessions = {}           

        if "admin" not in self._users_by_username:
            self.register("admin", "admin123", role="admin")

    def register(self, username: str, password: str, role: str = "student"):
        username = username.strip().lower()
        if not username or not password:
            raise ValueError("username/password required")
        if username in self._users_by_username:
            raise ValueError("username already exists")

        user = {
            "id": uid("u"),
            "username": username,
            "role": role,
            "password_hash": self._pwd.hash(password),
        }
        self._users_by_username[username] = user
        return {"id": user["id"], "username": user["username"], "role": user["role"]}

    def login(self, username: str, password: str):
        username = username.strip().lower()
        user = self._users_by_username.get(username)
        if not user or not self._pwd.verify(password, user["password_hash"]):
            return None, None

        token = secrets.token_urlsafe(24)
        self._sessions[token] = username
        safe_user = {"id": user["id"], "username": user["username"], "role": user["role"]}
        return token, safe_user

    def get_user_by_token(self, token: str):
        if not token:
            return None
        username = self._sessions.get(token)
        if not username:
            return None
        u = self._users_by_username.get(username)
        if not u:
            return None
        return {"id": u["id"], "username": u["username"], "role": u["role"]}