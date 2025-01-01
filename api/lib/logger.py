from contextlib import contextmanager
from contextvars import ContextVar
from typing import Protocol
from logging import Logger as PrintLogger

class Logger(Protocol):
  def info(self, msg, *args, **kwargs):
    pass

  def debug(self, msg, *args, **kwargs):
    pass

  def error(self, msg, *args, **kwargs):
    pass

  def warning(self, msg, *args, **kwargs):
    pass

  def critical(self, msg, *args, **kwargs):
    pass

logger_context = ContextVar[Logger | None]('logger', default=PrintLogger)

def get_logger_from_context() -> Logger:
  logger = logger_context.get()
  if logger is None:
    raise ValueError("Logger not found in context")
  return logger

def set_logger(logger: Logger | None) -> None:
  logger_context.set(logger)

@contextmanager
def with_logger(logger: Logger):
  set_logger(logger)
  yield
  set_logger(None)
