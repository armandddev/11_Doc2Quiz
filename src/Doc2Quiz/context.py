from dataclasses import dataclass, field
from enum import Enum


class Role(str, Enum):
    TEACHER = "teacher"
    STUDENT = "student"


@dataclass
class UserContext:
    user_id: int
    email: str
    name: str
    role: Role = Role.TEACHER


@dataclass
class AppContext:
    user: UserContext | None = None
    document_id: int | None = None
    sections: list = field(default_factory=list)

    @property
    def is_authenticated(self) -> bool:
        return self.user is not None

    @property
    def is_teacher(self) -> bool:
        return self.is_authenticated and self.user.role == Role.TEACHER

    @property
    def has_document(self) -> bool:
        return self.document_id is not None

    def reset_document(self):
        self.document_id = None
        self.sections = []

    def logout(self):
        self.user = None
        self.reset_document()