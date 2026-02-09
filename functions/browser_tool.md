# browser_tool

Browser automation with session management. Use this tool in your own skills and agents to control a real browser: start a session, run tasks, pause or resume, add or update instructions, and get results.

---

## Integrating in a skill or agent

- **Tool name:** `browser_tool`  
  Register or attach the async function `browser_tool` (from `browser_tool.py`) as a tool. The tool name your agent/skill uses should be **browser_tool**.

- **Preferred flow for agents:**  
  Use **run_task_and_wait** so that a single tool call runs the task and returns the result. That keeps tool-call count low and behavior predictable. Avoid using **run_task** and then repeatedly calling **get_status** for one logical task, as that leads to many tool calls.

- **Session lifecycle:**  
  The agent or skill should call **start_session** first and store the returned **session_id**. Use that **session_id** for all later actions (run task, get status, pause, etc.). When the user is done or the task is finished, call **stop_session** with that **session_id** so the browser closes and the session is cleaned up.

- **Instructions for your agent/skill:**  
  Tell your agent to prefer **run_task_and_wait** for one-shot tasks; to pass clear, step-by-step text in **task**; to always call **stop_session** when done; and to handle **error** and **status** (e.g. `failed`, `timeout`) in the response.

---

## Commands (actions)

You invoke the tool with an **action** (and the right arguments). These are the available commands:

| Action | What it does | Required besides action |
|--------|----------------|-------------------------|
| **start_session** | Starts a new browser session. Returns a **session_id** to use in all other actions. | None |
| **run_task_and_wait** | Runs the given task and waits until it finishes (or times out). Returns the result in the response. **Use this for most single tasks.** | session_id, task |
| **run_task** | Starts the task in the background. You must later use **get_status** and **get_result** to check progress and get the result. | session_id, task |
| **get_status** | Returns the current status of the session/task (e.g. idle, running, completed, failed). | session_id |
| **get_result** | Returns the final result when the task has completed or failed. | session_id |
| **pause** | Pauses the running browser agent. | session_id |
| **resume** | Resumes a paused agent. | session_id |
| **add_instruction** | Adds an instruction to the current task without restarting it. | session_id, instruction |
| **update_task** | Merges new instructions with the original task and restarts the task. | session_id, instruction |
| **stop** | Stops the current task. | session_id |
| **stop_session** | Closes the browser and removes the session. **Should be called when done.** | session_id |

---

## Options (parameters)

- **action** (required) — One of the commands in the table above.
- **session_id** — Required for every action except **start_session**. Use the **session_id** returned by **start_session**.
- **task** — Required for **run_task** and **run_task_and_wait**. The instruction for the browser (e.g. go to a URL, click something, type in a field). Clear, step-by-step text works best.
- **instruction** — Required for **add_instruction** and **update_task**. The extra or revised instruction to add or merge.
- **timeout_seconds** — Optional. Only used for **run_task_and_wait**. Maximum time to wait in seconds (default is 120).

---

## Response fields

The tool returns a dictionary. You may see:

- **status** — Indicates outcome or state: e.g. success, error, idle, running, paused, completed, failed, stopped, timeout.
- **message** — Short human-readable message.
- **session_id** — Included when relevant (e.g. after **start_session**).
- **result** — The task result when the task completed successfully.
- **error** — Error message when something went wrong or the task failed.
- **current_task** / **merged_task** — Shown in some responses for context.

Your skill or agent should read **status** and **error** (or **result**) to decide what to do next and what to show the user.

---

## Recommended usage

- **Single task:** Start session → run_task_and_wait with session_id and task → then stop_session. Keeps to a small number of tool calls.
- **Background or long task:** Start session → run_task → poll get_status until completed/failed/timeout → get_result → stop_session.
- **User says “pause” / “resume”:** Use **pause** or **resume** with the same session_id.
- **User changes goal:** Use **update_task** with session_id and the new instruction.
- **User adds a small tweak:** Use **add_instruction** with session_id and the extra instruction.
- **When finished:** Always call **stop_session** with the session_id so the browser and session are cleaned up.
