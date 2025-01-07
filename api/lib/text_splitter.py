import re
from typing import Generator, Optional

class HierarchicalMarkdownSplitter:
  def __init__(self, chunk_size: int):
    self.chunk_size = chunk_size

    # Regex for code fence
    self.fence_pattern = re.compile(r"^(```|~~~)")
    self.splitter_patterns = [
      re.compile(r"^(#{1})\s.*"),
      re.compile(r"^(#{2})\s.*"),
      re.compile(r"^(#{3})\s.*"),
      re.compile(r"^(#{4})\s.*"),
      re.compile(r"^(#{5})\s.*"),
      re.compile(r"^(#{6})\s.*"),
      re.compile(r"^\s*[-*_]{3,}\s*$"),
    ]

  def split(self, text: str) -> Generator[str, None, None]:
    """
    Public method to split text into chunks no larger than self.chunk_size.
    Yields each chunk as a string.
    """
    yield from self._split_recursive(text, 0)

  def _potentially_splittable_level(self, text: str, split_level: int) -> Optional[int]:
    """
    Returns the first level (starting at split_level) at which 'text'
    is potentially splittable. Returns None if no such level exists.
    """
    if split_level >= len(self.splitter_patterns):
      return None

    lines = text.splitlines()
    for level in range(split_level, len(self.splitter_patterns)):
      pattern = self.splitter_patterns[level]
      if any(pattern.match(line) for line in lines):
        return level

    return None

  def _split_recursive(self, text: str, split_level: int) -> Generator[str, None, None]:
    """
    If 'text' is larger than chunk_size, attempts to split via
    _split_by_markers(). If no split actually occurs, or if after
    splitting a sub-chunk is still too large, recursion continues.
    """
    if len(text) <= self.chunk_size:
      yield text
      return

    if split_level >= len(self.splitter_patterns):
      yield text
      return

    splittable_level = self._potentially_splittable_level(text, split_level)

    if splittable_level is None:
      yield text
      return

    split_level = splittable_level

    # Attempt a split
    sub_chunks = self._split_by_markers(text, self.splitter_patterns[split_level])

    # Go through each sub-chunk and yield it if it's small enough, otherwise
    # recurse further.
    for chunk in sub_chunks:
      if len(chunk) <= self.chunk_size:
        yield chunk
      else:
        # Recurse further if chunk is still too large
        yield from self._split_recursive(chunk, split_level + 1)

  def _split_by_markers(self, text: str, splitter_pattern: re.Pattern) -> Generator[str, None, None]:
    """
    Goes line by line. Splits when we encounter a heading or horizontal rule,
    except within code fences where splitting is suspended.

    Returns a list of sub-chunks. If only one sub-chunk is returned,
    that implies no split occurred.
    """
    lines = text.splitlines(keepends=True)
    buffer = []

    in_code_block = False
    fence_char = None

    for line in lines:
      # Check if this line starts or ends a code block
      fence_match = self.fence_pattern.match(line)
      if fence_match:
        if not in_code_block:
          # Entering a code block
          in_code_block = True
          fence_char = fence_match.group(1)
        else:
          # Possibly exiting the code block if fence matches
          if fence_char == fence_match.group(1):
            in_code_block = False
            fence_char = None
        # Always accumulate everything inside code fences
        buffer.append(line)
        continue

      # If we're inside a code block, accumulate without splitting
      if in_code_block:
        buffer.append(line)
        continue

      # Not in code block: check for splitter pattern
      splitter_match = splitter_pattern.match(line)
      if splitter_match:
        chunk_text = ''.join(buffer)
        if chunk_text.strip():
          yield chunk_text

        # Determine if current line is heading or HR
        heading_match = re.match(r"^(#{1,6})\s.*", line)
        if heading_match:
          # For a heading, include it in the next chunk
          buffer = [line]
        else:
          # For HR, skip the line entirely
          buffer = []
      else:
        # Normal line; just accumulate
        buffer.append(line)

    # End of file: append whatever is in buffer
    if buffer:
      remaining_text = ''.join(buffer)
      # Only add if it's not just an HR
      if not re.match(r"^\s*[-*_]{3,}\s*$", remaining_text.strip()):
        yield remaining_text

