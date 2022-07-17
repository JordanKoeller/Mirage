import argparse
import logging
import os

from mirage.util.Timing import StopWatch
    


if __name__ == "__main__":
    print("Program initialized.")
    print('____________________________ \n\n'+"Process ID = " + str(os.getpid())+'\n\n____________________________')
    parser = argparse.ArgumentParser()
    parser.add_argument("--load",nargs='?', type=str, help='Follow with a .param file to load in as parameters.')
    parser.add_argument("--run",nargs='?', type=str, help='Follow with a .params infile and outdirectory to save data to.')
    parser.add_argument("--outfile", nargs='?', type=str, help='Results file name. If one is not supplied, the file will be saved in the current directory using the Simulation name as filename.')
    parser.add_argument("--log",nargs='+', type=str, help='File to dump logging info to. Defaults to a file named after the date and time the program was initialized.')
    parser.add_argument("-v","--visualize",action='store_true',help='Launch program in visualization perspective.')
    args = parser.parse_args()
    print("With args", args)
    if args.log:
        logging.basicConfig(filename=args.log[0],level=logging.INFO)
    if args.run:
        from mirage import runSimulation
        runSimulation(args.run, args.outfile)
    else:
        print("Did not specify a command.")
