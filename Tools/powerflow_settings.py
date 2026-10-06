# -------------------------------------------------------------------------------
# Name:        PowerFlow settings parser
# Purpose:     Loads data from excel and converts to desired XML/RDF serialisation
#
# Author:      kristjan.vilgo
#
# Created:     2022-06-24
# Copyright:   (c) kristjan.vilgo 2022
# Licence:     GPLv2
# -------------------------------------------------------------------------------
# Updated by polinaamalinina september/october 2026 to the current structure of the PowerFlowSettings.xlsx 

import pandas
import RDF_parser
import json
import uuid
import sys
import re
import openpyxl
from datetime import datetime

ID = "aaed01a1-fff7-49aa-a5f2-df07c05e16a9"
VERSION = "2"
NAME = "PowerFlowSettings"
DEFINITION = "List of commonly used Power Flow Settings"
ISSUED = datetime.utcnow().isoformat()
DIST_ID = str(uuid.uuid4())
INSTANCE_ID = str(uuid.uuid4())

setting_sets = [
    (4, 'IGM Creation Set', '6efbd4ac-fbbf-42f8-a498-8dc819735be5'),
    (6, 'IGM Validation Set', 'b768cbab-ceb2-4fdb-877a-cb3f6d4ad711'),
    (9, 'CGM set', '23573ff8-f567-48c6-ab93-3df92afb3c35'),
    (12, 'CGM Relaxed set', 'ef9e4df5-17e0-4b6f-af08-e119064152a3'),
    (15, 'Model Debug set', 'd4c45d75-8ac5-450d-ab24-d10f3155352a'),
]
enum_types = {
    'algorithmKind': 'PowerFlowAlgorithmKind',
    'flatStartInitialisationKind': 'FlatStartInitialisationKind',
    'slackDistributionKind': 'SlackDistributionKind',
    'excludeFromLimitCheck': 'LimitCheckExclusionKind',
    'shiftKind': 'PowerShiftKind',
}

def clean_text(value):
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value).replace("\u200b", "").replace("\ufeff", "")).strip()

def clean_text(value):
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value).replace("\u200b", "").replace("\ufeff", "")).strip()

def setting_values(attribute, raw):
    value = clean_text(raw)
    if not value:
        return []
    if attribute in enum_types:
        if value.startswith("["):
            # No default is specified: retain each listed alternative.
            values = list(dict.fromkeys(v.strip() for v in value.strip("[]").split(",")))
        else:
            values = [value.split("[", 1)[0].strip()]
        return [enum_types[attribute] + "." + v for v in values]
    value = value.split("[", 1)[0].strip()
    value = re.sub(r"^max\s+", "", value)
    value = re.sub(r"\s*(MW|Mvar|pu)$", "", value).strip().lower()
    return [value]


workbook = openpyxl.load_workbook(sys.argv[1], data_only=True)
sheet = workbook["PowerFlowCalculationSettings"]
settings = []
for column, name, mrid in setting_sets:
    column += 1  # Convert the zero-based column to Excel's one-based column.
    record = {
        "IdentifiedObject.mRID": mrid,
        "IdentifiedObject.name": name,
        "IdentifiedObject.description": clean_text(sheet.cell(2, column).value).split(" - ", 1)[1],
    }
    for row in range(4, sheet.max_row + 1):
        attribute = sheet.cell(row, 1).value
        if not attribute:
            continue
        attribute = attribute.split(" (old name", 1)[0]
        values = setting_values(attribute, sheet.cell(row, column).value)
        if values:
            record["PowerFlowSettings." + attribute] = values
    settings.append(record)

print("Workbook:", sys.argv[1])
print("E8 — IGM Creation activePowerTolerance:", sheet["E8"].value)
print("E19 — ratio-tap priority:", sheet["E19"].value)
print("E23 — switched-shunt priority:", sheet["E23"].value)
workbook.close()

table_data = pandas.DataFrame(settings)
table_data["ID"] = table_data["IdentifiedObject.mRID"]
table_data["ID"] = f"{NAME}/" + table_data["ID"]
table_data = table_data.set_index("ID")
table_data["type"] = f"http://cim.ucaiug.io/ns#{NAME}"
data = RDF_parser.tableview_to_triplet(table_data)
data["INSTANCE_ID"] = INSTANCE_ID

