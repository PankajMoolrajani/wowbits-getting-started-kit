"""
Browser automation tool – single-file production design.

- Explicit Command enum + dispatch (no stringly-typed actions).
- Single execution pipeline; reuse LLM + browser per session.
- SessionManager: lifecycle, TTL, concurrency guard, locking.
- State machine: status derived from task handle.
- execute() = run_task_and_wait as the ADK happy path (blocking by default).
"""

import asyncio
import time
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, Optional

from dotenv import load_dotenv
from browser_use import Agent, Browser, ChatOpenAI

load_dotenv()


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class SessionStatus(str, Enum):
    """Session/task state; derived from task handle where possible."""

    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"
    TIMEOUT = "timeout"


class Command(str, Enum):
    """Explicit commands instead of stringly-typed actions."""

    START_SESSION = "start_session"
    RUN_TASK = "run_task"
    RUN_TASK_AND_WAIT = "run_task_and_wait"
    GET_STATUS = "get_status"
    GET_RESULT = "get_result"
    PAUSE = "pause"
    RESUME = "resume"
    ADD_INSTRUCTION = "add_instruction"
    UPDATE_TASK = "update_task"
    STOP = "stop"
    STOP_SESSION = "stop_session"

    @classmethod
    def from_action(cls, action: str) -> "Command":
        try:
            return cls(action)
        except ValueError:
            raise ValueError(f"Unknown action: {action}")


@dataclass
class ToolResponse:
    """Structured response; serialized to dict for ADK."""

    status: str
    message: Optional[str] = None
    session_id: Optional[str] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    current_task: Optional[str] = None
    merged_task: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {"status": self.status}
        if self.message is not None:
            out["message"] = self.message
        if self.session_id is not None:
            out["session_id"] = self.session_id
        if self.result is not None:
            out["result"] = self.result
        if self.error is not None:
            out["error"] = self.error
        if self.current_task is not None:
            out["current_task"] = self.current_task
        if self.merged_task is not None:
            out["merged_task"] = self.merged_task
        return out


# ---------------------------------------------------------------------------
# Session (state machine; status from task handle)
# ---------------------------------------------------------------------------


class Session:
    """Holds browser, LLM, agent, task handle. Status derived from task state."""

    def __init__(self, session_id: str, browser: Browser):
        self.session_id = session_id
        self.browser = browser
        self._llm: Optional[ChatOpenAI] = None
        self.agent: Optional[Agent] = None
        self._task_handle: Optional[asyncio.Task] = None
        self._explicit_status: Optional[SessionStatus] = None
        self.result: Any = None
        self.logs: list[str] = []
        self.original_task: Optional[str] = None
        self.current_task: Optional[str] = None
        self._created_at: float = time.monotonic()

    @property
    def llm(self) -> ChatOpenAI:
        """Reuse one LLM per session."""
        if self._llm is None:
            self._llm = ChatOpenAI(model="gpt-4o-mini")
        return self._llm

    @property
    def task_handle(self) -> Optional[asyncio.Task]:
        return self._task_handle

    @task_handle.setter
    def task_handle(self, value: Optional[asyncio.Task]) -> None:
        self._task_handle = value

    def status(self) -> SessionStatus:
        if self._explicit_status is not None:
            return self._explicit_status
        if self._task_handle is None:
            return SessionStatus.IDLE
        if not self._task_handle.done():
            return SessionStatus.RUNNING
        try:
            self._task_handle.result()
            return SessionStatus.COMPLETED
        except asyncio.CancelledError:
            return SessionStatus.STOPPED
        except Exception:
            return SessionStatus.FAILED

    def set_paused(self) -> None:
        self._explicit_status = SessionStatus.PAUSED

    def set_running(self) -> None:
        self._explicit_status = None

    def set_stopped(self) -> None:
        self._explicit_status = SessionStatus.STOPPED

    def set_failed(self, error: Any) -> None:
        self._explicit_status = SessionStatus.FAILED
        self.result = error

    def set_completed(self, result: Any) -> None:
        self._explicit_status = SessionStatus.COMPLETED
        self.result = result

    def sync_from_handle(self) -> None:
        if self._task_handle is None or not self._task_handle.done():
            return
        if self._explicit_status is not None:
            return
        try:
            self.result = self._task_handle.result()
            self._explicit_status = SessionStatus.COMPLETED
        except asyncio.CancelledError:
            self._explicit_status = SessionStatus.STOPPED
        except Exception as e:
            self.result = str(e)
            self._explicit_status = SessionStatus.FAILED

    def log(self, message: str) -> None:
        self.logs.append(message)
        print(f"[Session {self.session_id}] {message}")

    def age_seconds(self) -> float:
        return time.monotonic() - self._created_at


