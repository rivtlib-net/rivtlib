import fnmatch
import csv
import logging
import re
import sys
import warnings
from datetime import datetime, time
from io import StringIO
from pathlib import Path

import IPython
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy.linalg as la
import pandas as pd
import sympy as sp
import tabulate
from PIL import Image
from IPython.display import Image as _Image
from IPython.display import display as _display
from numpy import *
from sympy.abc import _clash2
from sympy.core.alphabets import greeks
from sympy.parsing.latex import parse_latex

from rivtlib import tags, cmds
from rivtlib.units import *

tabulate.PRESERVE_WHITESPACE = True


class CmdV:
    """ value commands format to utf8 or reSt

    Commands:
        a = 1+1 | unit | reference
        | VREAD | rel. pth |  dec1    
    """

    def __init__(self, folderD, labelD):
        """commands that format a utf doc

        Args:
            paramL (list): _description_
            labelD (dict): _description_
            folderD (dict): _description_
            localD (dict): _description_
        """

        self.folderD = folderD
        self.labelD = labelD
        errlogP = folderD["errlogP"]
        modnameS = __name__.split(".")[1]
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)-8s  " + modnameS +
            "   %(levelname)-8s %(message)s",
            datefmt="%m-%d %H:%M",
            filename=errlogP,
            filemode="w",
        )
        warnings.filterwarnings("ignore")

    def cmd_parse(self, cmdS, pthS, parS):
        """parse tagged line

        Args:
            cmdS (str): command
            pthS (str): path or equation string
            parS (str): command parameters

        Returns:
            utS: formatted utf string
        """

        cC = globals()['CmdV'](self.folderD, self.labelD)
        ccmdS = cmdS.lower()
        functag = getattr(cC, ccmdS)
        uS, rS = functag(pthS, parS)

        # print(f"{cmdS=}")
        # print(f"{pthS=}")
        # print(f"{parS=}")

        return uS, rS

    def valread(self, pthS, parS):
        """ import values from csv files

        Args:
            lineS (_type_): _description_
            labelD (_type_): _description_
            folderD (_type_): _description_
        Returns:
            _type_: _description_
        """
        pathP = Path(pthS)
        with open(pathP, "r") as csvfile:
            readL = list(csv.reader(csvfile))
        # print(f"{readL=}")
        tbL = []
        for vaL in readL:
            # print(f"{vL=}")
            if len(vaL[0].strip()) < 1:
                continue
            if "=" not in vaL[0]:
                continue
            cmdS = vaL[0].strip()
            varS = vaL[0].split("=")[0].strip()
            valS = vaL[0].split("=")[1].strip()
            descripS = vaL[1].strip()
            unit1S, unit2S = vaL[2].strip(), vaL[3].strip()
            dec1I, dec2I = int(vaL[4]), int(vaL[5])
            loc = {"x": 1}
            loc[varS] = loc.pop('x')
            if unit1S != "-":
                if type(eval(valS)) == list:
                    val1U = array(eval(valS)) * eval(unit1S)
                    val2U = [q.cast_unit(eval(unit2S)) for q in val1U]
                else:
                    cmdS = vaL[0].strip()
                    # print(f"{cmdS=}")
                    try:
                        exec(cmdS, globals(), loc)
                    except ValueError as ve:
                        print(f"A ValueError occurred: {ve}")
                    except Exception as e:
                        print(f"An unexpected error occurred: {e}")
                    exec(cmdS)
                    valU = eval(varS, globals(), loc)
                    val1U = str(valU.cast_unit(eval(unit1S)))
                    val2U = str(valU.cast_unit(eval(unit2S)))
            else:
                cmdS = varS + " = " + valS
                exec(cmdS, globals(), locals())
                valU = eval(varS)
                val1U = str(valU)
                val2U = str(valU)
            tbL.append([varS, val1U, val2U, descripS])

        tblfmt = 'rst'
        hdrvL = ["variable", "value", "[value]", "description"]
        alignL = ["left", "right", "right", "left"]
        vC = CmdV(self.folderD, self.labelD)
        uS, rS = vC.valtable(tbL, hdrvL, alignL, tblfmt)

        return uS, rS

    def valwrite(self, pthS, parS):
        pass

    def valtable(self, tbL, hdrL, alignL, tblfmt):
        """ format table

        """
        # print(f"{tbL=}")
        sys.stdout.flush()
        old_stdout = sys.stdout
        output = StringIO()
        output.write(
            tabulate.tabulate(
                tbL, tablefmt=tblfmt, headers=hdrL,
                showindex=False,  colalign=alignL))
        uS = rS = output.getvalue()
        sys.stdout = old_stdout
        sys.stdout.flush()

        return uS, rS

    def valeq(self, eqS, parS):
        """format equation ' = '

        Args:
            lineS (_type_): _description_
            labelD (_type_): _description_
            folderD (_type_): _description_

        Returns:
            _type_: _description_
        """

        alignaL = ["left", "right", "right", "left"]
        hdreL = ["variable", "value", "[value]", "description [eq. number]"]
        aligneL = ["left", "right", "right", "left"]
        wI = self.labelD["widthI"]

        spS = eqS.strip()
        refS = parS.split("|")[0].strip()
        try:
            spL = spS.split("=")
            spS = "Eq(" + spL[0] + ",(" + spL[1] + "))"
            # sps = sp.encode('unicode-escape').decode()
        except:
            pass
        refS = refS.rjust(wI)
        lineS = sp.pretty(sp.sympify(spS, _clash2, evaluate=False))
        # utf
        uS = refS + "\n" + lineS + "\n\n"
        # rst
        rS = ".. raw:: math\n\n   " + lineS + "\n"

        return uS, rS

    def vsub(self, eqL, precI, varS, val1U):
        """substitute numbers for variables in formatted equations

        :return assignL: assign results
        :rtype: list
        :return rstS: restruct string
        :rtype: string
        """

        locals().update(self.localD)
        fmtS = "%." + str(precI) + "f"
        varL = [str(eqL[0]), str(eqL[1])]
        # resultS = vars[0].strip() + " = " + str(eval(vars[1]))
        # sps = sps.encode('unicode-escape').decode()
        eqS = "Eq(" + eqL[0] + ",(" + eqL[1] + "))"
        with sp.evaluate(False):
            symeq = sp.sympify(eqS.strip())
        # print(f"{symeq=}")
        symat = symeq.atoms(sp.Symbol)
        # print(f"{symat=}")
        for n1O in symat:
            if str(n1O) == varS:
                symeq = symeq.subs(n1O, sp.Symbol(str(val1U)))
                continue
            # print(f"{n1O=}")
            n1U = eval(str(n1O))
            n1U.set_format(value_format=fmtS, auto_norm=True)
            # print(f"{n1U=}")
            evlen = len(str(n1U))  # get var length
            new_var = str(n1U).rjust(evlen, "~")
            new_var = new_var.replace("_", "|")
            # print(f"{new_var=}")
            with sp.evaluate(False):
                symeq = symeq.subs(n1O, sp.Symbol(new_var))
            # print(f"{symeq=}")
        out2 = sp.pretty(symeq, wrap_line=False)
        out3 = out2  # clean up unicode
        out3 = out3.replace("*", "\\u22C5")
        _cnt = 0
        for _m in out3:
            if _m == "-":
                _cnt += 1
                continue
            else:
                if _cnt > 1:
                    out3 = out3.replace("-" * _cnt, "\u2014" * _cnt)
                _cnt = 0
        self.localD.update(locals())
        indeqS = out3.replace("\n", "\n   ")
        rstS = "\n::\n\n   " + indeqS + "\n\n"
        # mdS = out3 + "\n\n"


