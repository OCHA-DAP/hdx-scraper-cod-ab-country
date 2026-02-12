import runpy
import subprocess
import sys

if sys.prefix == sys.base_prefix:
    sys.exit(subprocess.call(["uv", "run", __file__, *sys.argv[1:]]))

runpy.run_module("hdx.scraper.cod_ab_country", run_name="__main__")