# ---------------------------------------------------------------------------
# Single execution pipeline (reuse LLM + browser per session)
# ---------------------------------------------------------------------------


async def _run_agent(session: Session, task: str) -> None:
    """Single agent runner; used by run_task, run_task_and_wait, update_task."""
    try:
        session.agent = Agent(
            task=task,
            llm=session.llm,
            browser=session.browser,
        )
        session.log(f"Running task: {task}")
        history = await session.agent.run()
        session.set_completed(history)
        session.log("Task completed successfully")
    except asyncio.CancelledError:
        session.set_stopped()
        session.log("Task was stopped")
    except Exception as e:
        session.set_failed(str(e))
        session.log(f"Task failed: {e}")


# ---------------------------------------------------------------------------
# SessionManager (singleton, TTL, concurrency guard, locking)
# ---------------------------------------------------------------------------

DEFAULT_TTL_SECONDS = 3600  # 1 hour
DEFAULT_MAX_SESSIONS = 10


class SessionManager:
    _instance: Optional["SessionManager"] = None
    _lock: asyncio.Lock = asyncio.Lock()

    def __init__(
        self,
        ttl_seconds: float = DEFAULT_TTL_SECONDS,
        max_sessions: int = DEFAULT_MAX_SESSIONS,
        headless: bool = False,
    ):
        self._sessions: Dict[str, Session] = {}
        self._manager_lock = asyncio.Lock()
        self._ttl_seconds = ttl_seconds
        self._max_sessions = max_sessions
        self._headless = headless

    @classmethod
    def get_instance(
        cls,
        ttl_seconds: float = DEFAULT_TTL_SECONDS,
        max_sessions: int = DEFAULT_MAX_SESSIONS,
        headless: bool = False,
    ) -> "SessionManager":
        if cls._instance is None:
            cls._instance = cls(ttl_seconds=ttl_seconds, max_sessions=max_sessions, headless=headless)
        return cls._instance

    async def _cleanup_expired(self) -> None:
        """Remove sessions past TTL (and optionally stop their browser)."""
        now = time.monotonic()
        to_remove = [
            sid for sid, s in self._sessions.items()
            if s.age_seconds() > self._ttl_seconds
        ]
        for sid in to_remove:
            await self._remove_session(sid)

    async def _remove_session(self, session_id: str) -> None:
        session = self._sessions.get(session_id)
        if not session:
            return
        if session.task_handle and not session.task_handle.done():
            session.task_handle.cancel()
            try:
                await session.task_handle
            except asyncio.CancelledError:
                pass
        if session.browser:
            await session.browser.stop()
        del self._sessions[session_id]

    async def create_session(self) -> tuple[str, Session]:
        async with self._manager_lock:
            await self._cleanup_expired()
            if len(self._sessions) >= self._max_sessions:
                raise RuntimeError(
                    f"Max sessions ({self._max_sessions}) reached. Close a session first."
                )
            sid = str(uuid.uuid4())
            browser = Browser(headless=self._headless)
            session = Session(session_id=sid, browser=browser)
            self._sessions[sid] = session
            session.log(f"Session started: {sid}")
            return sid, session

    async def get_session(self, session_id: str) -> Optional[Session]:
        async with self._manager_lock:
            await self._cleanup_expired()
            return self._sessions.get(session_id)

    async def stop_session(self, session_id: str) -> bool:
        async with self._manager_lock:
            if session_id not in self._sessions:
                return False
            await self._remove_session(session_id)
            return True


# ---------------------------------------------------------------------------
# Command handlers (dispatch table)
# ---------------------------------------------------------------------------

async def _cmd_start_session(manager: SessionManager, **kwargs: Any) -> ToolResponse:
    sid, session = await manager.create_session()
    return ToolResponse(
        status="success",
        session_id=sid,
        message="Browser session started. Use run_task_and_wait for one-call execution.",
    )


async def _cmd_run_task(
    manager: SessionManager,
    session_id: str,
    session: Session,
    task: Optional[str],
    **kwargs: Any,
) -> ToolResponse:
    if not task:
        return ToolResponse(status="error", error="task is required for run_task")
    if session.status() == SessionStatus.RUNNING:
        return ToolResponse(
            status="error",
            error="A task is already running. Check status or stop it first.",
        )
    session.original_task = task
    session.current_task = task
    session.task_handle = asyncio.create_task(_run_agent(session, task))
    session.set_running()
    return ToolResponse(
        status=SessionStatus.RUNNING.value,
        message="Task started in background. Poll get_status or use run_task_and_wait for blocking.",
    )


