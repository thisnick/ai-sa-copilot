import pytest
from lib.text_splitter import HierarchicalMarkdownSplitter

def test_simple_text_split():
  text = "Hello world!"
  chunk_size = 5
  splitter = HierarchicalMarkdownSplitter(chunk_size)
  chunks = []

  for chunk in splitter.split(text):
    chunks.append(chunk)

  print(chunks)

  assert len(chunks) == 1
  assert chunks[0] == "Hello world!"

def test_headers():
  text = "# Header 1\nThis is some text.\n\n## Header 2\nMore text here."
  chunk_size = 10
  splitter = HierarchicalMarkdownSplitter(chunk_size)
  chunks = []

  for chunk in splitter.split(text):
    chunks.append(chunk)

  print(chunks)
  # We'll check that the headers are properly preserved in the chunks
  assert len(chunks) >= 2
  assert chunks[0].startswith("# Header 1\nThis")
  assert chunks[1].startswith("## Header 2\nMore")

def test_code_blocks():
  text = (
    "Here is some text\n"
    "```python\n"
    "print('Hello from code!')\n"
    "```\n"
    "Some more text."
  )
  chunk_size = 15
  splitter = HierarchicalMarkdownSplitter(chunk_size)
  chunks = []

  for chunk in splitter.split(text):
    chunks.append(chunk)

  # Ensure code block remains intact within a chunk
  assert any("```python\nprint('Hello from code!')\n```" in c for c in chunks)

def test_long_code_block():
  text = (
    "```python\n"
    + "x = 1\n" * 50
    + "```\n"
  )
  chunk_size = 40
  splitter = HierarchicalMarkdownSplitter(chunk_size)
  chunks = []

  for chunk in splitter.split(text):
    chunks.append(chunk)

  # Should split the code block into multiple sub-chunks, but keep fences
  # The first chunk should start with the opening fence
  assert chunks[0].startswith("```python")
  # The last chunk should end with the closing fence
  assert chunks[-1].endswith("```\n")

def test_mixed_content():
  text = (
    "# Header\n"
    "Some text here\n"
    "```bash\n"
    "echo 'Hello'\n"
    "# A comment\n"
    "# This should not be split\n"
    "```\n"
    "More text, plus a second header:\n"
    "## Another Header\n"
    "Even more text.\n"
  )
  chunk_size = 20
  splitter = HierarchicalMarkdownSplitter(chunk_size)
  chunks = []

  for chunk in splitter.split(text):
    chunks.append(chunk)

  assert len(chunks) == 2
  # Make sure multiple headers, code fences, etc. are preserved and split
  assert any(c.startswith("# Header\nSome") for c in chunks)
  assert any(c.startswith("## Another Header\nEven") for c in chunks)

def test_split_deeper_heading_level():
  text = (
    "# Header\n"
    "Some text here\n"
    "```bash\n"
    "echo 'Hello'\n"
    "# A comment\n"
    "# This should not be split\n"
    "```\n"
    "More text, plus a second header:\n"
    "#### Deeper Header\n"
    "Even more text.\n"
  )
  chunk_size = 20
  splitter = HierarchicalMarkdownSplitter(chunk_size)
  chunks = []

  for chunk in splitter.split(text):
    chunks.append(chunk)

  assert len(chunks) == 2
  # Make sure multiple headers, code fences, etc. are preserved and split
  assert any(c.startswith("# Header\nSome") for c in chunks)
  assert any(c.startswith("#### Deeper Header\nEven") for c in chunks)
