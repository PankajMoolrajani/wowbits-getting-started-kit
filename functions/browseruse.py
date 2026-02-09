import asyncio
import uuid
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from browser_use import Agent, Browser, ChatOpenAI

load_dotenv()

# Global dictionary to store active sessions
sessions: Dict[str, "SessionData"] = {}


class SessionData:
    """Holds all state for a browser session."""
    
    def __init__(self, browser: Browser):
        self.browser = browser
        self.agent: Optional[Agent] = None
        self.task_handle: Optional[asyncio.Task] = None
        self.status: str = "idle"
        self.result: Any = None
        self.logs: List[str] = []
        # Store the original and current task for merging
        self.original_task: Optional[str] = None
        self.current_task: Optional[str] = None

    def log(self, message: str):
        self.logs.append(message)
        print(f"[Session] {message}")


async def browseruse(
    action: str,
    session_id: Optional[str] = None,
    task: Optional[str] = None,
    instruction: Optional[str] = None,
    timeout_seconds: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Browser automation tool with session management.

    PREFERRED for agents (e.g. Google ADK): use "run_task_and_wait" so one tool call
    runs the task and returns the result. Avoid "run_task" + repeated "get_status"
    which causes hundreds of tool calls for a single page.

    Args:
        action: One of "start_session", "run_task", "run_task_and_wait", "get_status",
                "get_result", "pause", "resume", "add_instruction", "update_task",
                "stop", "stop_session"
        session_id: Session ID (required for all actions except start_session)
        task: Task description (required for run_task and run_task_and_wait)
        instruction: Additional instruction (required for add_instruction and update_task)
        timeout_seconds: Max wait in seconds for run_task_and_wait (default 120).

    Returns:
        Dictionary with status/result/error
    """
    
    # ==================== START SESSION ====================
    if action == "start_session":
        browser = Browser(headless=False)
        sid = str(uuid.uuid4())
        sessions[sid] = SessionData(browser=browser)
        sessions[sid].log(f"Session started: {sid}")
        return {
            "status": "success",
            "session_id": sid,
            "message": "Browser session started. Now call run_task with your task."
        }

    # Validate session_id for all other actions
    if not session_id:
        return {"error": "session_id is required for this action"}
    
    if session_id not in sessions:
        return {"error": f"Session not found: {session_id}"}

    session = sessions[session_id]

    # ==================== RUN TASK (NON-BLOCKING) ====================
    if action == "run_task":
        if not task:
            return {"error": "task argument is required for run_task"}
        
        if session.status == "running":
            return {"error": "A task is already running. Check status or stop it first."}

        # Store the task for potential future merging
        session.original_task = task
        session.current_task = task

        async def agent_runner(task_to_run: str):
            try:
                llm = ChatOpenAI(model="gpt-4o-mini")
                session.agent = Agent(
                    task=task_to_run,
                    llm=llm,
                    browser=session.browser,
                )
                session.log(f"Running task: {task_to_run}")
                history = await session.agent.run()
                session.result = history
                session.status = "completed"
                session.log("Task completed successfully")
            except asyncio.CancelledError:
                session.status = "stopped"
                session.log("Task was stopped")
            except Exception as e:
                session.status = "failed"
                session.result = str(e)
                session.log(f"Task failed: {e}")

        # Start the agent as a background task
        session.task_handle = asyncio.create_task(agent_runner(task))
        session.status = "running"
        
        return {
            "status": "running",
            "message": "Task started in background. Poll with get_status, use pause/resume/update_task as needed."
        }

    # ==================== RUN TASK AND WAIT (BLOCKING – use this to avoid 100s of tool calls) ====================
    if action == "run_task_and_wait":
        if not task:
            return {"error": "task argument is required for run_task_and_wait"}

        if session.status == "running":
            return {"error": "A task is already running. Stop it first or use get_status/get_result."}

        timeout = timeout_seconds if timeout_seconds is not None else 120
        session.original_task = task
        session.current_task = task

        async def agent_runner(task_to_run: str):
            try:
                llm = ChatOpenAI(model="gpt-4o-mini")
                session.agent = Agent(
                    task=task_to_run,
                    llm=llm,
                    browser=session.browser,
                )
                session.log(f"Running task (blocking): {task_to_run}")
                history = await session.agent.run()
                session.result = history
                session.status = "completed"
                session.log("Task completed successfully")
            except asyncio.CancelledError:
                session.status = "stopped"
                session.log("Task was stopped")
            except Exception as e:
                session.status = "failed"
                session.result = str(e)
                session.log(f"Task failed: {e}")

        session.task_handle = asyncio.create_task(agent_runner(task))
        session.status = "running"

        try:
            await asyncio.wait_for(session.task_handle, timeout=float(timeout))
        except asyncio.TimeoutError:
            session.log(f"Task still running after {timeout}s (timeout). Use get_status/get_result later.")
            return {
                "status": "timeout",
                "session_id": session_id,
                "message": f"Task did not finish within {timeout}s. Call get_status or get_result later with this session_id.",
            }

        if session.status == "completed":
            return {
                "status": "completed",
                "result": str(session.result),
                "message": "Task completed.",
            }
        elif session.status == "failed":
            return {
                "status": "failed",
                "error": str(session.result),
                "message": "Task failed.",
            }
        else:
            return {
                "status": session.status,
                "result": str(session.result) if session.result else None,
                "message": f"Task ended with status: {session.status}.",
            }

    # ==================== GET STATUS ====================
    elif action == "get_status":
        # Wait 3 seconds to throttle polling rate
        # User can type "pause" in between status checks
        await asyncio.sleep(0.5)
        
        # Check if task handle is done and update status
        if session.task_handle and session.task_handle.done():
            if session.status == "running":
                try:
                    session.task_handle.result()
                    session.status = "completed"
                except Exception as e:
                    session.status = "failed"
                    session.result = str(e)
        
        return {
            "status": session.status,
            "current_task": session.current_task,
            "message": f"Current status: {session.status}"
        }

    # ==================== GET RESULT ====================
    elif action == "get_result":
        if session.status == "completed":
            return {
                "status": "completed",
                "result": str(session.result)
            }
        elif session.status == "failed":
            return {
                "status": "failed",
                "error": str(session.result)
            }
        else:
            return {
                "status": session.status,
                "message": f"Task not finished yet. Current status: {session.status}"
            }

    # ==================== PAUSE ====================
    elif action == "pause":
        if session.agent and session.status == "running":
            session.agent.pause()
            session.status = "paused"
            session.log("Agent paused")
            return {
                "status": "paused",
                "current_task": session.current_task,
                "message": "Agent paused. Say 'resume' to continue, or 'update' to add new instructions."
            }
        return {"error": f"Cannot pause. Current status: {session.status}"}

    # ==================== RESUME ====================
    elif action == "resume":
        if session.agent and session.status == "paused":
            session.agent.resume()
            session.status = "running"
            session.log("Agent resumed")
            return {"status": "running", "message": "Agent resumed."}
        return {"error": f"Cannot resume. Current status: {session.status}"}

    # ==================== ADD INSTRUCTION (live injection) ====================
    elif action == "add_instruction":
        if not instruction:
            return {"error": "instruction argument is required for add_instruction"}
        
        if session.agent and session.status in ("running", "paused"):
            try:
                session.agent.add_new_task(instruction)
                session.log(f"Instruction added: {instruction}")
                return {"status": "success", "message": f"Instruction added: {instruction}"}
            except Exception as e:
                return {"error": f"Failed to add instruction: {e}"}
        return {"error": f"Cannot add instruction. Current status: {session.status}"}

    # ==================== UPDATE TASK (stop and restart with merged task) ====================
    elif action == "update_task":
        if not instruction:
            return {"error": "instruction argument is required for update_task"}
        
        if session.status not in ("paused", "running", "stopped"):
            return {"error": f"Cannot update task. Current status: {session.status}"}

        # Stop the current task if running
        if session.task_handle and not session.task_handle.done():
            session.task_handle.cancel()
            try:
                await session.task_handle
            except asyncio.CancelledError:
                pass
            session.log("Stopped current task for update")

        # Merge original task with new instruction
        merged_task = f"{session.original_task}\n\nADDITIONAL INSTRUCTIONS:\n{instruction}"
        session.current_task = merged_task
        session.log(f"Merged task: {merged_task}")

        # Create new agent runner
        async def agent_runner(task_to_run: str):
            try:
                llm = ChatOpenAI(model="gpt-4o-mini")
                session.agent = Agent(
                    task=task_to_run,
                    llm=llm,
                    browser=session.browser,
                )
                session.log(f"Running updated task: {task_to_run}")
                history = await session.agent.run()
                session.result = history
                session.status = "completed"
                session.log("Task completed successfully")
            except asyncio.CancelledError:
                session.status = "stopped"
                session.log("Task was stopped")
            except Exception as e:
                session.status = "failed"
                session.result = str(e)
                session.log(f"Task failed: {e}")

        # Start new task with merged instructions
        session.task_handle = asyncio.create_task(agent_runner(merged_task))
        session.status = "running"
        
        return {
            "status": "running",
            "merged_task": merged_task,
            "message": "Task updated and restarted with new instructions. Continue polling for status."
        }

    # ==================== STOP ====================
    elif action == "stop":
        if session.task_handle and not session.task_handle.done():
            session.task_handle.cancel()
            try:
                await session.task_handle
            except asyncio.CancelledError:
                pass
            session.status = "stopped"
            session.log("Task stopped")
            return {"status": "stopped", "message": "Task stopped."}
        return {"error": "No running task to stop"}

    # ==================== STOP SESSION ====================
    elif action == "stop_session":
        if session.task_handle and not session.task_handle.done():
            session.task_handle.cancel()
            try:
                await session.task_handle
            except asyncio.CancelledError:
                pass
        
        if session.browser:
            await session.browser.stop()
        
        del sessions[session_id]
        return {"status": "success", "message": "Session closed"}

    else:
        return {"error": f"Unknown action: {action}"}