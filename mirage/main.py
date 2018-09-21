import argparse
from datetime import datetime as DT
import logging
import os
import sys

def run_simulation(simfile,savefile):
    infile = file[0]
    outfile = files[1]
    from mirage.calculator import ResultCalculator
    from mirage.io import SimulationFileManager
    loader = SimulationFileManager()
    loader.open(infile)
    sim = loader.read()
    loader.close()
    calculator = ResultCalculator()
    engine = calculator.calculate(sim,name = outfile)
    return engine
    


if __name__ == "__main__":
    print("Program initialized.")
    print('____________________________ \n\n'+"Process ID = " + str(os.getpid())+'\n\n____________________________')
    starttime = DT.now()

    parser = argparse.ArgumentParser()
    parser.add_argument("--load",nargs='?', type=str, help='Follow with a .param file to load in as parameters.')
    parser.add_argument("--run",nargs='?', type=str, help='Follow with a .params infile and outdirectory to save data to.')
    parser.add_argument("--outfile", nargs='?', type=str, help='Results file name. If one is not supplied, the file will be saved in the current directory using the Simulation name as filename.')
    parser.add_argument("--log",nargs='+', type=str, help='File to dump logging info to. Defaults to a file named after the date and time the program was initialized.')
    parser.add_argument("-v","--visualize",action='store_true',help='Launch program in visualization perspective.')
    args = parser.parse_args()
    if args.log:
        logging.basicConfig(filename=args.log[0],level=logging.INFO)
    if args.run:
        simfile = args.run[0]
        savefile = args.outfile[0]
        run_simulation(simfile,savefile)
        endtime = DT.now()
    else:
        print("Did not specify a command.")