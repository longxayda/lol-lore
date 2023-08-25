import modules.scraping.utilities
import modules.ingestion.utilities
import modules.general.utilities
import modules.ingestion.constants
import contextlib
import os
import json
import typing as T

ROOT_DIRECTORY = modules.general.utilities.get_root_directory()
OUTPUT_DIRECTORY = ROOT_DIRECTORY + "/output/scraping"

JSON_DIRECTORY_PATH = OUTPUT_DIRECTORY + "/json"
HTML_DIRECTORY_PATH = OUTPUT_DIRECTORY + "/html"

DATA_PATH = JSON_DIRECTORY_PATH + "/info"

SCHEMAS = modules.ingestion.constants.SCHEMAS
MAPPINGS = modules.ingestion.constants.MAPPINGS


def ingest(input_chunk: tuple):
    output = {}
    success, failed = 0, 0
    with contextlib.ExitStack() as stack:
        for filename, filepath, db, table_name in input_chunk:
            db: modules.ingestion.utilities.Database = db
            file = json.load(stack.enter_context(open(filepath, "r", encoding="utf-8")))
            champ_data = modules.ingestion.utilities.preprocess(file)
            try:
                fields, values = [], []
                for key in champ_data:
                    fields.append(MAPPINGS[table_name][key])
                    values.append(champ_data[key])

                on_conflict_ref = set()
                for constraint in SCHEMAS[table_name]["constraints"]:
                    if constraint in ["unique"]:
                        on_conflict_ref.update(
                            SCHEMAS[table_name]["constraints"][constraint]["fields"]
                        )

                on_conflict = {
                    "ref": on_conflict_ref,
                    "update": {field: f"EXCLUDED.{field}" for field in fields},
                }

                db.insert(
                    table_name,
                    fields,
                    values,
                    on_conflict,
                )
                output[filename] = True
                success += 1
            except Exception as e:
                print(str(e))
                output[filename] = False
                failed += 1

    print("Processed", success + failed, f"({success} succeeded, {failed} failed)")
    return output


def run(from_scratch=False):
    precise_champ_data_path = DATA_PATH + "/%s/data.json"
    table_name = "info"
    db = modules.ingestion.utilities.Database(
        host=modules.ingestion.constants.DB_HOST,
        database=modules.ingestion.constants.DB_NAME,
        user=modules.ingestion.constants.DB_USER,
        password=modules.ingestion.constants.DB_PASSWORD,
    )
    if from_scratch:
        db.drop(table_name)
        db.create(
            table_name,
            SCHEMAS[table_name]["fields"],
            SCHEMAS[table_name]["constraints"],
        )

    input = tuple(
        (champ_name, precise_champ_data_path % champ_name, db, table_name)
        for champ_name in os.listdir(DATA_PATH)
        if "." not in champ_name
    )
    input_chunks = modules.general.utilities.split_chunks(input)
    output = {}
    for sub_output in modules.general.utilities.parallelize(
        input_chunks, ingest, idle_time=1
    ):
        output.update(sub_output)
    return output
