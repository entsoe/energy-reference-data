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

import pandas
import RDF_parser
import json
import uuid
from datetime import datetime

ID = "aaed01a1-fff7-49aa-a5f2-df07c05e16a9"
VERSION = "1"
NAME = "PowerFlowSettings"
DEFINITION = "List of commonly used Power Flow Settings"
ISSUED = datetime.utcnow().isoformat()
DIST_ID = str(uuid.uuid4())
INSTANCE_ID = str(uuid.uuid4())

table_data = pandas.read_excel("Header and metadata list.xlsx", sheet_name="__PowerFlowSettings__", dtype=str)
table_data["ID"] = table_data["IdentifiedObject.mRID"]
table_data["ID"] = f"{NAME}/" + table_data["ID"]
table_data = table_data.set_index("ID")
table_data["type"] = f"http://iec.ch/TC57/CIM100#{NAME}"
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
    data = data.append(description, ignore_index=True)
    return data

def add_key_and_value(data, type, key, value, id=None):

    if id:
        filter = data.query("ID == @id and KEY == 'Type' and VALUE == @type")

    else:
        filter = data.query("KEY == 'Type' and VALUE == @type")

    filter["KEY"] = key
    filter["VALUE"] = value

    data = data.append(filter, ignore_index=True)
    return data




# Bring some original values under new keys to data
#data = rename_and_append_key(data, "EICCode_MarketDocument.long_Names.name", "altLabel")
#data = rename_and_append_key(data, "EICCode_MarketDocument.lastRequest_DateAndOrTime.date", "start.use")
data = rename_and_append_key(data, "IdentifiedObject.name", "prefLabel")
data = rename_and_append_key(data, "IdentifiedObject.description", "definition")
data = rename_and_append_key(data, "IdentifiedObject.mRID", "identifier")

# Add urn:uuid to identifier
data.update("urn:uuid:" + data.query("KEY == 'identifier'").VALUE)

data = rename_and_append_key(data, "type", "Type", original_value=f"http://iec.ch/TC57/CIM100#{NAME}", new_value="Concept")

data = add_key_and_value(data, type="Concept", key="inScheme", value=NAME)
data = add_key_and_value(data, type="Concept", key="topConceptOf", value=NAME)


rdf_map = RDF_parser.load_export_conf(["conf_skos.json",
                                       "conf_dcat.json",
                                       "conf_cim100.json",
                                       "conf_eumd.json",
                                       "conf_rdf_rdfs.json"])

namespace_map = {
    "cim": "http://iec.ch/TC57/CIM100#",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "dcat": "http://www.w3.org/ns/dcat#",
    "skos": "http://www.w3.org/2004/02/skos/core#",
    "at": "http://publications.europa.eu/ontology/authority/",
    "dcterms": "http://purl.org/dc/terms/",
    "eumd": "http://entsoe.eu/ns/Metadata-European#"
}

# Export triplet to CGMES
data.export_to_cimxml(rdf_map=rdf_map,
                      namespace_map=namespace_map,
                      export_undefined=False,
                      export_type="xml_per_instance"
                      )