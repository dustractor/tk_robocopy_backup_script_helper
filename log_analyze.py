import pathlib,re,os,argparse

args = argparse.ArgumentParser()
args.add_argument("logfile",type=pathlib.Path)
ns = args.parse_args()

print("ns:",ns)

with open(ns.logfile,"r",encoding="UTF16") as f:
    fdata = f.readlines()

reportfilepath = ns.logfile.with_stem(ns.logfile.stem+"_report")

modified = list()
newer = list()
newfile = list()
newdir = list()

for ln in fdata:
    if re.match(r"^\s*Modified\s.*",ln):
        modified.append(ln.strip())
    elif re.match(r"^\s*Newer\s.*",ln):
        newer.append(ln.strip())
    elif re.match(r"^\s*New\sFile\s.*",ln):
        newfile.append(ln.strip())
    elif re.match(r"^\s*New\sDir\s.*",ln):
        newdir.append(ln.strip())

with open(reportfilepath,"w",encoding="UTF16") as f:
    f.write(os.linesep.join(modified))
    f.write(os.linesep.join(newer))
    f.write(os.linesep.join(newfile))
    f.write(os.linesep.join(newdir))

