from pydantic import BaseModel, Field

USERNAME_PATTERN = r"^[A-Za-z0-9_.-]+$"
EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50, pattern=USERNAME_PATTERN,
                          examples=["ivan_petrov"])
    email: str = Field(max_length=255, pattern=EMAIL_PATTERN, examples=["ivan@example.com"])
    password: str = Field(min_length=6, max_length=128, examples=["Secret123"])


class LoginRequest(BaseModel):
    login: str = Field(min_length=1, max_length=255, description="Логин или email")
    password: str = Field(min_length=1, max_length=128)


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Время жизни access-токена в секундах")


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=10)
