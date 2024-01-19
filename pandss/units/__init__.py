from pathlib import Path

import pint

here = Path(__file__)
ureg = pint.UnitRegistry()
ureg.load_definitions(here.parent / r"pandss_units.pint")

# Unpack so the pdss.units.Quantity object belongs to the correct registry
Quantity = ureg.Quantity

# Unpack common units so they are accessible as pandss.units.XXXX
# Time
day = ureg.days
month = ureg.month
year = ureg.year
# Flow
cfs = ureg.cfs
# Volume
taf = ureg.taf
af = ureg.af
# Salinity
umhos = ureg.umhos
cm = ureg.cm
# Unitless
percent = ureg.percent
undefined = ureg.undefined
logical = ureg.logical
