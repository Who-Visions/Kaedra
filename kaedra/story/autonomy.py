"""
🤖 Autonomous Novelist Control Types (v9.2)
More intelligent state, better steering, fewer mystery bugs.
"""
import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any


class AutoState(str, Enum):
    idle = "idle"
    running = "running"
    paused = "paused"
    stopping = "stopping"
    finished = "finished"
    errored = "errored"


class InjectKind(str, Enum):
    note = "note"                 # add flavor, direction, ideas
    constraint = "constraint"     # hard rule, do not violate
    retcon = "retcon"             # change canon, override prior
    question = "question"         # force the engine to ask or decide
    tool_request = "tool_request" # ask it to run a tool lane
    mode_switch = "mode_switch"   # switch NORMAL, GOD, DIRECTOR, etc


class ControlKind(str, Enum):
    pause = "pause"
    resume = "resume"
    stop = "stop"
    hold = "hold"                 # sleep until time, used for idle waits
    inject = "inject"
    set_goal = "set_goal"         # change targets mid run
    status = "status"             # request status snapshot
    checkpoint = "checkpoint"     # force save snapshot


@dataclass
class InjectMsg:
    kind: InjectKind
    text: str
    priority: int = 50            # lower number means earlier
    beat_index: Optional[int] = None
    scene: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.monotonic)


@dataclass
class ControlMessage:
    kind: ControlKind
    payload: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.monotonic)


@dataclass
class AutoSpec:
    """
    Mission specifications for autonomous generation.
    Use stop conditions together, first one to hit ends the run.
    """
    enabled: bool = False

    target_words: Optional[int] = None
    time_budget_s: Optional[int] = None
    max_beats: int = 40

    chunk_max_tokens: int = 900
    min_words_per_chunk: int = 120
    max_words_per_chunk: int = 420

    idle_grace_s: int = 30         # wait this long for user input before continuing
    barge_window_s: int = 600      # if user barges in, give them up to 10 minutes to keep injecting

    started_at: float = 0.0        # monotonic start time
    words_written: int = 0
    current_beat_index: int = 0

    state: AutoState = AutoState.idle
    stop_reason: Optional[str] = None

    def reset_run_counters(self):
        self.started_at = time.monotonic()
        self.words_written = 0
        self.current_beat_index = 0
        self.stop_reason = None
        self.state = AutoState.idle

    def elapsed_s(self) -> float:
        if not self.started_at:
            return 0.0
        return time.monotonic() - self.started_at

    def should_stop(self) -> bool:
        if self.target_words is not None and self.words_written >= self.target_words:
            self.stop_reason = "target_words"
            return True
        if self.time_budget_s is not None and self.elapsed_s() >= self.time_budget_s:
            self.stop_reason = "time_budget_s"
            return True
        if self.current_beat_index >= self.max_beats:
            self.stop_reason = "max_beats"
            return True
        return False


@dataclass
class AutoControl:
    """
    Runtime control primitives for async steering.
    This is the only bridge between user input and the auto loop.
    """
    queue: asyncio.Queue = field(default_factory=asyncio.Queue)

    resume_event: asyncio.Event = field(default_factory=asyncio.Event)
    stop_event: asyncio.Event = field(default_factory=asyncio.Event)

    last_user_input_at: float = field(default_factory=time.monotonic)
    hold_until: float = 0.0

    def __post_init__(self):
        # Default behavior, running is allowed unless paused.
        self.resume_event.set()

    async def send(self, msg: ControlMessage):
        await self.queue.put(msg)

    async def inject(self, inject: InjectMsg):
        await self.queue.put(ControlMessage(kind=ControlKind.inject, payload={"inject": inject}))

    async def pause(self):
        await self.send(ControlMessage(kind=ControlKind.pause))

    async def resume(self):
        await self.send(ControlMessage(kind=ControlKind.resume))

    async def stop(self, reason: str = "user_stop"):
        await self.send(ControlMessage(kind=ControlKind.stop, payload={"reason": reason}))

    async def hold(self, seconds: int):
        until = time.monotonic() + max(0, seconds)
        await self.send(ControlMessage(kind=ControlKind.hold, payload={"until": until}))

    def touch_user_input(self):
        self.last_user_input_at = time.monotonic()
