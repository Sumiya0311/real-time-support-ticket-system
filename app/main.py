import asyncio

from dotenv import load_dotenv
from fastapi import FastAPI

from app import models
from app.database import AsyncSessionLocal, Base, engine
from app.routers.auth import router as auth_router
from app.routers.categories import router as categories_router
from app.routers.tickets import router as tickets_router
from app.routers.agents import router as agents_router
from app.routers import messages
from app.routers import websocket
from app.routers import notifications
from app.routers import reports
from app.routers import feedback
from app.routers import sla_policy
from app.services.sla_service import check_sla_breaches

load_dotenv()

app = FastAPI(
    title="Real-Time Support Ticket System",
    description=(
        "Support tickets, agent assignment, live chat, "
        "feedback, ratings, and SLA tracking"
    ),
    version="1.0.0",
)



@app.on_event("startup")
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)



async def sla_monitor():
    while True:
        try:
            async with AsyncSessionLocal() as db:
                count = await check_sla_breaches(db)

                if count:
                    print(
                        f"SLA monitor: {count} ticket(s) breached."
                    )

        except asyncio.CancelledError:
            raise

        except Exception as exc:
            print(f"SLA monitor error: {exc}")

        await asyncio.sleep(60)


@app.on_event("startup")
async def start_sla_monitor():
    app.state.sla_monitor_task = asyncio.create_task(
        sla_monitor()
    )


@app.on_event("shutdown")
async def stop_sla_monitor():
    task = getattr(app.state, "sla_monitor_task", None)

    if task is not None:
        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            pass

 
@app.get("/")
async def root():
    return {
        "message": "Real-Time Support Ticket System API is running"
    }



@app.get("/health")
async def health_check():
    return {"status": "healthy"}



app.include_router(auth_router)
app.include_router(categories_router)
app.include_router(tickets_router)
app.include_router(agents_router)
app.include_router(messages.router)
app.include_router(websocket.router)
app.include_router(notifications.router)
app.include_router(reports.router)
app.include_router(feedback.router)
app.include_router(sla_policy.router)