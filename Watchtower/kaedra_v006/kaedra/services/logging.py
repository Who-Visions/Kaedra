"""
KAEDRA v0.0.6 - Logging Service
Session logging and system diagnostics.
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Optional
from dataclasses import dataclass

from ..core.config import CHAT_LOGS_DIR, KAEDRA_HOME


@dataclass
class SessionInfo:
    """Information about a logging session."""
    filepath: Path
    start_time: datetime
    log_count: int = 0


class LoggingService:
    """
    Manages session logging and system diagnostics.
    
    Features:
    - Markdown session logs
    - System-level Python logging
    - Performance metrics
    - Error tracking
    """
    
    def __init__(self, log_file: Optional[str] = None):
        # System logger
        self._setup_system_logger(log_file)
        
        # Session state
        self._session: Optional[SessionInfo] = None
        self._session_file = None
    
    def _setup_system_logger(self, log_file: Optional[str] = None):
        """Configure Python's logging system."""
        log_path = log_file or str(KAEDRA_HOME / "kaedra.log")
        
        logging.basicConfig(
            filename=log_path,
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        self._logger = logging.getLogger("kaedra")
    
    # ══════════════════════════════════════════════════════════════════════════
    # SESSION LOGGING (Markdown chat logs)
    # ══════════════════════════════════════════════════════════════════════════
    
    def start_session(self, version: str = "0.0.6", location: str = "us-east4") -> str:
        """
        Start a new session log.
        
        Returns:
            Path to the session log file
        """
        CHAT_LOGS_DIR.mkdir(parents=True, exist_ok=True)
        
        start_time = datetime.now()
        filename = f"session_{start_time.strftime('%Y%m%d_%H%M%S')}.md"
        filepath = CHAT_LOGS_DIR / filename
        
        self._session_file = open(filepath, 'w', encoding='utf-8')
        self._session_file.write(f"# KAEDRA v{version} Session Log\n")
        self._session_file.write(f"**Started:** {start_time.strftime('%Y-%m-%d %H:%M:%S EST')}\n")
        self._session_file.write(f"**Location:** {location}\n\n")
        self._session_file.write("---\n\n")
        self._session_file.flush()
        
        self._session = SessionInfo(
            filepath=filepath,
            start_time=start_time
        )
        
        self.info(f"Session started: {filepath}")
        return str(filepath)
    
    def stop_session(self) -> Optional[str]:
        """
        Stop the current session log.
        
        Returns:
            Path to the saved session log, or None if no session active
        """
        if not self._session or not self._session_file:
            return None
        
        duration = datetime.now() - self._session.start_time
        self._session_file.write(f"\n---\n")
        self._session_file.write(f"**Ended:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S EST')}\n")
        self._session_file.write(f"**Duration:** {duration}\n")
        self._session_file.write(f"**Messages:** {self._session.log_count}\n")
        self._session_file.close()
        
        filepath = str(self._session.filepath)
        self.info(f"Session ended: {filepath}")
        
        self._session = None
        self._session_file = None
        
        return filepath
    
    @property
    def is_session_active(self) -> bool:
        """Check if a session is currently active."""
        return self._session is not None
    
    def log_message(self, role: str, content: str, model: str = None, agent: str = None):
        """
        Log a message to the current session.
        
        Args:
            role: Who sent the message (YOU, KAEDRA, BLADE, NYX, SYSTEM)
            content: The message content
            model: The model used (optional)
            agent: The agent name (optional)
        """
        if not self._session_file:
            return
        
        timestamp = datetime.now().strftime('%H:%M:%S')
        tags = []
        if model:
            tags.append(model)
        if agent:
            tags.append(agent)
        tag_str = f" [{', '.join(tags)}]" if tags else ""
        
        self._session_file.write(f"### [{role}]{tag_str} - {timestamp}\n")
        self._session_file.write(f"{content}\n\n")
        self._session_file.flush()
        
        self._session.log_count += 1
    
    # ══════════════════════════════════════════════════════════════════════════
    # SYSTEM LOGGING
    # ══════════════════════════════════════════════════════════════════════════
    
    def debug(self, message: str):
        """Log a debug message."""
        self._logger.debug(message)
    
    def info(self, message: str):
        """Log an info message."""
        self._logger.info(message)
    
    def warning(self, message: str):
        """Log a warning message."""
        self._logger.warning(message)
    
    def error(self, message: str, exc_info: bool = False):
        """Log an error message."""
        self._logger.error(message, exc_info=exc_info)
    
    def critical(self, message: str, exc_info: bool = False):
        """Log a critical message."""
        self._logger.critical(message, exc_info=exc_info)
    
    # ══════════════════════════════════════════════════════════════════════════
    # PERFORMANCE METRICS
    # ══════════════════════════════════════════════════════════════════════════
    
    def log_latency(self, operation: str, duration_ms: float):
        """Log operation latency for performance tracking."""
        self._logger.info(f"LATENCY [{operation}]: {duration_ms:.2f}ms")
    
    def log_api_call(self, model: str, tokens_in: int, tokens_out: int, duration_ms: float):
        """Log API call metrics."""
        self._logger.info(
            f"API [{model}]: in={tokens_in}, out={tokens_out}, time={duration_ms:.2f}ms"
        )
