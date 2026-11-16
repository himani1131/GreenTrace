"""
energy.py - turns measured CPU time into energy (Wh) and carbon (g of CO2).

Nothing here is measured by a power meter. It is a model:
    energy (Wh)  = CPU seconds x power of one busy CPU core (W) / 3600
    carbon (g)   = energy (kWh) x grid intensity (g CO2 per kWh)

The numbers below are rough, typical values. Check them against a source such as
Ember or the IEA before you quote them in your report, and change them freely.
"""

# Power drawn by ONE busy CPU core, in watts.
HARDWARE_WATTS = {"laptop": 15, "server": 12, "mobile": 3}

# Grams of CO2 produced per kWh of electricity (yearly average of the region).
GRID_G_PER_KWH = {"india": 700, "us": 370, "eu": 250, "world": 480}


def estimate(cpu_seconds, hardware, region):
    """Returns (energy_wh, co2_g)."""
    watts = HARDWARE_WATTS.get(hardware, HARDWARE_WATTS["laptop"])
    grams_per_kwh = GRID_G_PER_KWH.get(region, GRID_G_PER_KWH["india"])
    energy_wh = watts * cpu_seconds / 3600
    co2_g = energy_wh / 1000 * grams_per_kwh
    return energy_wh, co2_g
