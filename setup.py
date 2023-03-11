
from pathlib import Path

from setuptools import setup
from setuptools.command.install import install


class CustomInstall(install):
    def run(self):
        import arcpy
        info = arcpy.GetInstallInfo()
        install_dir = Path(info["InstallDir"])
        _raster_types = install_dir / "Resources\Raster\Types"

        
        install.run(self)

setup(name="pix4d_extension", 
      version="1.0",
      author="Davis Schenkenberger",
      description=("Extension that provides tools for using Pix4D outputs with ArcGIS"),
      python_requires="~=3.3",
      cmdclass={"install": CustomInstall},
      packages=["pix4d"], 
      package_data={"pix4d":["esri/toolboxes/*",  
                  "esri/arcpy/*", "esri/help/gp/*",  
                  "esri/help/gp/toolboxes/*", "esri/help/gp/messages/*"], 
                  }, 
      )