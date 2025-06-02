from fastapi import FastAPI
from routers.telegram import router as telegram_router
from routers.constructor import router as constructor_router

app = FastAPI(
    title="Telegram CORP AI Integration API",
)

app.include_router(telegram_router)
app.include_router(constructor_router)


    
