import asyncio
import uuid
from enum import Enum
from typing import Optional, Dict, Any, List

from typing_extensions import Annotated
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from browser_use import Agent, Browser, ChatOpenAI

load_dotenv()

# =====================================================
# Enums
# =====================================================

class SessionState(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


class Command(str, Enum):
    START = "start"
    EXECUTE = "execute"                 # blocking (recommended)
    EXECUTE_ASYNC = "execute_async"
    STATUS = "status"
    RESULT = "result"
    PAUSE = "pause"
    RESUME = "resume"
    INJECT = "inject"
    UPDATE = "update"
    STOP = "stop"
    CLOSE = "close"


# =====================================================
# ADK Input / Output Models (Pydantic v2 CORRECT)
# =====================================================

class BrowserToolInput(BaseModel):
    command: Command

    session_id: Annotated[
        Optional[str],
        Field(
            validation_alias="sessionId",
            serialization_alias="sessionId",
            description="Browser session identifier"
        )
    ] = None

    task: Optional[str] = None
    instruction: Optional[str] = None
    timeout_seconds: int = 120
    headless: bool = True


class BrowserToolOutput(BaseModel):
    status: str
    session_id: Optional[str] = None
    state: Optional[SessionState] = None
    result: Optional[str] = None
    message: Optional[str] = None


# =====================================================
# Session
# =====================================================

class BrowserSession:
    def __init__(self, browser: Browser):
        self.id: str = str(uuid.uuid4())
        self.browser = browser
        self.llm = ChatOpenAI(model="gpt-4o-mini")

        self.agent: Optional[Agent] = None
        self.task_handle: Optional[asyncio.Task] = None

        self.state: SessionState = SessionState.IDLE
        self.original_task: Optional[str] = None
        self.current_task: Optional[str] = None
        self.result: Optional[Any] = None
        self.logs: List[str] = []

    def log(self, msg: str):
        self.logs.append(msg)
        print(f"[Session {self.id}] {msg}")

    def is_running(self) -> bool:
        return self.task_handle is not None and not self.task_handle.done()


# =====================================================
# Session Manager (in-memory, ADK-safe)
# =====================================================

class SessionManager:
    def __init__(self):
        self._sessions: Dict[str, BrowserSession] = {}

    def create(self, headless: bool) -> BrowserSession:
        browser = Browser(headless=headless)
        session = BrowserSession(browser)
        self._sessions[session.id] = session
        session.log("Session created")
        return session

    def get(self, session_id: str) -> BrowserSession:
        if session_id not in self._sessions:
            raise ValueError(f"Session not found: {session_id}")
        return self._sessions[session_id]

    async def close(self, session_id: str):
        session = self.get(session_id)

        if session.is_running():
            session.task_handle.cancel()
            try:
                await session.task_handle
            except asyncio.CancelledError:
                pass

        await session.browser.stop()
        del self._sessions[session_id]


SESSIONS = SessionManager()

# =====================================================
# Execution Engine (single source of truth)
# =====================================================

async def _run_agent(session: BrowserSession, task: str):
    try:
        session.state = SessionState.RUNNING
        session.current_task = task

        session.agent = Agent(
            task=task,
            llm=session.llm,
            browser=session.browser,
        )

        session.log("Executing task")
        history = await session.agent.run()

        session.result = history
        session.state = SessionState.COMPLETED
        session.log("Task completed")

    except asyncio.CancelledError:
        session.state = SessionState.STOPPED
        session.log("Task cancelled")

    except Exception as e:
        session.state = SessionState.FAILED
        session.result = str(e)
        session.log(f"Task failed: {e}")


# =====================================================
# Google ADK Tool Entry
# =====================================================

async def browser_tool(**kwargs) -> Dict[str, Any]:
    """
    Google ADK-compatible browser automation tool.
    """

    data = BrowserToolInput(**kwargs)
    cmd = data.command

    # ---------------- START ----------------
    if cmd == Command.START:
        session = SESSIONS.create(headless=data.headless)
        return BrowserToolOutput(
            status="ready",
            session_id=session.id,
            message="Session started. Call execute with a task."
        ).model_dump(by_alias=True)

    if not data.session_id:
        return {"error": "sessionId is required"}

    session = SESSIONS.get(data.session_id)

    # ---------------- EXECUTE (BLOCKING) ----------------
    if cmd == Command.EXECUTE:
        if session.is_running():
            return {"error": "Task already running"}

        if not data.task:
            return {"error": "task is required"}

        session.original_task = data.task
        session.task_handle = asyncio.create_task(
            _run_agent(session, data.task)
        )

        try:
            await asyncio.wait_for(
                session.task_handle,
                timeout=data.timeout_seconds
            )
        except asyncio.TimeoutError:
            return BrowserToolOutput(
                status="timeout",
                session_id=session.id,
                message="Task still running. Call status/result."
            ).model_dump(by_alias=True)

        return BrowserToolOutput(
            status=session.state.value,
            session_id=session.id,
            state=session.state,
            result=str(session.result)
        ).model_dump(by_alias=True)

    # ---------------- STATUS ----------------
    if cmd == Command.STATUS:
        return BrowserToolOutput(
            status="ok",
            session_id=session.id,
            state=session.state,
            message=f"Running={session.is_running()}"
        ).model_dump(by_alias=True)

    # ---------------- RESULT ----------------
    if cmd == Command.RESULT:
        return BrowserToolOutput(
            status=session.state.value,
            session_id=session.id,
            state=session.state,
            result=str(session.result)
        ).model_dump(by_alias=True)

    # ---------------- PAUSE / RESUME ----------------
    if cmd == Command.PAUSE:
        if session.agent and session.state == SessionState.RUNNING:
            session.agent.pause()
            session.state = SessionState.PAUSED
            return {"status": "paused"}
        return {"error": "Cannot pause"}

    if cmd == Command.RESUME:
        if session.agent and session.state == SessionState.PAUSED:
            session.agent.resume()
            session.state = SessionState.RUNNING
            return {"status": "running"}
        return {"error": "Cannot resume"}

    # ---------------- INJECT ----------------
    if cmd == Command.INJECT:
        if not data.instruction:
            return {"error": "instruction required"}
        if session.agent:
            session.agent.add_new_task(data.instruction)
            return {"status": "injected"}
        return {"error": "No active agent"}

    # ---------------- UPDATE ----------------
    if cmd == Command.UPDATE:
        if not data.instruction:
            return {"error": "instruction required"}

        if session.is_running():
            session.task_handle.cancel()
            try:
                await session.task_handle
            except asyncio.CancelledError:
                pass

        merged = f"{session.original_task}\n\nADDITIONAL INSTRUCTIONS:\n{data.instruction}"
        session.task_handle = asyncio.create_task(
            _run_agent(session, merged)
        )

        return {
            "status": "restarted",
            "sessionId": session.id,
            "task": merged
        }

    # ---------------- STOP ----------------
    if cmd == Command.STOP:
        if session.is_running():
            session.task_handle.cancel()
            return {"status": "stopped"}
        return {"error": "Nothing running"}

    # ---------------- CLOSE ----------------
    if cmd == Command.CLOSE:
        await SESSIONS.close(data.session_id)
        return {"status": "closed"}

    return {"error": "Unknown command"}
