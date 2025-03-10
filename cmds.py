# python #!
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
from reportlab.lib.utils import ImageReader
from numpy import *
from sympy.abc import _clash2
from sympy.core.alphabets import greeks
from sympy.parsing.latex import parse_latex

from rivtlib import tags
from rivtlib.units import *

tabulate.PRESERVE_WHITESPACE = True


class Cmd:
    """
        insert commands that format to utf8 or reSt

        || APPEND | rel. pth | num; nonum                      .pdf
        || IMG  | rel. pth | caption, scale, (**[_F]**)        .png, .jpg
        || IMG2  | rel. pth | c1, c2, s1, s2, (**[_F]**)       .png, .jpg
        || TEXT | rel. pth |  plain; rivt                      .txt
        || TABLE | rel. pth | col width, l;c;r                 .csv, .txt, .xls
    """

    def __init__(self,  folderD, labelD):
        """commands that format to utf and reSt

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
        """parse a tagged line

        Args:
            cmdS (_type_): _description_
            lineS (_type_): _description_

        Returns:
            utS: formatted utf string
        """

        cC = globals()['Cmd'](self.folderD, self.labelD)
        ccmdS = cmdS.lower()
        functag = getattr(cC, ccmdS)
        uS, rS = functag(pthS, parS)

        # print(f"{cmdS=}")
        # print(f"{pthS=}")
        # print(f"{parS=}")

        return uS, rS, self.folderD, self.labelD

    def append(self, pthS, parS):
        """_summary_
        """
        pass

    def table(self, pthS, parS):
        """insert table from csv, xlsx or reSt file

        """
        # print(f"{pthS=}")
        uS = rS = ""
        pthP = Path(pthS)                                  # path
        extS = pthP.suffix[1:]                             # file extension
        parL = parS.split(",")
        titleS = parL[0].strip()                           # title
        if titleS == "-":
            titleS = " "
        maxwI = int(parL[1].strip())                       # max col. width
        alnS = parL[2].strip()                             # col. alignment
        rowS = parL[3].strip()                                # read rows
        alignD = {"s": "", "d": "decimal",
                  "c": "center", "r": "right", "l": "left"}
        if parL[4].strip() == "_[T]":                      # table number
            tnumI = int(self.labelD["tableI"])
            fillS = str(tnumI).zfill(2)
            utitlnS = "\nTable " + fillS + " - "
            rtitlnS = "\n**Table " + fillS + " -** "
            self.labelD["tableI"] = tnumI + 1
        else:
            titlnS = " "
            rtitlnS = " "

        utlS = titlnS + titleS                             # file path
        rtlS = rtitlnS + titleS
        pthxP = Path(*Path(pthS).parts[-3:])
        pthxS = str(pthxP.as_posix())
        pS = " [file: " + pthxS + "]" + "\n\n"

        readL = []
        if extS == "csv":                                  # read csv file
            with open(pthP, "r") as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    # print(f"{row=}")
                    if row and row[0].startswith('#'):
                        continue
                    else:
                        readL.append(row)
        elif extS == "xlsx":                               # read xls file
            pDF1 = pd.read_excel(pthS, header=None)
            readL = pDF1.values.tolist()
        else:
            return

        sys.stdout.flush()
        old_stdout = sys.stdout
        output = StringIO()
        alignS = alignD[alnS]
        output.write(tabulate.tabulate(
            readL, tablefmt="rst", headers="firstrow",
            numalign="decimal", maxcolwidths=maxwI, stralign=alignS))
        uS = rS = output.getvalue()
        sys.stdout = old_stdout

        # utf
        uS = utlS + pS + uS + "\n"
        # rst2
        r2S = rtlS + pS + rS + "\n"
        # rst
        rS = rtlS + pS + rS + "\n"

        return uS, r2S

    def img(self, pthS, parS):
        """ insert image from file

        Args:
            pthS (str): relative file path
            parS (str): parameters

        Returns:
            uS (str): formatted utf string
            r2S (str): formatted rst2 string
            rS (str): formatted reSt string
        """
        print(f"{parS=}")
        print(f"{pthS=}")
        parL = parS.split(",")
        capS = parL[0].strip()
        if capS == "-":
            capS = " "
        scS = parL[1].strip()
        figS = "Fig. "
        insP = Path(pthS)
        insS = str(insP.as_posix())
        pthxS = str(Path(*Path(self.folderD["rivP"]).parts[-1:]))
        pthxS = str(Path(insP, pthS))
        if parL[2].strip() == "_[F]":
            numS = str(self.labelD["figI"])
            self.labelD["fnum"] = int(numS) + 1
            figS = "Fig. " + numS
        else:
            figS = " "
        # utf
        uS = figS + capS + " [file: " + pthxS + " ] \n"
        # rst2
        r2S = ("\n\n.. image:: " + insS + "\n"
               + "   :width: " + scS + "% \n"
               + "   :align: center \n"
               + "   :caption: " + figS + capS + "\n"
               + "\n\n\n"
               )
        # rSt
        rS = ("\n\n.. image:: " + insS + "\n"
              + "   :width: " + scS + "% \n"
                + "   :align: center \n"
                + "   :caption: " + figS + capS + "\n"
                + "\n\n\n"
              )
        return uS, r2S

    def img2(self, pthS, parS):
        """ insert side by side images from files

        Args:
            pthS(str): relative file path
            parS(str): parameters

        Returns:
            uS(str): formatted utf string
            rS(str): formatted reSt string
        """
        # print(f"{parS=}")
        parL = parS.split(",")
        fileL = pthS.split(",")
        file1P = Path(fileL[0])
        file2P = Path(fileL[1])
        cap1S = parL[0].strip()
        cap2S = parL[1].strip()
        scale1S = parL[2].strip()
        scale2S = parL[3].strip()
        figS = "Fig. "
        if parL[2] == "_[F]":
            numS = str(self.labelD["fnum"])
            self.labelD["fnum"] = int(numS) + 1
            figS = figS + numS + cap1S
        try:
            img1 = Image.open(pthS)
            _display(img1)
        except:
            pass
        uS = "<" + cap1S + " : " + str(file1P) + "> \n"
        rS = ("\n.. image:: "
              + pthS + "\n"
              + "   :scale: "
              + scale1S + "%" + "\n"
              + "   :align: center"
              + "\n\n"
              )

        return uS, rS

    def text(self, pthS, parS):
        """insert text from file using block formats

        | text | file | type

        """

        # print(f"{pthS=}")
        uS = rS = ""
        pthP = Path(pthS)                                  # path
        extS = pthP.suffix[1:]                             # file extension
        parL = parS.split(",")
        typeS = parL[0].strip()                           # title
        pthxP = Path(*Path(pthS).parts[-3:])
        pthxS = str(pthxP.as_posix())
        pS = "\n [file: " + pthxS + "]" + "\n"

        with open(pthP, "r") as fileO:
            fileL = fileO.readlines()

        if typeS == "[[]]":
            blkC = tags.Tag()
            ubS, rb2S = blkC.blkplain(fileL, self.folderD, self.labelD)
        elif typeS == "[[S]]":
            blkC = tags.Tag()
            ubS, rb2S = blkC.blkspace(fileL, self.folderD, self.labelD)
        elif typeS == "[[C]]":
            blkC = tags.Tag()
            ubS, rb2S = blkC.blkcode(fileL, self.folderD, self.labelD)
        elif typeS == "[[L]]":
            blkC = tags.Tag()
            ubS, rb2S = blkC.blklatex(fileL, self.folderD, self.labelD)
        elif typeS == "[[O]]":
            blkC = tags.Tag()
            ubS, rb2S = blkC.blkital(fileL, self.folderD, self.labelD)
        elif typeS == "[[B]]":
            blkC = tags.Tag()
            ubS, rb2S = blkC.blkbold(fileL, self.folderD, self.labelD)
        elif typeS == "[[I]]":
            blkC = tags.Tag()
            ubS, rb2S = blkC.blkitind(fileL, self.folderD, self.labelD)
        else:
            pass

        # utf
        uS = pS + ubS
        # rst2
        r2S = pS + rb2S
        # rst
        rS = pS + rb2S

        return uS, r2S
