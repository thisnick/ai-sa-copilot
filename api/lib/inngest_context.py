from inngest import Step
from contextlib import contextmanager
from contextvars import ContextVar

inngest_step_context = ContextVar[Step | None]("inngest_step_context", default=None)

def get_inngest_step_from_context() -> Step:
  step = inngest_step_context.get()
  if step is None:
    raise ValueError("Inngest step not found in context")
  return step

@contextmanager
def with_inngest_step(step: Step):
  inngest_step_context.set(step)
  yield
  inngest_step_context.set(None)
