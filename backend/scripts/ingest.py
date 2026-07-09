import argparse
import json
import logging

from app.infrastructure.ingestion.pipeline import run_ingestion

logging.basicConfig(level="INFO", format="%(asctime)s %(levelname)s %(name)s: %(message)s")
parser = argparse.ArgumentParser()
parser.add_argument("--full", action="store_true", help="Ignora el manifiesto y reindexa todo")
args = parser.parse_args()
print(json.dumps(run_ingestion(full=args.full), indent=2, ensure_ascii=False))