async def _cmd_run_task_and_wait(
    manager: SessionManager,
    session_id: str,
    session: Session,
    task: Optional[str],
    timeout_seconds: Optional[int] = 120,
    **kwargs: Any,
) -> ToolResponse:
    if not task:
        return ToolResponse(status="error", error="task is required for run_task_and_wait")
    if session.status() == SessionStatus.RUNNING:
        return ToolResponse(
            status="error",
            error="A task is already running. Stop it first or use get_status/get_result.",
        )
    timeout = timeout_seconds if timeout_seconds is not None else 120
    session.original_task = task
    session.current_task = task
    session.task_handle = asyncio.create_task(_run_agent(session, task))
    session.set_running()
    try:
        await asyncio.wait_for(session.task_handle, timeout=float(timeout))
    except asyncio.TimeoutError:
        session.log(f"Task still running after {timeout}s (timeout). Use get_status/get_result later.")
        return ToolResponse(
            status=SessionStatus.TIMEOUT.value,
            session_id=session_id,
            message=f"Task did not finish within {timeout}s. Call get_status or get_result later.",
        )
    st = session.status()
    if st == SessionStatus.COMPLETED:
        return ToolResponse(
            status=SessionStatus.COMPLETED.value,
            result=str(session.result),
            message="Task completed.",
        )
    if st == SessionStatus.FAILED:
        return ToolResponse(
            status=SessionStatus.FAILED.value,
            error=str(session.result),
            message="Task failed.",
        )
    return ToolResponse(
        status=st.value,
        result=str(session.result) if session.result else None,
        message=f"Task ended with status: {st.value}.",
    )


async def _cmd_get_status(
    manager: SessionManager,
    session_id: str,
    session: Session,
    **kwargs: Any,
) -> ToolResponse:
    await asyncio.sleep(0.5)
    session.sync_from_handle()
    st = session.status()
    return ToolResponse(
        status=st.value,
        current_task=session.current_task,
        message=f"Current status: {st.value}",
    )


async def _cmd_get_result(
    manager: SessionManager,
    session_id: str,
    session: Session,
    **kwargs: Any,
) -> ToolResponse:
    session.sync_from_handle()
    st = session.status()
    if st == SessionStatus.COMPLETED:
        return ToolResponse(status=SessionStatus.COMPLETED.value, result=str(session.result))
    if st == SessionStatus.FAILED:
        return ToolResponse(status=SessionStatus.FAILED.value, error=str(session.result))
    return ToolResponse(
        status=st.value,
        message=f"Task not finished yet. Current status: {st.value}",
    )


async def _cmd_pause(
    manager: SessionManager,
    session_id: str,
    session: Session,
    **kwargs: Any,
) -> ToolResponse:
    if session.agent and session.status() == SessionStatus.RUNNING:
        session.agent.pause()
        session.set_paused()
        session.log("Agent paused")
        return ToolResponse(
            status=SessionStatus.PAUSED.value,
            current_task=session.current_task,
            message="Agent paused. Say 'resume' to continue, or 'update_task' to add instructions.",
        )
    return ToolResponse(
        status="error",
        error=f"Cannot pause. Current status: {session.status().value}",
    )


async def _cmd_resume(
    manager: SessionManager,
    session_id: str,
    session: Session,
    **kwargs: Any,
) -> ToolResponse:
    if session.agent and session.status() == SessionStatus.PAUSED:
        session.agent.resume()
        session.set_running()
        session.log("Agent resumed")
        return ToolResponse(status=SessionStatus.RUNNING.value, message="Agent resumed.")
    return ToolResponse(
        status="error",
        error=f"Cannot resume. Current status: {session.status().value}",
    )


async def _cmd_add_instruction(
    manager: SessionManager,
    session_id: str,
    session: Session,
    instruction: Optional[str] = None,
    **kwargs: Any,
) -> ToolResponse:
    if not instruction:
        return ToolResponse(status="error", error="instruction is required for add_instruction")
    if session.agent and session.status() in (SessionStatus.RUNNING, SessionStatus.PAUSED):
        try:
            session.agent.add_new_task(instruction)
            session.log(f"Instruction added: {instruction}")
            return ToolResponse(status="success", message=f"Instruction added: {instruction}")
        except Exception as e:
            return ToolResponse(status="error", error=str(e))
    return ToolResponse(
        status="error",
        error=f"Cannot add instruction. Current status: {session.status().value}",
    )


