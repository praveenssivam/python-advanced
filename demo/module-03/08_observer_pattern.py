"""
08_observer_pattern.py
========================
Observer Pattern — a subject notifies a list of observers whenever
its state changes. Observers can be added or removed without touching
the subject's core logic.

Run:
    python demo/module-03/08_observer_pattern.py
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime


# ══════════════════════════════════════════════════════════════════════════════
# OVERVIEW
#
# Two roles:
#   Subject (PipelineRunner)  — the thing being observed.
#                               Maintains a list of Observer objects.
#                               Calls notify(event) when something happens.
#
#   Observer                  — any object that implements handle(event).
#                               Registered with the subject at setup time.
#
# Adding a new observer:
#   1. Write a class that implements the Observer interface.
#   2. Call subject.attach(new_observer).
#   PipelineRunner never changes.
#
# Flow for PipelineRunner.run():
#   run() → notify("pipeline.start")
#           → for each observer: observer.handle(event)
#   run() → ... execute steps ...
#   run() → notify("pipeline.complete") or notify("pipeline.error")
#           → for each observer: observer.handle(event)
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class PipelineEvent:
    """Immutable snapshot passed to every observer on each notification."""

    name: str                           # e.g. "pipeline.start", "step.complete"
    pipeline_id: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    metadata: dict = field(default_factory=dict)
    error: Exception | None = None


class Observer(ABC):
    """Abstract observer — must be able to handle a PipelineEvent."""

    @abstractmethod
    def handle(self, event: PipelineEvent) -> None: ...


class Subject:
    """Mixin that gives any class an observer list and notify() method."""

    def __init__(self):
        self._observers: list[Observer] = []

    def attach(self, observer: Observer) -> None:
        self._observers.append(observer)

    def detach(self, observer: Observer) -> None:
        self._observers.remove(observer)

    def notify(self, event: PipelineEvent) -> None:
        """Broadcast event to all attached observers."""
        # Flow: for each observer → observer.handle(event)
        for obs in self._observers:
            obs.handle(event)


# ── Concrete observers ───────────────────────────────────────────────────────

class LoggingObserver(Observer):
    """Prints a structured log line for each event it receives."""

    def handle(self, event: PipelineEvent) -> None:
        meta = f" {event.metadata}" if event.metadata else ""
        print(f"  [LOG  ] [{event.timestamp}] {event.pipeline_id} — {event.name}{meta}")


class MetricsObserver(Observer):
    """Accumulates timing metrics per pipeline."""

    def __init__(self):
        self._start_times: dict[str, str] = {}
        self.metrics: dict[str, dict] = {}

    def handle(self, event: PipelineEvent) -> None:
        pid = event.pipeline_id
        if event.name == "pipeline.start":
            self._start_times[pid] = datetime.now()
            self.metrics[pid] = {"status": "running", "steps_ok": 0, "steps_failed": 0}
        elif event.name == "step.complete":
            self.metrics.setdefault(pid, {})
            self.metrics[pid]["steps_ok"] = self.metrics[pid].get("steps_ok", 0) + 1
        elif event.name == "step.failed":
            self.metrics[pid]["steps_failed"] = self.metrics[pid].get("steps_failed", 0) + 1
        elif event.name in ("pipeline.complete", "pipeline.error"):
            elapsed = "n/a"
            if pid in self._start_times:
                delta = datetime.now() - self._start_times[pid]
                elapsed = f"{delta.total_seconds():.3f}s"
            self.metrics[pid]["status"] = "complete" if "complete" in event.name else "error"
            self.metrics[pid]["elapsed"] = elapsed
            print(f"  [METRICS] {pid}: {self.metrics[pid]}")


class AlertObserver(Observer):
    """NEW observer — added without modifying Subject or any other observer."""

    def __init__(self, alert_on: set[str] | None = None):
        self._alert_on = alert_on or {"pipeline.error", "step.failed"}

    def handle(self, event: PipelineEvent) -> None:
        if event.name in self._alert_on:
            reason = str(event.error) if event.error else event.metadata.get("reason", "")
            print(f"  [ALERT] ⚠ {event.name.upper()} on {event.pipeline_id}: {reason}")


# ── Subject (PipelineRunner) ─────────────────────────────────────────────────

class PipelineRunner(Subject):
    """Runs a list of named processing steps and notifies observers at each stage.

    PipelineRunner never imports or references concrete observer classes.
    All it does is call self.notify(event) at the right moments.
    """

    def __init__(self, pipeline_id: str):
        super().__init__()
        self._id = pipeline_id

    def run(self, steps: list[tuple[str, bool]]) -> None:
        """Run (step_name, should_succeed) pairs. should_succeed=False simulates a failure."""

        # Flow: notify start → for each step: notify step event → notify end
        self.notify(PipelineEvent("pipeline.start", self._id))

        encountered_error = False
        for step_name, should_succeed in steps:
            if should_succeed:
                self.notify(PipelineEvent(
                    "step.complete", self._id,
                    metadata={"step": step_name},
                ))
            else:
                err = RuntimeError(f"Step '{step_name}' timed out")
                self.notify(PipelineEvent(
                    "step.failed", self._id,
                    metadata={"step": step_name},
                    error=err,
                ))
                encountered_error = True
                break  # stop pipeline on first failure

        final = "pipeline.error" if encountered_error else "pipeline.complete"
        self.notify(PipelineEvent(final, self._id))


def demo_observer():
    print("=" * 60)
    print("Observer Pattern — subject notifies all registered observers")
    print("=" * 60)

    print()
    print("--- Successful pipeline with LoggingObserver + MetricsObserver ---")
    runner = PipelineRunner("etl-daily")
    metrics = MetricsObserver()
    runner.attach(LoggingObserver())
    runner.attach(metrics)

    # Flow: runner.run(steps)
    #   → notify("pipeline.start")  → LoggingObserver.handle + MetricsObserver.handle
    #   → notify("step.complete")   × 3
    #   → notify("pipeline.complete") → both observers
    runner.run([("extract", True), ("transform", True), ("load", True)])

    print()
    print("--- Pipeline with a failure — AlertObserver also attached ---")
    runner2 = PipelineRunner("backfill-2026-03")
    runner2.attach(LoggingObserver())
    runner2.attach(MetricsObserver())
    runner2.attach(AlertObserver())  # NEW observer — PipelineRunner unchanged

    runner2.run([("extract", True), ("transform", False), ("load", True)])

    print()
    print("AlertObserver was added with zero changes to PipelineRunner.")
    print("Detaching an observer is equally simple: runner.detach(obs).")


def demo_detach():
    print("\n" + "=" * 60)
    print("Detaching an observer at runtime")
    print("=" * 60)
    print()

    runner = PipelineRunner("incremental-load")
    logger = LoggingObserver()
    metrics = MetricsObserver()
    runner.attach(logger)
    runner.attach(metrics)

    print("Run 1 — both observers active:")
    runner.run([("read", True)])

    runner.detach(logger)
    print("\nRun 2 — LoggingObserver detached (metrics only):")
    runner.run([("read", True)])


def main():
    demo_observer()
    demo_detach()


if __name__ == "__main__":
    main()
