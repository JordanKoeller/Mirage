{
  "name": "Test Simulation",
  "description": "This is a test.",
  "trial_count": 1,
  "variation": "",
  "parameters": {
    "lens": {
      "ellipticity": {
        "magnitude": {
          "values": 1.0,
          "unit": ""
        },
        "direction": 0.0
      },
      "shear": {
        "magnitude": {
          "values": 0.07,
          "unit": ""
        },
        "direction": 67.1
      },
      "velocity_dispersion": {
        "values": 177.95,
        "unit": "km / s"
      },
      "redshift": 0.04
    },
    "source": {
      "redshift": 1.69,
      "mass": {
        "values": 1000000000.0,
        "unit": "solMass"
      },
      "radius": {
        "values": 0.08,
        "unit": "uas"
      }
    },
    "ray_region": {
      "center": {
        "x": 1.4,
        "y": 1.4,
        "unit": "arcsec"
      },
      "dims": {
        "x": 0.0004166725631481171,
        "y": 0.00016666902525924683,
        "unit": "arcsec"
      },
      "resolution": {
        "x": 1000,
        "y": 1000,
        "unit": ""
      }
    },
    "star_generator": {
      "seed": 123,
      "mass_limits": [
        0.01,
        0.08,
        0.5,
        1.0,
        181.44000000000017
      ],
      "powers": [
        -0.3,
        -1.3,
        -2.3,
        -2.3
      ]
    },
    "percent_stars": 20.0,
    "source_plane": {
      "center": {
        "x": 0.0,
        "y": 0.0,
        "unit": "rad"
      },
      "dims": {
        "x": 6.733618638572807e-10,
        "y": 6.733618638572807e-10,
        "unit": "rad"
      }
    }
  },
  "results": {
    "magmap": {
      "magmap_resolution": {
        "x": 1000,
        "y": 1000,
        "unit": ""
      }
    },
    "lightcurves": {
      "seed": 123,
      "num_curves": 200,
      "sample_density": {
        "values": 10.0,
        "unit": "1 / uas"
      }
    }
  }
}