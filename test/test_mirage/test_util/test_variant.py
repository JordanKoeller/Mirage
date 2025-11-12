from abc import ABC, abstractmethod
from datetime import datetime
from unittest import TestCase
from typing import List, Dict
from dataclasses import dataclass
import numpy as np

from astropy import units as u
from astropy.cosmology import Cosmology, WMAP7

from mirage.calc.reducers import LightCurvesReducer
from mirage.util import VariantDictify

class TestVariantDictify(TestCase):
    def testFromDict_singelVariantSuccess(self):
        dict_repr = {
            "Radius": ["${sub}", "uas"],
            "Resolution": [10, "1/uas"],
            "NumCurves": 10,
            "Seed": 12,
            "Name": "lightcurve",
            "Variants": [
                {
                    "LinspaceVariant": {
                        "Name": "sub",
                        "Start": 1,
                        "Stop": 10,
                        "NumPoints": 10,
                    },
                },
            ],
        }
        expected = [
            LightCurvesReducer(
                radius=s * u.uas,
                resolution=10 / u.uas,
                num_curves=10,
                seed=12,
                name="lightcurve",
            )
            for s in np.linspace(1, 10, 10, endpoint=True).tolist()
        ]
        actual = VariantDictify.from_dict(LightCurvesReducer, dict_repr)
        self.assertEqual(expected, actual.variants())

    def testFromDict_tagsMoveTogether(self):
        dict_repr = {
            "Radius": ["${radius}", "uas"],
            "Resolution": ["${resolution}", "1/uas"],
            "NumCurves": 10,
            "Seed": 12,
            "Name": "lightcurve",
            "Variants": [
                {
                    "LinspaceVariant": {
                        "Name": "radius",
                        "Tag": "tag",
                        "Start": 1,
                        "Stop": 10,
                        "NumPoints": 10,
                    },
                },
                {
                    "LinspaceVariant": {
                        "Name": "resolution",
                        "Tag": "tag",
                        "Start": 10,
                        "Stop": 100,
                        "NumPoints": 10,
                    },
                },
            ],
        }
        expected = [
            LightCurvesReducer(
                radius=s * u.uas,
                resolution=10 * s / u.uas,
                num_curves=10,
                seed=12,
                name="lightcurve",
            )
            for s in np.linspace(1, 10, 10, endpoint=True).tolist()
        ]
        actual = VariantDictify.from_dict(LightCurvesReducer, dict_repr)
        self.assertEqual(expected, actual.variants())

    def testFromDict_differentTagsMoveSeparately(self):
        dict_repr = {
            "Radius": ["${radius}", "uas"],
            "Resolution": "${resolution} 1/uas",
            "NumCurves": 10,
            "Seed": 12,
            "Name": "lightcurve",
            "Variants": [
                {
                    "LinspaceVariant": {
                        "Name": "radius",
                        "Start": 1,
                        "Stop": 10,
                        "NumPoints": 10,
                    },
                },
                {
                    "LinspaceVariant": {
                        "Name": "resolution",
                        "Start": 10,
                        "Stop": 100,
                        "NumPoints": 10,
                    },
                },
            ],
        }
        expected = []
        for res in np.linspace(10, 100, 10, endpoint=True):
            for rad in np.linspace(1, 10, 10, endpoint=True):
                expected.append(
                    LightCurvesReducer(
                        radius=rad * u.uas,
                        resolution=res / u.uas,
                        num_curves=10,
                        seed=12,
                        name="lightcurve",
                    )
                )
        actual = VariantDictify.from_dict(LightCurvesReducer, dict_repr)
        self.assertEqual(expected, actual.variants())

    def testFromDict_fixedEndBehavior(self):
        dict_repr = {
            "Radius": ["${radius}", "uas"],
            "Resolution": "${resolution} 1/uas",
            "NumCurves": 10,
            "Seed": 12,
            "Name": "lightcurve",
            "Variants": [
                {
                    "LinspaceVariant": {
                        "Name": "radius",
                        "Tag": "tag",
                        "Start": 0,
                        "Stop": 10,
                        "NumPoints": 5,
                        "EndBehavior": "FIXED",
                    },
                },
                {
                    "LinspaceVariant": {
                        "Name": "resolution",
                        "Tag": "tag",
                        "Start": 10,
                        "Stop": 100,
                        "NumPoints": 10,
                        "EndBehavior": "REPEAT",
                    },
                },
            ],
        }
        radii = [0, 2.5, 5.0, 7.5, 10, 10, 10, 10, 10, 10]
        resolutions = np.linspace(10, 100, 10, endpoint=True)
        expected = []
        for rad, res in zip(radii, resolutions.tolist()):
            expected.append(
                LightCurvesReducer(
                    radius=rad * u.uas,
                    resolution=res / u.uas,
                    num_curves=10,
                    seed=12,
                    name="lightcurve",
                )
            )
        actual = VariantDictify.from_dict(LightCurvesReducer, dict_repr)
        self.assertEqual(expected, actual.variants())

    def testFromDict_mirrorEndBehavior(self):
        dict_repr = {
            "Radius": ["${radius}", "uas"],
            "Resolution": "${resolution} 1/uas",
            "NumCurves": 10,
            "Seed": 12,
            "Name": "lightcurve",
            "Variants": [
                {
                    "LinspaceVariant": {
                        "Name": "radius",
                        "Tag": "tag",
                        "Start": 0,
                        "Stop": 10,
                        "NumPoints": 5,
                        "EndBehavior": "MIRROR",
                    },
                },
                {
                    "LinspaceVariant": {
                        "Name": "resolution",
                        "Tag": "tag",
                        "Start": 10,
                        "Stop": 100,
                        "NumPoints": 10,
                        "EndBehavior": "REPEAT",
                    },
                },
            ],
        }
        radii = [0, 2.5, 5.0, 7.5, 10, 7.5, 5.0, 2.5, 0, 2.5]
        resolutions = np.linspace(10, 100, 10, endpoint=True)
        expected = []
        for rad, res in zip(radii, resolutions.tolist()):
            expected.append(
                LightCurvesReducer(
                    radius=rad * u.uas,
                    resolution=res / u.uas,
                    num_curves=10,
                    seed=12,
                    name="lightcurve",
                )
            )
        actual = VariantDictify.from_dict(LightCurvesReducer, dict_repr)
        self.assertEqual(expected, actual.variants())

