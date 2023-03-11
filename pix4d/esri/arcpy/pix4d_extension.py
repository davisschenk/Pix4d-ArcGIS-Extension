# -*- coding: utf-8 -*-
r""""""
__all__ = ["Tool"]
__alias__ = "toolbox"
from arcpy.arcobjects.arcobjectconversion import convertArcObjectToPythonObject
from arcpy.geoprocessing._base import gp, gp_fixargs, gptooldoc


# Tools
@gptooldoc("Tool_toolbox", None)
def Tool():
    """Tool_toolbox()."""
    from arcpy.arcobjects.arcobjectconversion import convertArcObjectToPythonObject
    from arcpy.geoprocessing._base import gp, gp_fixargs
    try:
        retval = convertArcObjectToPythonObject(gp.Tool_toolbox(*gp_fixargs((), True)))
        return retval
    except Exception as e:
        raise e


# End of generated toolbox code
del gptooldoc, gp, gp_fixargs, convertArcObjectToPythonObject