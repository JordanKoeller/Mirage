"""
Preprocessor supporting variance generators in YAML.

Variances are used to generate multiple values in a YAML spec. A new YAML doc is made for
each value in the variance, resulting in a list of YAML documents that are returned
"""
from dataclasses import dataclass
from enum import Enum
from typing import List, Self
from abc import ABC, abstractmethod
import re

from astropy import units as u
import numpy as np


class EdgeBehavior(Enum):
  FIXED_TAIL = "FIXED_TAIL"
  REPEAT = "REPEAT"
  MIRROR = "MIRROR"

  def apply(self, index: int, values: list[float]) -> float:
    if index < len(values):
      return values[index]
    if self == EdgeBehavior.FIXED_TAIL:
      return values[-1]
    if self == EdgeBehavior.REPEAT:
      return values[index % len(values)]
    if self == EdgeBehavior.MIRROR:
      if len(values) < 3:
        return values[index % len(values)]
      tooth = values + values[1:-1][::-1]
      return tooth[index % len(tooth)]
    raise ValueError("Unreachable")


@dataclass(frozen=True)
class Variance:
  variance_string: str
  values: list[float]
  tag: str
  edge_behavior: EdgeBehavior

  @classmethod
  def from_string(cls, string_value: str, default_tag: str, edge_behavior=EdgeBehavior.FIXED_TAIL) -> 'Variance':
    for regex_exp, func in EXPR_REGEXES:
      full_regex = f"(({regex_exp})( (\\@([a-zA-Z\\-_]+))?( ?[A-Z_]+)?)?)"
      compiled = re.compile(full_regex)
      matches = compiled.search(string_value)
      if matches:
        groups = matches.groups()
        num_groups = len(groups)
        variance_supergroup = groups[1]
        variance_arguments = groups[2:-4]
        tag_group = groups[-2]
        edge_group = groups[-1]
        tag = tag_group.strip() if tag_group else default_tag
        edge = EdgeBehavior[edge_group.strip()] if edge_group else edge_behavior
        variance_string = matches[0]
        return Variance(variance_string,
                        list(func(variance_arguments)),
                        tag,
                        edge)
    raise ValueError(f"Variance of string '{string_value}' is invalid")

  def __len__(self) -> int:
    return len(self.values)

  def get_value(self, index: int) -> float:
    return self.edge_behavior.apply(index, self.values)


class VariancePreprocessor:

  def __init__(self, default_edge_behavior: EdgeBehavior = EdgeBehavior.FIXED_TAIL):
    self.default_edge_behavior = default_edge_behavior

  def generate_variants(self, yaml_document: str) -> list[str]:
    variances = self._get_all_variances(yaml_document)
    yaml_documents: list[str] = []

    all_variances: list[Variance] = []
    for sublist in variances.values():
      all_variances.extend(sublist)

    if all_variances:
      max_variance_length = max(len(v) for v in all_variances)
      return self._generate_all_documents(yaml_document, variances, max_variance_length)
    return [yaml_document]

  def _generate_all_documents(self, yaml_document: str, variances: dict[str, list[Variance]], values_length: int) -> list[str]:
    """
    Generates all yaml documents.

    Variances with the same tag increment concurrently.

    Variances with different tags produce the cartesian product of their values.

    This is the same problem as counting in some arbitrary base.

      Modeling it that way, this is a much easier problem to solve.

    """
    documents: list[str] = []

    permutations = self._generate_variants_values(len(variances), values_length)

    for permutation in permutations:
      documents.append(self._generate_document(yaml_document, permutation, variances))

    return documents

  def _generate_variants_values(self, num_tags: int, max_value: int) -> list[list[int]]:
    """
    Generates all possible values for each tag. For example, for 2 tags and a max value of

    [[0, 0], [0, 1], [0, 2], [1, 0], [1, 1], [1, 2], [2, 0], [2, 1], [2, 2]]

    The algorithm enumerates all combinations by incrementing a counter with base `max_value`
    and `num_tags` many places
    """
    num_permutations = max_value ** num_tags - 1

    permutations: list[list[int]] = [[0 for _ in range(num_tags)]]

    for _ in range(num_permutations):
      permutation = permutations[-1][:]  # copy last permutation created
      i = 0
      permutation[0] += 1
      while i < num_tags and permutation[i] == max_value:
        permutation[i + 1] += 1
        permutation[i] = 0
        i += 1
      permutations.append(permutation)

    return permutations

  def _generate_document(self, yaml_document: str, indices: list[int], variances: dict[str, list[Variance]]) -> str:
    sorted_tags = sorted(variances.keys())
    template = yaml_document
    for i, t in enumerate(sorted_tags):
      for variance_obj in variances[t]:
        template = template.replace(
          variance_obj.variance_string, str(variance_obj.get_value(indices[i])))
    return template

  def _get_all_variances(self, yaml_document: str) -> dict[str, list[Variance]]:
    variance_groups: dict[str, list[Variance]] = {}
    tag_seed = 0
    for line in yaml_document.splitlines():
      try:
        variance = Variance.from_string(
          line, f"zzzzzzzzz_MIRAGE_DEFAULT_TAG_{tag_seed}", self.default_edge_behavior)
        tag_seed += 1
        if variance.tag in variance_groups:
          variance_groups[variance.tag].append(variance)
        else:
          variance_groups[variance.tag] = [variance]
      except ValueError as e:  # No variance present. Do nothing.
        pass
    return variance_groups


EXPR_REGEXES = [
  (
    r"linspace\(([0-9.e\-]+), ?([0-9.e\-]+), ?([0-9]+)\)",
    lambda matches: np.linspace(
      float(matches[0]), float(matches[1]), int(matches[2]), endpoint=True)
  ),
  (
    r"logspace\(([0-9.e\-]+), ?([0-9.e\-]+), ?([0-9]+)\) ([\w]+)",
    lambda matches: np.logspace(
      float(matches[0]), float(matches[1]), int(matches[2]), endpoint=True)
  ),
]
