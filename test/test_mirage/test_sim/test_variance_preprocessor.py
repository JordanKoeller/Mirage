from unittest import TestCase

from mirage.sim.variance_preprocessor import Variance, EdgeBehavior, VariancePreprocessor

VALUES = [0.0, 0.5, 1.0, 2.0]


class TestVariance(TestCase):

  def test_fromString_fullString_success(self):
    string = "linspace(5, 10, 6) @my-tag REPEAT"

    variance = Variance.from_string(string, "default")

    self.assertEqual(variance.variance_string, string)
    self.assertEqual(variance.values, [5, 6, 7, 8, 9, 10])
    self.assertEqual(variance.tag, "my-tag")
    self.assertEqual(variance.edge_behavior, EdgeBehavior.REPEAT)

  def test_fromString_noEdgeBehavior_success(self):
    string = "linspace(5, 10, 6) @my-tag"

    variance = Variance.from_string(string, "default")

    self.assertEqual(variance.variance_string, string)
    self.assertEqual(variance.values, [5, 6, 7, 8, 9, 10])
    self.assertEqual(variance.tag, "my-tag")
    self.assertEqual(variance.edge_behavior, EdgeBehavior.FIXED_TAIL)

  def test_fromString_noTag_success(self):
    string = "linspace(5, 10, 6)"

    variance = Variance.from_string(string, "default")

    self.assertEqual(variance.variance_string, string)
    self.assertEqual(variance.values, [5, 6, 7, 8, 9, 10])
    self.assertEqual(variance.tag, "default")
    self.assertEqual(variance.edge_behavior, EdgeBehavior.FIXED_TAIL)

  def test_fromString_noTagWithEdgeBehavior_success(self):
    string = "linspace(5, 10, 6) REPEAT"

    variance = Variance.from_string(string, "default")

    self.assertEqual(variance.variance_string, string)
    self.assertEqual(variance.values, [5, 6, 7, 8, 9, 10])
    self.assertEqual(variance.tag, "default")
    self.assertEqual(variance.edge_behavior, EdgeBehavior.REPEAT)

  def test_fromString_withKeyPrefix_success(self):
    string = "some_key: linspace(5, 10, 6)"

    variance = Variance.from_string(string, "default")

    self.assertEqual(variance.variance_string, "linspace(5, 10, 6)")
    self.assertEqual(variance.values, [5, 6, 7, 8, 9, 10])
    self.assertEqual(variance.tag, "default")
    self.assertEqual(variance.edge_behavior, EdgeBehavior.FIXED_TAIL)

  def test_fromString_fullStringWithPrefix_success(self):
    string = "some_key: linspace(5, 10, 6) @my-tag REPEAT"

    variance = Variance.from_string(string, "default")

    self.assertEqual(variance.variance_string, "linspace(5, 10, 6) @my-tag REPEAT")
    self.assertEqual(variance.values, [5, 6, 7, 8, 9, 10])
    self.assertEqual(variance.tag, "my-tag")
    self.assertEqual(variance.edge_behavior, EdgeBehavior.REPEAT)


class TestEdgeBehavior(TestCase):

  def test_inRangeIndex_success(self):
    for behavior in [EdgeBehavior.FIXED_TAIL, EdgeBehavior.REPEAT, EdgeBehavior.MIRROR]:
      self.assertEqual(1.0, behavior.apply(2, VALUES))
      self.assertEqual(2.0, behavior.apply(3, VALUES))

  def test_fixedTail_success(self):
    self.assertEqual(EdgeBehavior.FIXED_TAIL.apply(200, VALUES), VALUES[-1])

  def test_repeat_success(self):
    self.assertEqual(EdgeBehavior.REPEAT.apply(5, VALUES), 0.5)

  def test_mirror_success(self):
    expected = [0, 0.5, 1, 2, 1, 0.5, 0, 0.5, 1, 2, 1, 0.5, 0, 0.5, 1, 2, 1, 0.5, 0]
    for i, e in enumerate(expected):
      self.assertEqual(EdgeBehavior.MIRROR.apply(i, VALUES), e, f"Failed on index {i}")