async def _cmd_update_task(
    manager: SessionManager,
    session_id: str,
    session: Session,
    instruction: Optional[str] = None,
    **kwargs: Any,
) -> ToolResponse:
    if not instruction:
        return ToolResponse(status="error", error="instruction is required for update_task")
    if session.status() not in (SessionStatus.PAUSED, SessionStatus.RUNNING, SessionStatus.STOPPED):
        return ToolResponse(
            status="error",
            error=f"Cannot update task. Current status: {session.status().value}",
        )
    if session.task_handle and not session.task_handle.done():
        session.task_handle.cancel()
        try:
            await session.task_handle
        except asyncio.CancelledError:
            pass
        session.log("Stopped current task for update")
    merged = f"{session.original_task or ''}\n\nADDITIONAL INSTRUCTIONS:\n{instruction}"
    session.current_task = merged
    session.log(f"Merged task: {merged}")
    session.task_handle = asyncio.create_task(_run_agent(session, merged))
    session.set_running()
    return ToolResponse(
        status=SessionStatus.RUNNING.value,
        merged_task=merged,
        message="Task updated and restarted. Continue polling for status.",
    )


async def _cmd_stop(
    manager: SessionManager,
    session_id: str,
    session: Session,
    **kwargs: Any,
) -> ToolResponse:
    if session.task_handle and not session.task_handle.done():
        session.task_handle.cancel()
        try:
            await session.task_handle
        except asyncio.CancelledError:
            pass
        session.set_stopped()
        session.log("Task stopped")
        return ToolResponse(status=SessionStatus.STOPPED.value, message="Task stopped.")
    return ToolResponse(status="error", error="No running task to stop")


async def _cmd_stop_session(
    manager: SessionManager,
    session_id: str,
    **kwargs: Any,
) -> ToolResponse:
    removed = await manager.stop_session(session_id)
    if removed:
        return ToolResponse(status="success", message="Session closed")
    return ToolResponse(status="error", error="Session not found")


# Dispatch: Command -> handler (all receive manager; most need session_id + session)
_HANDLERS: Dict[Command, Callable[..., Any]] = {
    Command.START_SESSION: _cmd_start_session,
    Command.RUN_TASK: _cmd_run_task,
    Command.RUN_TASK_AND_WAIT: _cmd_run_task_and_wait,
    Command.GET_STATUS: _cmd_get_status,
    Command.GET_RESULT: _cmd_get_result,
    Command.PAUSE: _cmd_pause,
    Command.RESUME: _cmd_resume,
    Command.ADD_INSTRUCTION: _cmd_add_instruction,
    Command.UPDATE_TASK: _cmd_update_task,
    Command.STOP: _cmd_stop,
    Command.STOP_SESSION: _cmd_stop_session,
}


# ---------------------------------------------------------------------------
# ADK entrypoint: execute() = happy path (blocking); full action set supported
# ---------------------------------------------------------------------------


async def browser_tool(
    action: str,
    session_id: Optional[str] = None,
    task: Optional[str] = None,
    instruction: Optional[str] = None,
    timeout_seconds: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Browser automation with session management.

    Preferred for ADK: use action="run_task_and_wait" (blocking) so one tool call
    runs the task and returns the result.

    Args:
        action: start_session | run_task | run_task_and_wait | get_status | get_result
                | pause | resume | add_instruction | update_task | stop | stop_session
        session_id: Required for all actions except start_session.
        task: Required for run_task and run_task_and_wait.
        instruction: Required for add_instruction and update_task.
        timeout_seconds: Max wait for run_task_and_wait (default 120).

    Returns:
        Dict with status, message, result/error as appropriate.
    """
    try:
        cmd = Command.from_action(action)
    except ValueError as e:
        return {"error": str(e)}

    manager = SessionManager.get_instance()

    if cmd == Command.START_SESSION:
        resp = await _cmd_start_session(manager)
        return resp.to_dict()

    if not session_id:
        return {"error": "session_id is required for this action"}
    session = await manager.get_session(session_id)
    if not session:
        return {"error": f"Session not found: {session_id}"}

    handler = _HANDLERS[cmd]
    if cmd == Command.STOP_SESSION:
        resp = await handler(manager, session_id=session_id)
    else:
        resp = await handler(
            manager,
            session_id=session_id,
            session=session,
            task=task,
            instruction=instruction,
            timeout_seconds=timeout_seconds,
        )
    return resp.to_dict()
