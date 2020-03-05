#!/usr/bin/python3

"""
This file is part of ToR Conversor.

    ToR Conversor is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Foobar is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Foobar.  If not, see <https://www.gnu.org/licenses/>.
"""

import argparse
from sys import exit
import csvh
import tor


HOME="España"
UNIV_COLUMN="Código VICERRECTORADO donde se han cursado los estudios:"

HOME = HOME.strip().upper()
UNIV_COLUMN = UNIV_COLUMN.strip()

def exportCSVToR(personalData, ToR, fileName):
    csv_data = []
    for d in personalData:
        csv_data.append([d, personalData[d]])
    csv_data.append([])
    idv = 1
    for d in ToR:
        csv_data.append(["Bloque:", idv])
        csv_data.append(["", "Asignatura Destino", "Créditos", "Nota Destino", "Sugerencia Origen", "Min. Origen", "Máx. Origen", "Min. Destino", "Máx. Destino", "Alias"])
        for subject in ToR[d][0]:
            csv_data.append([""] + subject)
        csv_data.append([])
        csv_data.append(["", "Asignatura Origen", "Créditos"])
        for subject in ToR[d][1]:
            csv_data.append([""] + subject)
        csv_data.append([])
        idv += 1

    csvh.exportRawCSVData(fileName, csv_data)


def readData(fileName, origin, destination):
    eq_data = csvh.importRawCSVData(fileName)

    data = {}
    for d in eq_data:
        d[0] = d[0].strip().upper()
        if str(d[0])[0] == "#":
            pass
        else:
            data[d[0]] = d[1:]

    r = data[destination]
    raw_destination = []
    for d in r:
        raw_destination.append(str(d))
    raw_origin = data[origin]
    return (raw_destination, raw_origin)

def readToR(fileName):
    ToR = csvh.importRawCSVData(fileName)

    subjectData = []
    readSubjects = False
    personalData = {}
    for d in ToR:
        d[0] = d[0].replace("\n"," ").replace("\r", " ").strip()
        if readSubjects:
            subjectData.append(d)
        else:
            if d[0] == "Asignatura":
                readSubjects = True
            elif (d[0] != "" and str(d[0])[0] == "#") or d[0] == "":
                pass
            else:
                personalData[d[0]] = str(d[1]).strip()

    return (personalData, subjectData)

parser = argparse.ArgumentParser(description='Convert track of records o students from CSV files.')
parser.add_argument('--data', type=str, required=True,
                    help='The path to the CSV file containing the equivalence table.')
parser.add_argument('--origin', type=str, required=False, default=HOME,
                    help='The CODE of the origin.')
parser.add_argument('--scores', '-s', type=str, required=True,
                    help='The path to the CSV file containing the Transcript of Records.')
parser.add_argument('--debug_output', '-dbg', type=str, required=False,
                    help='The path to the CSV output debug file.')
parser.add_argument('--template', '-t', type=str, required=True,
                    help='The path to the LaTeX template to generate the output document.')
parser.add_argument('--output', '-o', type=str, required=True,
                    help='The path to the CSV output suggested file.')

# parser.add_argument('--no-fixed-images', '-nfi', required=False,
#                     help="If set, ignore images of the folder 'fixed'.",
#                     action="store_true")
# parser.add_argument('--size', '--size', required=False, nargs='+',
#                     help="If set, scale input images and mask to that size (default is 1024 640).")


args = parser.parse_args()

# 1. Parse and prepare ToR data.
personalData, ToR = readToR(args.scores)
destination = personalData[UNIV_COLUMN].upper()
american, ToR = tor.parseToR(ToR)

# 2. Parse and prepare equivalences table.
raw_destination, raw_origin = readData(args.data, args.origin, destination)
x,aliasx,y,aliasy = tor.expandScores(raw_origin, raw_destination, american)

# 3. Expand the table to score suggestions for each destination subject
ToR = tor.extendToR(ToR, x, aliasx, y, aliasy, american)

# Generate debug information
if args.debug_output:
    exportCSVToR(personalData, ToR, args.debug_output)

# 4. Load the LaTeX document
f=open(args.template,"r",encoding='utf8')
text = f.read()
f.close()

for d in personalData:
    personalData[d] = personalData[d].replace("\\", "/").replace("_", "\_").replace("$", "\$")
    text = text.replace("[["+str(d)+"]]", personalData[d].upper())
    text = text.replace("{{"+str(d)+"}}", personalData[d])

# 5. Add the final calification:
table = ""
for block in ToR:
    table += "\\hline \\hline \n"
    maxCr = 0
    fail = -1
    score = 0
    n = len(ToR[block][0])
    for i in range(n):
        maxCr += ToR[block][0][i][1]
    for i in range(n):
        if ToR[block][0][i][3] < 5:
            fail = ToR[block][0][i][3]
            score = fail
            break
        else:
            score += ToR[block][0][i][3] * (ToR[block][0][i][1] / maxCr)
    for i in range(max(n, len(ToR[block][1]))):
        try:
            sOrig = ToR[block][1][i][0]
        except:
            sOrig = ""
        try:
            sDst = ToR[block][0][i][0]
        except:
            sDst = ""
        try:
            crOrig = ToR[block][1][i][1]
        except:
            crOrig = ""
        try:
            crDst = ToR[block][0][i][1]
        except:
            crDst = ""
        try:
            scoreDst = ToR[block][0][i][2]
        except:
            scoreDst = ""

        score = float("{:.1f}".format(score))
        if score < 0:
            crLabel = "NO PRESENTADO"
        elif score < 5:
            crLabel = "(SUSPENSO)"
        elif score < 7:
            crLabel = "(APROBADO)"
        elif score < 9:
            crLabel = "(NOTABLE)"
        elif score < 9.5:
            crLabel = "(SOBRESALIENTE)"
        else:
            crLabel = "(MATRÍCULA)"

        if score < 0 and sOrig != "":
            table += " {} & {} &  & {} & {} & {} &  & {} \\\\ \\hline \n".format(sDst, crDst, scoreDst, sOrig, crOrig, crLabel)
        elif sOrig == "":
            table += " {} & {} &  & {} & {} & {} &  & \\\\ \\hline \n".format(sDst, crDst, scoreDst, sOrig, crOrig)
        else:
            table += " {} & {} &  & {} & {} & {} &  & {:.1f} {} \\\\ \\hline \n".format(sDst, crDst, scoreDst, sOrig, crOrig, score, crLabel)

text = text.replace("{{:SUBJECT-LIST:}}", table)

f=open(args.output,"w")
f.write(text)
f.close()






#print()
