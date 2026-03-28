"""Gemini core for Muswin persona, session memory, and tool routing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from google import genai
from google.genai import errors as genai_errors
from google.genai import types

from config import get_settings


SYSTEM_PROMPT = (
    "Your name is Muswin. You are an advanced, CLI-based Windows assistant. "
    "You are highly efficient but possess a dry, sarcastic, and condescending "
    "persona. Keep verbal responses under 2 sentences."
)


@dataclass(frozen=True)
class ToolResult:
    """Normalized result from a callable tool."""

    name: str
    ok: bool
    output: str


class GeminiCore:
    """Owns Gemini chat session and routes model-driven tool calls."""

    def __init__(self, tool_handlers: dict[str, Callable[..., str]] | None = None) -> None:
        self.settings = get_settings()
        self._client = genai.Client(api_key=self.settings.gemini_api_key)
        self._active_model_name = self.settings.gemini_model_name

        self._tool_handlers = tool_handlers or {}
        self._tools = self._build_tool_declarations()

        self._chat = self._create_chat(self._active_model_name)

    def process_user_input(self, text: str) -> str:
        """Send user text to Gemini and resolve optional tool calls."""

        try:
            response = self._send_with_fallback(text)
            if response is None:
                return (
                    "Rate limits smoked your request. Switch to a Flash model or wait a minute and try again."
                )

            calls = self._extract_tool_calls(response)
            if not calls:
                return self._extract_text(response)

            tool_summaries: list[str] = []
            for call in calls:
                tool_result = self._execute_tool_call(call)
                tool_summaries.append(
                    f"Tool {tool_result.name}: {'ok' if tool_result.ok else 'failed'} - {tool_result.output}"
                )

            follow_up_prompt = (
                "The requested actions were executed with these results:\n"
                + "\n".join(tool_summaries)
                + "\nRespond to the user in your persona."
            )
            follow_up = self._send_with_fallback(follow_up_prompt)
            if follow_up is None:
                return "Task done, but API quota is exhausted right now. Ask again in a moment."

            return self._extract_text(follow_up)
        except Exception as exc:  # noqa: BLE001
            return f"Gemini API error: {exc}"

    def _create_chat(self, model_name: str):
        return self._client.chats.create(
            model=model_name,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                tools=self._tools,
            ),
        )

    def _send_with_fallback(self, text: str):
        try:
            return self._chat.send_message(text)
        except genai_errors.ClientError as exc:
            if not self._is_quota_error(exc):
                raise

        for fallback_model in self._fallback_models():
            try:
                candidate_chat = self._create_chat(fallback_model)
                response = candidate_chat.send_message(text)
                self._chat = candidate_chat
                self._active_model_name = fallback_model
                return response
            except genai_errors.ClientError as fallback_exc:
                if not self._is_quota_error(fallback_exc):
                    raise

        return None

    def _fallback_models(self) -> list[str]:
        order = [
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-1.5-flash",
        ]
        return [m for m in order if m != self._active_model_name]

    @staticmethod
    def _is_quota_error(exc: Exception) -> bool:
        status_code = getattr(exc, "status_code", None)
        text = str(exc).upper()
        return status_code == 429 or "RESOURCE_EXHAUSTED" in text

    def _build_tool_declarations(self) -> list[types.Tool]:
        """Declare tools Gemini is allowed to call."""

        return [
            types.Tool(
                function_declarations=[
                    types.FunctionDeclaration(
                        name="open_app",
                        description="Open a local Windows application by common name.",
                        parameters={
                            "type": "object",
                            "properties": {
                                "app_name": {
                                    "type": "string",
                                    "description": "Human-friendly app name, e.g. vscode or spotify.",
                                }
                            },
                            "required": ["app_name"],
                        },
                    ),
                    types.FunctionDeclaration(
                        name="open_folder",
                        description="Open a folder path in Windows Explorer.",
                        parameters={
                            "type": "object",
                            "properties": {
                                "path": {"type": "string"},
                            },
                            "required": ["path"],
                        },
                    ),
                    types.FunctionDeclaration(
                        name="clean_directory",
                        description="Sort files in a folder into categories.",
                        parameters={
                            "type": "object",
                            "properties": {
                                "path": {
                                    "type": "string",
                                    "description": "Absolute or user-relative directory path.",
                                }
                            },
                            "required": ["path"],
                        },
                    ),
                    types.FunctionDeclaration(
                        name="create_directory",
                        description="Create a directory path if it does not already exist.",
                        parameters={
                            "type": "object",
                            "properties": {"path": {"type": "string"}},
                            "required": ["path"],
                        },
                    ),
                    types.FunctionDeclaration(
                        name="move_path",
                        description="Move a file or folder from source to destination.",
                        parameters={
                            "type": "object",
                            "properties": {
                                "source": {"type": "string"},
                                "destination": {"type": "string"},
                            },
                            "required": ["source", "destination"],
                        },
                    ),
                    types.FunctionDeclaration(
                        name="copy_path",
                        description="Copy a file or folder from source to destination.",
                        parameters={
                            "type": "object",
                            "properties": {
                                "source": {"type": "string"},
                                "destination": {"type": "string"},
                            },
                            "required": ["source", "destination"],
                        },
                    ),
                    types.FunctionDeclaration(
                        name="delete_path",
                        description="Delete a file or folder (force=true required).",
                        parameters={
                            "type": "object",
                            "properties": {
                                "path": {"type": "string"},
                                "force": {"type": "boolean"},
                            },
                            "required": ["path"],
                        },
                    ),
                    types.FunctionDeclaration(
                        name="list_directory",
                        description="List files and folders in a given directory path.",
                        parameters={
                            "type": "object",
                            "properties": {
                                "path": {
                                    "type": "string",
                                    "description": "Absolute or user-relative directory path.",
                                },
                                "limit": {
                                    "type": "integer",
                                    "description": "Maximum number of entries to show.",
                                },
                            },
                            "required": ["path"],
                        },
                    ),
                    types.FunctionDeclaration(
                        name="run_shell_command",
                        description="Run a shell command and return output.",
                        parameters={
                            "type": "object",
                            "properties": {"command": {"type": "string"}},
                            "required": ["command"],
                        },
                    ),
                    types.FunctionDeclaration(
                        name="list_processes",
                        description="List active processes.",
                        parameters={
                            "type": "object",
                            "properties": {"limit": {"type": "integer"}},
                        },
                    ),
                    types.FunctionDeclaration(
                        name="kill_process",
                        description="Kill a process by name or PID.",
                        parameters={
                            "type": "object",
                            "properties": {"identifier": {"type": "string"}},
                            "required": ["identifier"],
                        },
                    ),
                    types.FunctionDeclaration(
                        name="get_system_info",
                        description="Get basic operating system and hardware details.",
                        parameters={
                            "type": "object",
                            "properties": {},
                        },
                    ),
                    types.FunctionDeclaration(
                        name="trigger_routine",
                        description="Run a named routine made of multiple actions.",
                        parameters={
                            "type": "object",
                            "properties": {
                                "routine_name": {
                                    "type": "string",
                                    "description": "Routine label such as coding_mode.",
                                }
                            },
                            "required": ["routine_name"],
                        },
                    ),
                    types.FunctionDeclaration(
                        name="search_web",
                        description="Research a topic and return summarized source text.",
                        parameters={
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "Search query to research.",
                                }
                            },
                            "required": ["query"],
                        },
                    ),
                    types.FunctionDeclaration(
                        name="osint_lookup",
                        description="Search public footprint traces for a username or email.",
                        parameters={
                            "type": "object",
                            "properties": {
                                "identity": {
                                    "type": "string",
                                    "description": "Username or email to investigate.",
                                }
                            },
                            "required": ["identity"],
                        },
                    ),
                ]
            )
        ]

    def _extract_tool_calls(self, response: Any) -> list[dict[str, Any]]:
        """Extract function calls from Gemini response payload."""

        calls: list[dict[str, Any]] = []
        candidates = getattr(response, "candidates", []) or []
        for candidate in candidates:
            content = getattr(candidate, "content", None)
            parts = getattr(content, "parts", []) if content else []
            for part in parts:
                function_call = getattr(part, "function_call", None)
                if not function_call:
                    continue

                name = getattr(function_call, "name", "")
                args = dict(getattr(function_call, "args", {}) or {})
                if name:
                    calls.append({"name": name, "args": args})
        return calls

    def _execute_tool_call(self, call: dict[str, Any]) -> ToolResult:
        """Execute tool handler when available, otherwise return fallback."""

        name = call.get("name", "")
        args = call.get("args", {})
        handler = self._tool_handlers.get(name)

        if not handler:
            return ToolResult(
                name=name or "unknown_tool",
                ok=False,
                output="Tool handler is not implemented yet in this build.",
            )

        try:
            output = handler(**args)
            return ToolResult(name=name, ok=True, output=str(output))
        except Exception as exc:  # noqa: BLE001
            return ToolResult(name=name, ok=False, output=f"Runtime error: {exc}")

    @staticmethod
    def _extract_text(response: Any) -> str:
        """Read text from Gemini response safely."""

        text = getattr(response, "text", None)
        if isinstance(text, str) and text.strip():
            return text.strip()

        candidates = getattr(response, "candidates", []) or []
        for candidate in candidates:
            content = getattr(candidate, "content", None)
            parts = getattr(content, "parts", []) if content else []
            for part in parts:
                part_text = getattr(part, "text", None)
                if isinstance(part_text, str) and part_text.strip():
                    return part_text.strip()

        return "I processed that. You are welcome."