class TagV:
    """format to utf8 or reSt

    Functions:
            _[E]                    equation
            _[F]                    figure
            _[T]                    table
            _[A]                    page
            _[[V]]                  values
            _[[Q]]                  quit
    """

    def __init__(self,  folderD, labelD):
        """tags that format to utf and reSt

        """
        self.folderD = folderD
        self.labelD = labelD
        # print(folderD)
        errlogP = folderD["errlogP"]
        modnameS = __name__.split(".")[1]
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)-8s  " + modnameS +
            "   %(levelname)-8s %(message)s",
            datefmt="%m-%d %H:%M",
            filename=errlogP,
            filemode="w",
        )
        warnings.filterwarnings("ignore")

    def tag_parse(self, tagcmdS, blockL):
        """parse a tagged line

        Args:
            tagcmd (_type_): _description_
            lineS (_type_): _description_

        Returns:
            utS: formatted utf string
        """

        tC = TagV(self.folderD, self.labelD)
        tcmdS = str(tagcmdS)
        functag = getattr(tC, tcmdS)
        uS, rS = functag(blockL)

        # print(f"{tcmdS=}")
        return uS, rS

    def values(self, blockL):
        """return value table

        """

        vaL = []
        tbL = []
        # print(f"{blockL=}")
        for vaS in blockL:
            # print(f"{vaS=}")
            # print(tbL)
            vaL = vaS.split("|")
            # print(f"{vaL=}")
            if len(vaL) != 4 or len(vaL[0]) < 1:
                continue
            if "=" not in vaL[0]:
                continue
            cmdS = vaL[0].strip()
            varS = vaL[0].split("=")[0].strip()
            valS = vaL[0].split("=")[1].strip()
            descripS = vaL[1].strip()
            unitL = vaL[2].split(",")
            unit1S, unit2S = unitL[0], unitL[1]
            decL = vaL[3].split(",")
            dec1I, dec2I = decL[0], decL[1]
            loc = {"x": 1}
            loc[varS] = loc.pop('x')
            if unit1S != "-":
                if type(eval(valS)) == list:
                    val1U = array(eval(valS)) * eval(unit1S)
                    val2U = [q.cast_unit(eval(unit2S)) for q in val1U]
                else:
                    cmdS = vaL[0].strip()
                    # print(f"{cmdS=}")

                    try:
                        exec(cmdS, globals(), loc)
                    except ValueError as ve:
                        print(f"A ValueError occurred: {ve}")
                    except Exception as e:
                        print(f"An unexpected error occurred: {e}")
                    exec(cmdS)

                    # print(globals())
                    # print(loc)
                    valU = eval(varS, globals(), loc)
                    val1U = str(valU.cast_unit(eval(unit1S)))
                    val2U = str(valU.cast_unit(eval(unit2S)))
            else:
                cmdS = varS + " = " + valS
                exec(cmdS, globals(), locals())
                valU = eval(varS)
                val1U = str(valU)
                val2U = str(valU)
            tbL.append([varS, val1U, val2U, descripS])

        tblfmt = 'rst'
        hdrvL = ["variable", "value", "[value]", "description"]
        alignL = ["left", "right", "right", "left"]

        vC = CmdV(self.folderD, self.labelD)
        uS, rS = vC.valtable(tbL, hdrvL, alignL, tblfmt)

        return uS, rS
