# CySkeleton

*CySkeleton* is a tool to produce a *skeleton* of the C++-generated python module `CvPythonExtensions` in Civilization IV: Beyond the sword, or any mod. A skeleton is a module that contains class, function, and member definitions and types without functionality. This makes it possible to use certain IDE features when editing python files of CivIV mods.

*CySkeleton* consists of two parts: *CySkeleton-extract*, a mod(comp) used to extract information on the `CvPythonExtensions` from the running game, and *CySkeleton-generate*, used to generate the skeleton from that information. See the directories `extract` and `generate` for more information on the two components.