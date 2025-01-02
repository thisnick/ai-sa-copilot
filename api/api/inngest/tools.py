from hashlib import sha256

def get_sha256_hash(input_string: str) -> str:
  """
  Generate a SHA256 hash from an input string.

  Args:
    input_string: The string to be hashed

  Returns:
    str: The hexadecimal representation of the SHA256 hash
  """
  return sha256(input_string.encode('utf-8')).hexdigest()