# Distribution part, needed for filename
header_list = [
                (DIST_ID, "Type", "Distribution", INSTANCE_ID),
                (DIST_ID, "label", "../GeneratedData/PowerFlowSettings.rdf", INSTANCE_ID),
                #(DIST_ID, "issued", ISSUED, INSTANCE_ID),
                (DIST_ID, "modified", ISSUED, INSTANCE_ID),
                (DIST_ID, "version", VERSION, INSTANCE_ID),

                # Concept scheme definition
                (NAME, "Type", "ConceptScheme", INSTANCE_ID),
                (NAME, "type", "http://www.w3.org/ns/dcat#Dataset", INSTANCE_ID),
                #(NAME, "issued", ISSUED, INSTANCE_ID),
                (NAME, "modified", ISSUED, INSTANCE_ID),
                (NAME, "version", VERSION, INSTANCE_ID),
                #(NAME, "label", NAME, INSTANCE_ID),
                (NAME, "prefLabel", NAME, INSTANCE_ID),
                (NAME, "identifier", ID, INSTANCE_ID),
                (NAME, "keyword", "PFS", INSTANCE_ID),
                (NAME, "definition", DEFINITION, INSTANCE_ID)
                ]

data = pandas.concat([pandas.DataFrame(header_list, columns=["ID", "KEY", "VALUE", "INSTANCE_ID"]), data])


def rename_and_append_key(data, original_key, new_key, original_value=None, new_value=None):

    if original_value:
        description = pandas.DataFrame(data.query(f"KEY == '{original_key}' and VALUE =='{original_value}'"))
        description["VALUE"] = new_value
    else:
        description = pandas.DataFrame(data.query(f"KEY == '{original_key}'"))

    description["KEY"] = new_key
    data = pandas.concat([data, description], ignore_index=True)
    return data

def add_key_and_value(data, type, key, value, id=None):

    if id:
        filter = data.query("ID == @id and KEY == 'Type' and VALUE == @type")

    else:
        filter = data.query("KEY == 'Type' and VALUE == @type")

    filter["KEY"] = key
    filter["VALUE"] = value

    data = pandas.concat([data, filter], ignore_index=True)
    return data


# Bring some original values under new keys to data
#data = rename_and_append_key(data, "EICCode_MarketDocument.long_Names.name", "altLabel")
#data = rename_and_append_key(data, "EICCode_MarketDocument.lastRequest_DateAndOrTime.date", "start.use")
data = rename_and_append_key(data, "IdentifiedObject.name", "prefLabel")
data = rename_and_append_key(data, "IdentifiedObject.description", "definition")
data = rename_and_append_key(data, "IdentifiedObject.mRID", "identifier")

# Add urn:uuid to identifier
data.update("urn:uuid:" + data.query("KEY == 'identifier'").VALUE)

data = rename_and_append_key(data, "type", "Type", original_value=f"http://cim.ucaiug.io/ns#{NAME}", new_value="Concept")

data = add_key_and_value(data, type="Concept", key="inScheme", value=NAME)
data = add_key_and_value(data, type="Concept", key="topConceptOf", value=NAME)


rdf_map = RDF_parser.load_export_conf(["conf_skos.json",
                                       "conf_dcat.json",
                                       "conf_cim100.json",
                                       "conf_eumd.json",
                                       "conf_rdf_rdfs.json"])

for definition in rdf_map.values():
    if isinstance(definition, dict):
        if definition.get("namespace") == "http://iec.ch/TC57/CIM100#":
            definition["namespace"] = "http://cim.ucaiug.io/ns#"

for key in table_data.columns:
    if key.startswith("PowerFlowSettings."):
        rdf_map[key] = {
            "namespace": "http://cim.ucaiug.io/ns#",
            "text": "",
        }
        if key.split(".", 1)[1] in enum_types:
            rdf_map[key]["attrib"] = {
                "attribute": "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource",
                "value_prefix": "http://cim.ucaiug.io/ns#",
            }

namespace_map = {
    "cim": "http://cim.ucaiug.io/ns#",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "dcat": "http://www.w3.org/ns/dcat#",
    "skos": "http://www.w3.org/2004/02/skos/core#",
    "at": "http://publications.europa.eu/ontology/authority/",
    "dcterms": "http://purl.org/dc/terms/",
    "eumd": "http://entsoe.eu/ns/Metadata-European#"
}

data = data.explode("VALUE", ignore_index=True).dropna(subset=["VALUE"])

# Export triplet to CGMES
data.export_to_cimxml(rdf_map=rdf_map,
                      namespace_map=namespace_map,
                      export_undefined=False,
                      export_type="xml_per_instance"
                      )