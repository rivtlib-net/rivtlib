#! python
""" rivt API
The API is intialized with 

    import rivtlib.api as rv 

API Functions:

    rv.R(rS) - (Run) Execute shell scripts 
    rv.I(rS) - (Insert) Insert static text, math, images and tables
    rv.V(rS) - (Values) Evaluate values and equations 
    rv.T(rS) - (Tools) Execute Python functions and scripts 
    rv.X(rS) - (eXclude) Skip string processing 
    rv.W(rS) - (Write) Write formatted documents 
    rv.Q(rS) - (Quit) Exit rivt processing
    
where rS is a triple quoted utf-8 string. The rivtlib code base uses
variable types identified with the last letter of a variable name:

A = array
B = boolean
C = class instance
D = dictionary
F = float
I = integer
L = list
N = file name
P = path
S = string
"""

import __main__
from pathlib import Path
from datetime import datetime, time
from configparser import ConfigParser
import warnings
import os
import logging
import fnmatch
import sys
from rivtlib.units import *
from rivtlib import params, parse

# from rivtlib import write

global utfS, rstS, folderD, labelD, rivtD

curP = Path(os.getcwd())
rivP = curP
if __name__ == "rivtlib.api":
    rivtP = Path(__main__.__file__)
    rivN = rivtP.name
    if fnmatch.fnmatch(rivN, "r????-*.py"):
        rivtP = Path(rivP, rivN)
        folderD, labelD, rivtD = params.dicts(rivN, rivP, rivtP)
else:
    print(f"INFO     rivt file - {rivN}")
    print(f"INFO     The name must match 'rddss-filename.py' where")
    print(f"INFO     dd and ss are two digit integers")
    sys.exit()

# print(f"{rivtP=}")
# print(f"{curP=}")
# print(f"{rivN=}")
# print(f"{__name__=}")

# initialize strings, config, logging
rstS = utfS = xrstS = xutfS = """"""
timeS = datetime.now().strftime("%Y-%m-%d | %I:%M%p") + 2*"\n"
rstS += timeS
utfS += timeS
config = ConfigParser()
config.read(Path(folderD["projP"], "rivt-config.ini"))
headS = config.get('report', 'title')
footS = config.get('utf', 'foot1')
modnameS = __name__.split(".")[1]
# print(f"{modnameS=}")
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)-8s  " + modnameS +
    "   %(levelname)-8s %(message)s",
    datefmt="%m-%d %H:%M",
    filename=folderD["errlogP"],
    filemode="w",
)
warnings.filterwarnings("ignore")
# warnings.simplefilter(action="ignore", category=FutureWarning)


def rivt_parse(rS, tS):
    """parse and accumulate a rivt string

    Globals:
        utfS (str): accumulated utf text string 
        rstS (str): accumulated reSt text string
        labelD (dict): labels 
        folderD (dict): folders 
        rivtD (dict): values

    Args:
        rS (str): rivt string
        tS (str): section type is R,I,V,T,W or X

    Calls:
        RivtParse (class)
        parse_str (method)

    Returns:
        None
    """
    global utfS, rstS, folderD, labelD, rivtD

    rL = rS.split("\n")
    # print(rL)
    parseC = parse.RivtParse(tS)
    xutfS, xrstS, folderD, labelD, rivtD = parseC.parse_str(
        rL, folderD, labelD, rivtD)

    utfS += xutfS       # accumulate output strings
    rstS += xrstS

    return utfS, rstS


def R(rS):
    """ process Run string

    Args:
        rS (str): rivt string
    """
    global utfS, rstS, folderD, labelD, rivtD

    utfS, rstS = rivt_parse(rS, "R")


def I(rS):
    """ format Insert string

    Args:
        rS (str): rivt string
    """
    global utfS, rstS, folderD, labelD

    utfS, rstS = rivt_parse(rS, "I")


def V(rS):
    """ format Value string

    Args:
        rS (str): rivt string
    """
    global utfS, rstS, folderD, labelD, rivtD

    locals().update(rivtD)
    utfS, rstS = rivt_parse(rS, "V")
    rivtD.update(locals())


def T(rS):
    """ process Tools string

    Args:
        rS (str): rivt string
    """
    global utfS, rstS, folderD, labelD, rivtD

    locals().update(rivtD)
    utfS, rstS = rivt_parse("T", rS)
    rivtD.update(locals())


def W(rS):
    """ write output files

    Args:
        rS (str): rivt string
    """
    pass


def X(rS):
    """ skip rivt string - no processing

    Args:
        rS (str): rivt string
    """

    rL = rS.split("|")
    print("\n X func - section skipped: " + rL[0] + "\n")


def Q():
    with open(folderD["reportP"], 'w', encoding="utf-8") as file:
        file.write(utfS)
    print("<<<<< end rivtlib >>>>>")
    sys.exit()
