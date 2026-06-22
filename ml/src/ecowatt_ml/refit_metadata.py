from __future__ import annotations


# Official REFIT House 8 channel metadata. In NILMTK, meter 1 is the aggregate
# clamp and meters 2..10 correspond to Appliance1..Appliance9.
REFIT_HOUSE8_APPLIANCES = {
    "Appliance1": "fridge",
    "Appliance2": "freezer",
    "Appliance3": "washer_dryer",
    "Appliance4": "washing_machine",
    "Appliance5": "toaster",
    "Appliance6": "computer",
    "Appliance7": "television",
    "Appliance8": "microwave",
    "Appliance9": "kettle",
}

APPLIANCE_DISPLAY_NAMES_ES = {
    "standby": "Sin artefacto activo",
    "fridge": "Refrigeradora",
    "freezer": "Congeladora",
    "washer_dryer": "Lavaseca",
    "washing_machine": "Lavadora",
    "toaster": "Tostadora",
    "computer": "Computadora",
    "television": "Televisor",
    "microwave": "Microondas",
    "kettle": "Hervidor",
}

REFIT_HOUSE8_METADATA_SOURCE = (
    "NILMTK REFIT metadata: "
    "nilmtk/dataset_converters/refit/metadata/building8.yaml"
)


def appliance_display_name(appliance: str) -> str:
    return APPLIANCE_DISPLAY_NAMES_ES.get(
        appliance,
        appliance.replace("_", " ").strip().title(),
    )