class TestVariancePreprocessor(TestCase):

  def test_generateVariantsValues_success(self):
    vp = VariancePreprocessor()

    testcases = [
      (2, 2),
      (3, 2),
      (2, 3),
    ]

    expected = [
      [[0, 0], [1, 0], [0, 1], [1, 1]],
      [[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0], [
        0, 0, 1], [1, 0, 1], [0, 1, 1], [1, 1, 1]],
      [[0, 0], [1, 0], [2, 0], [0, 1], [1, 1], [2, 1], [0, 2], [1, 2], [2, 2]]
    ]
    for testcase, expect in zip(testcases, expected):
      self.assertEqual(vp._generate_variants_values(
        *testcase), expect, f"On testcase {testcase}")

  def test_generateVariants_singleVariant_success(self):
    doc = """
      key:
        some_value: linspace(0, 12, 3)
        some_other_value: Not a linspace
      some_key:
        some_keys_some_value: 12"""
    preprocessor = VariancePreprocessor()

    versions = preprocessor.generate_variants(doc)

    expected = [
      doc.replace("linspace(0, 12, 3)", "0.0"),
      doc.replace("linspace(0, 12, 3)", "6.0"),
      doc.replace("linspace(0, 12, 3)", "12.0"),
    ]
    self.assertEqual(versions, expected)

  def test_generateVariants_multipleVariants_success(self):
    doc = """
      key:
        some_value: linspace(0, 12, 3) @first REPEAT
        some_other_value: Not a linspace
      some_key:
        some_keys_some_value: linspace(12, 24, 3) @second MIRROR
        another_first_key: linspace(20, 32, 2) @first"""
    preprocessor = VariancePreprocessor()

    versions = preprocessor.generate_variants(doc)

    expected = [
      doc.replace("linspace(0, 12, 3) @first REPEAT", "0.0")
         .replace("linspace(20, 32, 2) @first", "20.0")
         .replace("linspace(12, 24, 3) @second MIRROR", "12.0"),
      doc.replace("linspace(0, 12, 3) @first REPEAT", "6.0")
         .replace("linspace(20, 32, 2) @first", "32.0")
         .replace("linspace(12, 24, 3) @second MIRROR", "12.0"),
      doc.replace("linspace(0, 12, 3) @first REPEAT", "12.0")
         .replace("linspace(20, 32, 2) @first", "32.0")
         .replace("linspace(12, 24, 3) @second MIRROR", "12.0"),

      doc.replace("linspace(0, 12, 3) @first REPEAT", "0.0")
         .replace("linspace(20, 32, 2) @first", "20.0")
         .replace("linspace(12, 24, 3) @second MIRROR", "18.0"),
      doc.replace("linspace(0, 12, 3) @first REPEAT", "6.0")
         .replace("linspace(20, 32, 2) @first", "32.0")
         .replace("linspace(12, 24, 3) @second MIRROR", "18.0"),
      doc.replace("linspace(0, 12, 3) @first REPEAT", "12.0")
         .replace("linspace(20, 32, 2) @first", "32.0")
         .replace("linspace(12, 24, 3) @second MIRROR", "18.0"),

      doc.replace("linspace(0, 12, 3) @first REPEAT", "0.0")
         .replace("linspace(20, 32, 2) @first", "20.0")
         .replace("linspace(12, 24, 3) @second MIRROR", "24.0"),
      doc.replace("linspace(0, 12, 3) @first REPEAT", "6.0")
         .replace("linspace(20, 32, 2) @first", "32.0")
         .replace("linspace(12, 24, 3) @second MIRROR", "24.0"),
      doc.replace("linspace(0, 12, 3) @first REPEAT", "12.0")
         .replace("linspace(20, 32, 2) @first", "32.0")
         .replace("linspace(12, 24, 3) @second MIRROR", "24.0"),
    ]
    self.assertEqual(versions, expected)

  def test_generateVariants_untaggedVariantsProduceProduct_success(self):
    doc = """
      key:
        some_value: linspace(0, 12, 2)
        some_other_value: Not a linspace
      some_key:
        some_keys_some_value: linspace(15, 20, 2)"""
    preprocessor = VariancePreprocessor()

    versions = preprocessor.generate_variants(doc)

    expected = [
      doc.replace("linspace(0, 12, 2)", "0.0")
         .replace("linspace(15, 20, 2)", "15.0"),
      doc.replace("linspace(0, 12, 2)", "12.0")
         .replace("linspace(15, 20, 2)", "15.0"),

      doc.replace("linspace(0, 12, 2)", "0.0")
         .replace("linspace(15, 20, 2)", "20.0"),
      doc.replace("linspace(0, 12, 2)", "12.0")
         .replace("linspace(15, 20, 2)", "20.0"),
    ]
    self.assertEqual(versions, expected)
