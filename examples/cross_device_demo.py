"""Pull plasma current for a MAST shot via the FDP/toksearch stack.

Run: pixi run fdp run python examples/cross_device_demo.py
(device auto-detects to 'mast' since toksearch_mast is the only device
installed in this env).
"""

from toksearch import Pipeline
from toksearch_mast import MastSignal, setup_environment

setup_environment()

shots = [30421]
pipe = Pipeline(shots)
pipe.fetch("ip", MastSignal("summary/ip"))
pipe.keep(["ip"])

for rec in pipe.compute_serial():
    ip = rec["ip"]
    print(f"shot {rec['shot']}: ip {ip['data'].shape}, "
          f"units={ip.get('units', {}).get('data')}")
