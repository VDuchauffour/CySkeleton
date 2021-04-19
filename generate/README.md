# CySkeleton-generate

Generates a skeleton of the `CvPythonExtensions` module from information obtained by the *CySkeleton-extract* mod.

## How to use

First, extract python data from BtS or your mod (see `../extract/README.md`). Alternatively, you can use the file `skeleton_bts.json` in this directory.

### Preprocessing

The skeleton produced by *CySkeleton-extract* is very simple, containing only basic types and docstrings for each function or member. However, the docstrings in BtS are fairly uniform and can thus be used to extract function signatures. This is what script `cyskeleton.preprocess` does (among other things). Depending on your operating system, type one of the following in your terminal console window, after switching to this directory (`generate`):

```
# Windows
.\preprocess.bat --config config_default.json -v3 skeleton_bts.json skeleton_bts_proc.json

# Linux
./preprocess.sh --config config_default.json -v3 skeleton_bts.json skeleton_bts_proc.json
```

`--config config_default.json` is optional, but recommended. It tells the script to override certain signatures that are missing or wrong in the DLL, and also to override certain types. You can supply your own config file (perhaps an edited `config_default.json`), if you want.

`-v3` is similarly optional. The number (0-3) controls how much extra information (e.g., failures to parse certain signatures) is printed.

The last two arguments are the input and output files. If you have previously run CySkeleton-extract on your own mod, you should obviously replace the input file, and probably should also rename the output file.

### Generating the skeleton

To generate the `CvPythonExtensions.py` file, simply run, e.g.,

```
# Windows
.\generate.bat skeleton_bts_proc.json out/bts/CyPythonExtensions.py

# Linux
./generate.sh skeleton_bts_proc.json out/bts/CyPythonExtensions.py
```

This produces a file `CyPythonExtensions.py` in the `out/bts` directory, which you can then add to your IDE (In PyCharm, for example, you can add `out/bts` as a project root and then designate it as a source folder.
