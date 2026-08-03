class AuthService:
    async def register(self, email: str, password: str, name: str) -> dict:
        return {"email": email, "name": name, "status": "registered"}

    async def login(self, email: str, password: str) -> dict:
        return {"email": email, "status": "logged-in"}
