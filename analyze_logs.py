import argparse
import dataclasses

import numpy as np


parser = argparse.ArgumentParser()
parser.add_argument("-f", "--file", type=str,
                   required=True, nargs=1)


@dataclasses.dataclass
class Timing:
    name: str
    secs: float

def main():
    args = parser.parse_args()
    with open(args.file[0]) as f:
        lines = [l for l in f.readlines() if "Timeit" in l]
    timing_groups = {}
    for line in lines:
        _k, fname, elapsed_secs = line.split(" ")
        timing_groups.setdefault(fname, []).append(Timing(fname, float(elapsed_secs)))
    for fname, timings in timing_groups.items():
        print("=====================")
        print(f"Function: {fname}")
        print(f"Called:   {len(timings)}")
        timings_arr = np.array([t.secs for t in timings])
        print(f"Avg:      {timings_arr.mean()}")
        print(f"Stddev:   {timings_arr.std()}")




main()
