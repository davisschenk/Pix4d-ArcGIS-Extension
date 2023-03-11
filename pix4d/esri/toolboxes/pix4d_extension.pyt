# -*- coding: utf-8 -*-
# https://pro.arcgis.com/en/pro-app/latest/arcpy/geoprocessing_and_python/a-template-for-python-toolboxes.htm
import arcpy
# from raster_type.Pix4d.Pix4dProject import Pix4dProject

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


def convert_bool(t):
    return t == "true"

@dataclass
class Index:
    name: str
    formula: str
    enabled: bool

    @classmethod
    def from_xml(cls, index):
        return cls(
            name=index.get("name"),
            formula=index.get("formula"),
            enabled=convert_bool(index.get("enabled"))
        )
    
    @classmethod
    def from_prj(cls, root):
        return [
            cls.from_xml(idx) 
            for idx in root.findall("./options/index/indices/index")
        ]



@dataclass
class Band:
    name: str
    central_wavelength: int
    width: int

    @classmethod
    def from_xml(cls, band):
        return cls(
            name=band.get("name"),
            central_wavelength=int(band.get("centralWaveLength")),
            width=int(band.get("width"))
        )

    @classmethod
    def from_prj(cls, root):
        return [
            cls.from_xml(band)
            for band in root.findall(".//camera/band")
        ]

    def wavelengths(self):
        return (self.central_wavelength - self.width, self.central_wavelength + self.width)


@dataclass
class Camera:
    name: str
    id: int
    band: Band

    @classmethod
    def from_prj(cls, root):
        return [
            cls(
                name=cam.get("name"),
                id=cam.find("id").text,
                band=Band.from_xml(cam.find("band"))
            )
            for cam in root.findall("./inputs/cameras/camera")
        ]

@dataclass
class Projection:
    wkt: str
    geoid_model: str
    geoid_name: str

    @classmethod
    def from_xml(cls, prj):
        vert = prj.find("verticalDef")
        
        return cls(
            wkt=prj.find("WKT").text,
            geoid_model=vert.get("model"),
            geoid_name=vert.get("geoidName")
        )

    def spatial_reference(self):
        return arcpy.SpatialReference(text=self.wkt)

@dataclass
class CoordinateSystem:
    southing_westing: bool
    output: Projection
    gcp: Projection
    image: Projection

    @classmethod
    def from_prj(cls, root):
        cs = root.find("./inputs/coordinateSystems")
        return cls(
            southing_westing=convert_bool(cs.find("southingWesting").text),
            output=Projection.from_xml(cs.find("output")),
            gcp=Projection.from_xml(cs.find("gcp")),
            image=Projection.from_xml(cs.find("image"))
        )

@dataclass
class Image:
    path: str
    group: str
    time: datetime
    altitude: float
    latitude: float
    longitude: float
    yaw: float
    pitch: float
    roll: float

    @classmethod
    def from_xml(cls, image):
        gps = image.find("gps")
        ori = image.find("ori") or  {"yaw": -1, "pitch": -1, "roll": -1}

        return cls(
            path=image.get("path"),
            group=image.get("group"),
            time=datetime.strptime(image.find("time").text, "%Y:%m:%d %H:%M:%S"),
            altitude=float(gps.get("alt")),
            latitude=float(gps.get("lat")),
            longitude=float(gps.get("lng")),
            yaw=float(ori.get("yaw")),
            pitch=float(ori.get("pitch")),
            roll =float(ori.get("roll"))
        )
    
    @classmethod
    def from_proj(cls, root):
        images = root.findall("./inputs/images/image")

        return [cls.from_xml(img) for img in images]
    

class Pix4dProject:
    def __init__(self, path) -> None:
        self.tree = ET.parse(path)
        self.root = self.tree.getroot()
        self.path = Path(path)
        self.dire = self.path.with_suffix("")
        self.name = self.dire.name

    def cameras(self):
        return Camera.from_prj(self.root) 
    
    def indicies(self):
        return Index.from_prj(self.root)
    
    def coordinate_system(self):
        return CoordinateSystem.from_prj(self.root)
    
    def images(self):
        return Image.from_proj(self.root)

    def dsm(self):
        return self.dire / "3_dsm_ortho" / "1_dsm" / f"{self.name}_dsm.tif"

    @staticmethod
    def _group_to_ident(name):
        return name.lower()

    def orthos(self, transparent=True):
        for group in self.groups():
            group = self._group_to_ident(group)
            file_name = [self.name]
            if transparent:
                file_name.append("transparent")
            
            file_name += ["mosaic", group]

            yield self.dire / "3_dsm_ortho" / "2_mosaic" / ("_".join(file_name) + ".tif")
    
    def reflectance(self, transparent=True):
        reflectance_d = self.dire / "4_index" / "reflectance"

        if not reflectance_d.exists():
            return []

        for group in self.groups():
            group = self._group_to_ident(group)
            file_name = [self.name]
            if transparent:
                file_name.append("transparent")
            
            file_name += ["reflectance", group]

            yield reflectance_d / ("_".join(file_name) + ".tif")
    
    def groups(self):
        return [b.name for b in self.bands()]

    def bands(self):
        return Band.from_prj(self.root)


class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Pix4d Toolbox"
        self.alias = "pix4d_toolbox"

        # List of tool classes associated with this toolbox
        self.tools = [CreatePixMosaic]


class CreatePixMosaic(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Create Mosaic Dataset from Pix4d File"
        self.description = ""
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""

        mosaic_name = arcpy.Parameter(
            displayName="Mosaic Database Name",
            name="mosaic_name",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
        )

        p4d_file = arcpy.Parameter(
            displayName="Pix4d Project File",
            name="p4d_file",
            datatype="DEFile",
            parameterType="Required",
            direction="Input"
        )

        # p4d_file.filter.type = "File"
        # p4d_file.filter.list = ["*.p4d"]
        
        return [mosaic_name, p4d_file]

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        
        mosaic_name = parameters[0].valueAsText
        p4d_file = parameters[1].valueAsText

        prj = Pix4dProject(p4d_file)

        arcpy.CreateMosaicDataset_management(
            arcpy.env.workspace,
            mosaic_name,
            prj.coordinate_system().output.spatial_reference(),
            len(prj.bands()),
            None,
            "CUSTOM",
            [(band.name,) + band.wavelengths() for band in prj.bands()]
        )

        return
    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return
