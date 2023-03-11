import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import arcpy
import pandas as pd


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
            enabled=convert_bool(index.get("enabled")),
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
            width=int(band.get("width")),
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
                band=Band.from_xml(cam.find("band")),
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
            geoid_name=vert.get("geoidName"),
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
            image=Projection.from_xml(cs.find("image")),
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
            roll =float(ori.get("roll")),
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
        k = {}

        for i in self.images():
            if i.group not in k:
                k[i.group] = None

        return list(k.keys())

    def bands(self):
        return Band.from_prj(self.root)
    
    def aquisition_date(self):
        """Find an approximate aquisition time, remove any possible outliers caused by GPS issues (lack of a lock)."""
        times = pd.Series([i.time for i in self.images()])
        threshold = times.mean() - times.std() * 3
        return times[times > threshold][0]




if __name__ == "__main__":

    projects = [
        r"D:\nr426\Final Project\Data\050722-Easten-Julesburg-RGB-40M3MS.p4d",
        r"D:\nr426\Final Project\Data\Julesburg Thermal\050622-Easten-Julesburg-Thermal-40M3MS.p4d",
        r"D:\nr426\Final Project\Data\050622-Easten-Julesburg-Multi-40M3MS.p4d",
    ]

    for project in projects:
        p = Pix4dProject(project)

        print(p.aquisition_date())
