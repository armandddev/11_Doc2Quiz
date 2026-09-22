import pytest
from unittest.mock import patch, MagicMock
import bcrypt

from Doc2Quiz.context import Role, UserContext
from Doc2Quiz.auth import sign_in, sign_up

@pytest.fixture
def hashed_password():
    return bcrypt.hashpw(b"motdepasse123", bcrypt.gensalt()).decode()


@pytest.fixture
def db_user(hashed_password):
    return {
        "id": 1,
        "email": "prof@iut.fr",
        "password_hash": hashed_password,
        "role": "teacher",
    }

def test_sign_in_succes(db_user):
    with patch("Doc2Quiz.auth.get_cursor") as mock_cursor:
        cur = MagicMock()
        cur.fetchone.return_value = db_user
        mock_cursor.return_value.__enter__ = lambda s: cur
        mock_cursor.return_value.__exit__ = MagicMock(return_value=False)

        user = sign_in("prof@iut.fr", "motdepasse123")

        assert isinstance(user, UserContext)
        assert user.email == "prof@iut.fr"
        assert user.role == Role.TEACHER


def test_sign_in_email_inconnu():
    with patch("Doc2Quiz.auth.get_cursor") as mock_cursor:
        cur = MagicMock()
        cur.fetchone.return_value = None
        mock_cursor.return_value.__enter__ = lambda s: cur
        mock_cursor.return_value.__exit__ = MagicMock(return_value=False)

        with pytest.raises(ValueError, match="Email ou mot de passe incorrect."):
            sign_in("inconnu@iut.fr", "motdepasse123")


def test_sign_in_mauvais_mot_de_passe(db_user):
    with patch("Doc2Quiz.auth.get_cursor") as mock_cursor:
        cur = MagicMock()
        cur.fetchone.return_value = db_user
        mock_cursor.return_value.__enter__ = lambda s: cur
        mock_cursor.return_value.__exit__ = MagicMock(return_value=False)

        with pytest.raises(ValueError, match="Email ou mot de passe incorrect."):
            sign_in("prof@iut.fr", "mauvaismdp")


def test_sign_up_succes():
    new_user = {"id": 2, "email": "nouveau@iut.fr", "role": "teacher"}

    with patch("Doc2Quiz.auth.get_cursor") as mock_cursor:
        cur = MagicMock()
        cur.fetchone.return_value = new_user
        mock_cursor.return_value.__enter__ = lambda s: cur
        mock_cursor.return_value.__exit__ = MagicMock(return_value=False)

        user = sign_up("nouveau@iut.fr", "motdepasse123")

        assert isinstance(user, UserContext)
        assert user.email == "nouveau@iut.fr"
        assert user.role == Role.TEACHER


def test_sign_up_email_vide():
    with pytest.raises(ValueError, match="Email et mot de passe obligatoires."):
        sign_up("", "motdepasse123")


def test_sign_up_password_vide():
    with pytest.raises(ValueError, match="Email et mot de passe obligatoires."):
        sign_up("prof@iut.fr", "")


def test_sign_up_password_trop_court():
    with pytest.raises(ValueError, match="au moins 8 caractères"):
        sign_up("prof@iut.fr", "court")


def test_sign_up_email_deja_utilise():
    with patch("Doc2Quiz.auth.get_cursor") as mock_cursor:
        cur = MagicMock()
        cur.execute.side_effect = Exception("duplicate key")
        mock_cursor.return_value.__enter__ = lambda s: cur
        mock_cursor.return_value.__exit__ = MagicMock(return_value=False)

        with pytest.raises(ValueError, match="déjà utilisé"):
            sign_up("prof@iut.fr", "motdepasse123")