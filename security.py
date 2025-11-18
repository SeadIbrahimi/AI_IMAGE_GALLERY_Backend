from fastapi.security import HTTPBearer

# Shared HTTP bearer security dependency for all controllers
security = HTTPBearer()

