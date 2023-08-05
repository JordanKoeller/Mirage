import re
from hurry.filesize import size, alternative
from typing import Union


CONVERSION_STRINGS = ["k", "m", "g", "t", "p", "x"]
UNIT_REGEX = re.compile(r"([0-9.]+) ?([kmgtpbxi]+)", re.IGNORECASE)


def size_to_bytes(size_string: str) -> int:
  """
  Converts a human-readabile data size to the equivalent number of bytes.

  For example, the string "1Kb" will be converted to 1024 (bytes)

  Raises:

    + ValueError() if `size` could not be converted to bytes
  """
  try:
    unit_match = UNIT_REGEX.match(size_string.lower())
    if unit_match is None:
      raise ValueError(
          f"String {size_string} did not match expected format " "'{number}{unit}'"
      )
    num_group, unit_group = unit_match.group(1, 2)  # type: ignore
    num, unit = float(num_group), unit_group[0]
  except Exception as e:
    raise ValueError(
        f"Could not convert string {size_string} to a number of bytes\n{e}"
    )
  power = CONVERSION_STRINGS.index(unit) + 1
  return num * 1024**power


def bytes_to_size(size_in_bytes: Union[float, int]) -> str:
  return size(int(size_in_bytes), system=alternative).replace(" ", "")
