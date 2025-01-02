from typing import Protocol, Union
from inngest import Event, Function
from contextlib import contextmanager
from contextvars import ContextVar

class InngestStep(Protocol):
  async def send_event(
    self,
    step_id: str,
    events: Union[Event, list[Event]],
  ) -> list[str]:
    return []

class NoOpStep(InngestStep):
  async def send_event(self, step_id: str, events: Union[Event, list[Event]]) -> list[str]:
    return []

inngest_step_context = ContextVar[InngestStep | None]("inngest_step_context", default=NoOpStep())

def get_inngest_step_from_context() -> InngestStep:
  step = inngest_step_context.get()
  if step is None:
    raise ValueError("Inngest step not found in context")
  return step

@contextmanager
def with_inngest_step(step: InngestStep):
  inngest_step_context.set(step)
  yield
  inngest_step_context.set(None)
