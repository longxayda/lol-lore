import modules.ingestion.functions

print("Let's ingest")

output = modules.ingestion.functions.run(True)

print(f"Ingested of {len([champ for champ in output if output[champ]])} champs")

print("Failed to ingest of these champs:")

for champ in output:
    if not output[champ]:
        print("\t-", champ)
