import argparse
from datetime import datetime as DT
import logging
import os

def run_simulation(simfile,savefile):
    """
    Entry point function for running a simulation. Given a `.sim` file, computes the described simulation and saves the results to `savefile`.

    Arguments:

    * `simfile` (`str`): The file containing a specification of a simulation to compute. Should have a `.sim` extension.
    * `savefile` (`str`): The filename to save the result of the simulation to. If `savefile` does not have the proper extension, the proper extension (`.res`) will be appended on to `savefile`.

    .. seealso:: This method **does not** include any options for specifying the context that should be used to perform the computation. In order to learn how to choose a context, see |GettingStartedWithMirage|.

    .. warning:: If `savefile` already exists in the file system, this method will overwrite `savefile`!
    """
    from mirage.calculator import ResultCalculator
    from mirage.io import SimulationFileManager
    loader = SimulationFileManager()
    loader.open(simfile)
    sim = loader.read()
    loader.close()
    calculator = ResultCalculator()
    print("Input accepted. Starting computation.")
    print("_____________________________________\n\n")
    saver = calculator.calculate(sim,name = savefile)
    print("Done. All results saved to " + saver.filename)
    try:
        from mirage import lens_analysis as la
        return la.load(saver.filename)
    except:
        return 
    # return engine
    


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
    if args.log:
        logging.basicConfig(filename=args.log[0],level=logging.INFO)
    if args.run:
        simfile = args.run[0]
        savefile = args.outfile[0]
        run_simulation(simfile,savefile)
    else:
        print("Did not specify a command.")
