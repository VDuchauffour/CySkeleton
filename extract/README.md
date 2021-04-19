# CySkeleton-extract

A Mod with the single purpose of extracting information about available python functions and classes (specifically, the `CvPythonExtensions` module). Can be merged with any mod to capture newly exposed functions.

## How to use

### Setup

*CySkeleton-extract* consists of a single `Assets` folder. To extract vanilla BtS python information, you can simply create a new mod folder and put the supplied `Assets` folder into it. If you want to extract python information from your mod, you have to merge the supplied `Assets` folder with your mod. If your mod does not touch `Python/Entrypoints/CvEventInterface.py` (it usually will not be present in that case), you can simply copy the supplied `Assets` folder into your mod's directory. Otherwise, you have to merge your `CvEventInterface.py` with the supplied one. The only change in *CySkeleton-extract's* `CvEventInterface.py` are the following lines, which are easily copied into your `CvEventManager`, below the imports:

```python
# ExtractSkeleton 11/2020 lfgr START
import CvPythonExtensions
import extract_skeleton
extract_skeleton.extract_skeleton( CvPythonExtensions )
# ExtractSkeleton END
```

### Extraction

Simply start the mod (you don't need to start a new game, and can close the game immediately). The output is stored in the python log (for me it's in `C:\Users\...\Documents\My Games\Beyond the Sword\Logs\PythonDbg.log`. In that file, copy all the (many) lines between `Tree for CvPythonExtensions START` and `Tree for CvPythonExtensions END`. Store it in a JSON file (e.g. `skeleton_YOURMOD.json`) to further process it with *CySkeleton-Generate*.

Alternatively, you can use the `tools/retrieve_extract.py` script as follows.

```
# Windows
py tools\retrieve_extract.py

# Linux
./tools/retrieve_extract.py
```

This produces a file `skeleton.json`.