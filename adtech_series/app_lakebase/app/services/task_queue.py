import threading
import logging
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Generator, Literal


TypingStage = Literal["thinking", "generating", "finishing"]


class StreamingBuffer:
    """
    Thread-safe append-only buffer for streaming text.
    A cursor (integer) can be used by readers to fetch new content since last read.
    Now includes typing stage tracking for AI generation indicators.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._chunks: List[str] = []
        self._done: bool = False
        self._error: Optional[str] = None
        self._typing_stage: TypingStage = "thinking"
        self._stage_start_time: float = time.time()

    def append(self, text_chunk: str) -> None:
        if not text_chunk:
            return
        with self._lock:
            # Coerce any non-string content to string defensively
            try:
                if not isinstance(text_chunk, str):
                    text_chunk = str(text_chunk)
            except Exception:
                text_chunk = ""
            if text_chunk:
                self._chunks.append(text_chunk)

    def mark_done(self) -> None:
        with self._lock:
            self._done = True

    def mark_error(self, error_message: str) -> None:
        with self._lock:
            self._error = error_message
            self._done = True

    def read_all(self) -> str:
        with self._lock:
            return "".join(self._chunks)

    def read_since(self, cursor: int) -> str:
        with self._lock:
            # Cursor is number of characters already consumed
            accumulated = "".join(self._chunks)
            return accumulated[cursor:]

    def length(self) -> int:
        with self._lock:
            return len("".join(self._chunks))

    @property
    def is_done(self) -> bool:
        with self._lock:
            return self._done

    @property
    def error(self) -> Optional[str]:
        with self._lock:
            return self._error

    def set_typing_stage(self, stage: TypingStage) -> None:
        """Update the current typing stage for UI indicators"""
        with self._lock:
            if self._typing_stage != stage:
                self._typing_stage = stage
                self._stage_start_time = time.time()

    @property
    def typing_stage(self) -> TypingStage:
        with self._lock:
            return self._typing_stage

    @property
    def stage_duration(self) -> float:
        """Time in seconds since the current stage started"""
        with self._lock:
            return time.time() - self._stage_start_time

    def get_typing_display_text(self) -> str:
        """Get appropriate display text for current typing stage"""
        with self._lock:
            if self._typing_stage == "thinking":
                return "🤔 Thinking..."
            elif self._typing_stage == "generating":
                # Show three dots with cycling animation effect
                dots_count = int((time.time() - self._stage_start_time) * 2) % 4
                return "💭 " + "." * (dots_count if dots_count > 0 else 3)
            elif self._typing_stage == "finishing":
                return "✨ Finishing up..."
            return ""


@dataclass
class SaveStatus:
    message_id: str
    ok: bool = False
    error: Optional[str] = None


_executor = ThreadPoolExecutor(max_workers=8)
_generations: Dict[str, StreamingBuffer] = {}
_saves: Dict[str, SaveStatus] = {}
_registry_lock = threading.Lock()
_history_results: Dict[str, List[Dict[str, Any]]] = {}

logger = logging.getLogger(__name__)


def create_message_id() -> str:
    return str(uuid.uuid4())


def submit_generation(message_id: str, generate_fn: Callable[[], str], simulate_stream: bool = False, chunk_delay_seconds: float = 0.05) -> None:
    """
    Submit a generation job. If simulate_stream is True, the final text will be split
    into small chunks and appended to a streaming buffer over time to emulate streaming.
    """
    buffer = StreamingBuffer()
    with _registry_lock:
        _generations[message_id] = buffer

    logger.debug(f"submit_generation: queued message_id={message_id}, simulate_stream={simulate_stream}")

    def _run() -> None:
        try:
            logger.debug(f"submit_generation.run: start message_id={message_id}")
            result_text = generate_fn()
            if not simulate_stream:
                buffer.append(result_text)
                buffer.mark_done()
                logger.debug(f"submit_generation.run: done (non-stream) message_id={message_id}, len={len(result_text)}")
                return

            # Simulated streaming by words (optional)
            words = result_text.split(" ")
            for word in words:
                buffer.append((word + " "))
                time.sleep(chunk_delay_seconds)
            buffer.mark_done()
            logger.debug(f"submit_generation.run: done (stream) message_id={message_id}, total_len={buffer.length()}")
        except Exception as gen_err:
            buffer.mark_error(str(gen_err))
            logger.exception(f"submit_generation.run: error message_id={message_id}: {gen_err}")

    _executor.submit(_run)


def submit_streaming_generation(message_id: str, stream_generator_fn: Callable[[], Generator[str, None, None]]) -> None:
    """
    Submit a real streaming generation job. Takes a function that returns a generator
    that yields text chunks as they arrive from the model.
    Now includes proper typing stage management.
    """
    buffer = StreamingBuffer()
    with _registry_lock:
        _generations[message_id] = buffer

    logger.debug(f"submit_streaming_generation: queued message_id={message_id}")

    def _run() -> None:
        try:
            logger.debug(f"submit_streaming_generation.run: start message_id={message_id}")
        
            buffer.set_typing_stage("thinking")
            stream_generator = stream_generator_fn()
            chunk_count = 0
            
            for chunk in stream_generator:
                if chunk:  # Only append non-empty chunks
                    buffer.append(chunk)
                    chunk_count += 1
                    
            buffer.mark_done()
            logger.debug(f"submit_streaming_generation.run: done message_id={message_id}, chunks={chunk_count}, total_len={buffer.length()}")
        except Exception as gen_err:
            buffer.mark_error(str(gen_err))
            logger.exception(f"submit_streaming_generation.run: error message_id={message_id}: {gen_err}")

    _executor.submit(_run)


def get_generation_buffer(message_id: str) -> Optional[StreamingBuffer]:
    with _registry_lock:
        return _generations.get(message_id)


def submit_save(message_id: str, save_fn: Callable[[], None]) -> None:
    status = SaveStatus(message_id=message_id)
    with _registry_lock:
        # Guard: if this message_id already has a pending or successful save, skip duplicate submission
        existing = _saves.get(message_id)
        if existing and (existing.ok or existing.error is None):
            logger.debug(f"submit_save: duplicate submission ignored message_id={message_id}")
            return
        _saves[message_id] = status

    def _run() -> None:
        try:
            logger.debug(f"submit_save.run: start message_id={message_id}")
            save_fn()
            status.ok = True
            logger.debug(f"submit_save.run: success message_id={message_id}")
        except Exception as save_err:
            status.error = str(save_err)
            logger.exception(f"submit_save.run: error message_id={message_id}: {save_err}")
        finally:
            with _registry_lock:
                _saves[message_id] = status
                logger.debug(f"submit_save.run: status recorded message_id={message_id}, ok={status.ok}")

    _executor.submit(_run)


def get_save_status(message_id: str) -> Optional[SaveStatus]:
    with _registry_lock:
        return _saves.get(message_id)


def pop_save_status(message_id: str) -> Optional[SaveStatus]:
    """
    Return a terminal save status (success or error). If the status is still pending
    (ok == False and error is None), do not pop it yet so a subsequent tick can read
    the final result.
    """
    with _registry_lock:
        status = _saves.get(message_id)
        if status is None:
            return None
        is_terminal = status.ok or (status.error is not None)
        if not is_terminal:
            logger.debug(f"pop_save_status: pending message_id={message_id} (not popped)")
            return None
        # Terminal -> remove and return
        _saves.pop(message_id, None)
        logger.debug(f"pop_save_status: popped terminal message_id={message_id}, ok={status.ok}, error={status.error}")
        return status


def clear_finished_generation(message_id: str) -> None:
    with _registry_lock:
        buf = _generations.get(message_id)
        if buf and buf.is_done:
            _generations.pop(message_id, None)
            logger.debug(f"clear_finished_generation: cleared message_id={message_id}")


def submit_history_load(key: str, load_fn: Callable[[], List[Dict[str, Any]]]) -> None:
    """
    Run a background load for chat history (or any list of dicts), indexed by `key` (e.g., chat_id).
    The full result is stored atomically and can be consumed via pop_history_result.
    """
    logger.debug(f"submit_history_load: queued key={key}")

    def _run() -> None:
        try:
            result = load_fn()
            logger.debug(f"submit_history_load.run: success key={key}, items={len(result)}")
        except Exception as err:
            # Store an empty list on error to avoid blocking the UI
            result = []
            logger.exception(f"submit_history_load.run: error key={key}: {err}")
        finally:
            with _registry_lock:
                _history_results[key] = result
                logger.debug(f"submit_history_load.run: result recorded key={key}")

    _executor.submit(_run)


def pop_history_result(key: str) -> Optional[List[Dict[str, Any]]]:
    with _registry_lock:
        result = _history_results.pop(key, None)
        if result is not None:
            logger.debug(f"pop_history_result: popped key={key}, items={len(result)}")
        return result


