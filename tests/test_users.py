from src.schemas.user import PublicKeyResponse

def test_public_key_response_schema():
    response = PublicKeyResponse(
        user_id="2026",
        email="jpezko@example.com",
        public_key="-----BEGIN PUBLIC KEY-----\nabc\n-----END PUBLIC KEY-----",
    )

    assert response.user_id == "2026"
    assert response.email == "jpezko@example.com"
    assert "BEGIN PUBLIC KEY" in response.public_key