import logging
from pathlib import Path

import arcpy
from Pix4dProject import Pix4dProject

logging.basicConfig(
    filename=r"D:\nr426\Final Project\pix4d_extension\pix4d\esri\raster_type\Pix4d\output.log", level=logging.DEBUG)
logging.info("Loaded p4d raster type")


class DataSourceType():
    File = 1
    Folder = 2
    RasterDataset = 128


class RasterTypeFactory:
    acquisitionDate_auxField = arcpy.Field()
    acquisitionDate_auxField.name = "AcquisitionDate"
    acquisitionDate_auxField.aliasName = "Acquisition Date"
    acquisitionDate_auxField.type = "Date"
    acquisitionDate_auxField.length = 50

    def getRasterTypesInfo(self):
        logging.info("Got raster type info")
        return [
            {
                "rasterTypeName": "Pix4d RGB",
                "productDefinitionName": "Pix4d RGB",
                "builderName": "Pix4dRasterBuilder",
                "crawlerName": "Pix4dRasterCrawler",
                "description": "Support for Pix4d RGB",
                "isRasterProduct": True,
                "dataSourceType": DataSourceType.File,
                "processingTemplates": [

                ],
                # "bandProperties": [
                #     },

                #     },
                #     },
                "fields": [self.acquisitionDate_auxField],
            },
        ]


def dbg(fmt, obj, **kwargs):
    logging.debug(fmt.format(obj=obj, **kwargs))

    return obj


class Pix4dRasterBuilder:
    def __init__(self, **kwargs) -> None:
        self.RasterTypeName = "Pix4d Raster Dataset"

        logging.info(f"Builder Kwargs: {kwargs}")

    def canOpen(self, datasetPath: str) -> bool:
        logging.info(f"Dataset Path: {datasetPath}")

        return True

    def build(self, item):
        logging.info(f"Item URI: {item}")

        path = item["path"]
        display_name = item["displayName"]
        group_name = item["groupName"]
        item["uriProperties"]

        p4d = Pix4dProject(path)

        tif = next(p4d.orthos()).as_posix()

        return dbg("Builder Output: {obj}", [{
            "raster": self.get_raster_properties(p4d),
            "itemURI": {
                "path": tif,
                "displayName": display_name,
                "groupName": group_name,
            },
            "spatialReference": p4d.coordinate_system().output.spatial_reference(),
            "keyProperties": {
                "bandProperties": self.get_band_properties(p4d),
                "AcquisitionDate": p4d.aquisition_date().strftime("%Y-%m-%d %H:%M:%S"),
            },

        }])

    def get_band_properties(self, prj):
        """Collect band properties from a .p4d project.

        https://github.com/Esri/raster-functions/wiki/KeyMetadata#raster-bands

        """
        return [
            {
                "BandName": band.name,
                "WavelengthMin": min(band.wavelengths()),
                "WavelengthMax": max(band.wavelengths()),
            }
            for band in prj.bands()
        ]
    
    def get_raster_properties(self, prj):
        if len(prj.groups()) == 1:
            return {
                "uri": next(prj.orthos()).as_posix(),
            }

        elif len(prj.groups()) == 5:
            return {
                "functionDataset": {
                    "rasterFunction": "pix4d_composite.rft.xml",
                    "rasterFunctionArguments": {
                        f"Raster{i}": raster.as_posix() for i, raster in enumerate(prj.orthos(), 1)
                    },

                },
            }


class Pix4dRasterCrawler:
    def __init__(self, **kwargs) -> None:
        logging.info(f"Crawler Kwargs: {kwargs}")

        self.paths = kwargs["paths"]
        self.recurse = kwargs["recurse"]
        self.filter = kwargs["filter"]
        self.raster_type_info = kwargs["rasterTypeInfo"]
        self.gen = self.generator()

    def build_from_path(self, prj: Path):
        return {
            "path": str(prj),
            "tag": "MS",
            "displayName": prj.name,
            "groupName": "grp",
            "productName": "p4d",
            "uriProperties": {},
        }

    def generator(self):
        logging.info(f"Crawler: generator started: {self.paths}")

        for path in self.paths:
            p = Path(path)

            logging.info(
                f"Crawler: Path info({p.suffix}-{p.is_dir()}-{list(p.glob('*.p4d'))})")

            # if not p.is_dir():

            # for prj in p.glob("*.p4d"):
            yield self.build_from_path(p)

    def next(self):
        try:
            logging.info("Crawler: Provided item")
            return next(self.gen)
        except StopIteration:
            logging.info("Crawler: Finished crawling")
            return None

