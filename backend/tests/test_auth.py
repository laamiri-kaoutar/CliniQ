from fastapi.testclient import TestClient
from app.main import app
from app.core.security import get_password_hash, verify_password

client = TestClient(app)

def test_password_encryption():
    # Vérifie que le mot de passe n'est pas stocké en clair
    pwd = "secure_password_123"
    hashed = get_password_hash(pwd)
    assert hashed != pwd
    assert verify_password(pwd, hashed) is True

def test_access_blocked_without_token():
    # Vérifie que l'accès à l'historique est refusé sans authentification
    response = client.get("/chat/history")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"