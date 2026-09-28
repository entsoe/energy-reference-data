from lxml import etree
from pathlib import Path
from rdflib import Graph
from os import path

publication_base_path = r"../docs"
def publish_item(data, name, relative_path="", base_path=publication_base_path):
    # Define all folder and path names
    item_path = Path(base_path).joinpath(Path(relative_path)).joinpath(Path(name))
    print(f"Publishing {item_path}")

    item_file_name = Path(name)

    item_file_path = item_path.parent.joinpath(item_file_name)
    item_index_path = item_path.joinpath(Path("index.html"))

    # Create path
    item_path.mkdir(parents=True, exist_ok=True)

    # Write index.html
    item_index_path.write_text(redirect_html_template.format(identifier=name))

    # Write .rdf data
    Path(f"{item_file_path}.rdf").write_bytes(etree.tostring(data, pretty_print=True))

    # Generate .jsonld data based on .rdf
    convert_rdfxml_to_jsonld(f"{item_file_path}.rdf", f"{item_file_path}.jsonld")

    # Generate .ttl data based on .rdf
    convert_rdfxml_to_turtle(f"{item_file_path}.rdf", f"{item_file_path}.ttl")


def clean_directory(path: str, excluded_files: set):
    path = Path(path)
    folders_to_delete = []
    for item in path.iterdir():
        if item.is_dir():
            folders_to_delete.append(item)
            clean_directory(item, excluded_files)
        elif item.is_file() and item.name not in excluded_files:
            item.unlink()
    for folder in  folders_to_delete:
        if not any(folder.iterdir()):
            folder.rmdir()

def convert_rdfxml_to_jsonld(source_path, destination_path):
    # Parse to graph
    graph = Graph()
    graph.parse(source_path, format='application/rdf+xml')

    # Extend context
    context = {f"@{key}": value for key, value in etree.parse(str(source_path)).getroot().nsmap.items()}
    #context["@language"] = "en"

    # Serialize rdflib graph to JSON-LD
    data = graph.serialize(format='json-ld', indent=4, context=context, sort_keys=False, use_native_types=True)

    # Write JSON-LD data to a file
    Path(destination_path).write_text(data)

def convert_rdfxml_to_turtle(source_path, destination_path):
    # Parse to graph
    graph = Graph()
    graph.parse(source_path, format='application/rdf+xml')

    # Serialize rdflib graph to JSON-LD
    data = graph.serialize(format='turtle')

    # Write JSON-LD data to a file
    Path(destination_path).write_text(data)



redirect_html_template = """
<!DOCTYPE html>
<html>
    <head>
        <link rel="alternate" type="application/rdf+xml" href="../{identifier}.rdf" title="RDF/XML" />
        <link rel="alternate" type="application/ld+json" href="../{identifier}.jsonld" title="JSON-LD" />
        <link rel="alternate" type="text/turtle" href="../{identifier}.ttl" title="Turtle" />
        <!-- Google tag (gtag.js) -->
        <script async src="https://www.googletagmanager.com/gtag/js?id=G-L1R5VF4NBS"></script>
        <script>
          window.dataLayer = window.dataLayer || [];
          function gtag(){{dataLayer.push(arguments);}}
          gtag('js', new Date());
        
          gtag('config', 'G-L1R5VF4NBS');
        </script>
    </head>    
    <body>
        <meta http-equiv = "refresh" content = "0; url = ../{identifier}.rdf" />
    </body>
</html>"""

frontpage_html_template = """
<!DOCTYPE html>
<html xmlns:dcat="http://www.w3.org/ns/dcat#" xmlns:skos="http://www.w3.org/2004/02/skos/core#" xmlns:dcterms="http://purl.org/dc/terms/">
  <head>
    <!-- Google tag (gtag.js) -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-L1R5VF4NBS"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){{dataLayer.push(arguments);}}
      gtag('js', new Date());
    
      gtag('config', 'G-L1R5VF4NBS');
    </script>
    
    <!-- Metadata Section -->
    <meta charset="UTF-8">
    <title>Energy Reference Data SKOS Concept Schemes</title>
    <meta name="description" content="This project aims to create common reference data for energy-related business processes using SKOS, DCAT, and CIM.">
    <meta name="keywords" content="reference data, energy, SKOS, DCAT, CIM, rdf, cim, dcat, skos, entso-e, codelists, EIC, CGMES, meter reading">
    <meta name="robots" content="index,follow">
    <meta name="dc.language" content="en">
    <meta name="dc.title" content="Energy Reference Data SKOS Concept Schemes">
    <meta name="dc.description" content="This project aims to create common reference data for energy-related business processes using SKOS, DCAT, and CIM.">
    <meta name="dc.subject" content="reference data, energy, SKOS, DCAT, CIM, rdf, cim, dcat, skos, entso-e, codelists, EIC, CGMES, meter reading">
    <style>
           body {{
        font-family: Arial, sans-serif;
        margin: 0;
        padding: 0;
        background-color: #fff;
        color: #000;
      }}
      header {{
        background-color: #000;
        color: #fff;
        padding: 20px;
        text-align: center;
        display: flex;
        justify-content: space-between;
        align-items: center;
      }}
      header a {{
        display: flex;
        align-items: center;
        color: #fff;
        text-decoration: none;
      }}
      header img {{
        height: 50px;
        margin-right: 10px;
      }}
      h1 {{
        margin: 0;
        font-size: 2em;
        font-weight: bold;
        text-transform: uppercase;
      }}
      main {{
        max-width: 1600px;
        margin: 0 auto;
        padding: 20px;
        line-height: 1.5;
      }}
      table {{
        border-collapse: collapse;
        width: 100%;
        margin-bottom: 20px;
      }}
      th, td {{
        border: 1px solid #ddd;
        padding: 8px;
        text-align: left;
      }}
      th {{
        background-color: #f2f2f2;
        font-weight: bold;
        text-transform: uppercase;
      }}
      a {{
        color: #000;
        text-decoration: none;
        font-weight: bold;
      }}
      a:hover {{
        color: #f00;
      }}
      .publication-column a {{
        font-size: smaller;
      }}
    </style>
  </head>
  <body>
    <header>
      <div></div>      
      <h1>Energy Reference Data</h1>
      <a href="https://github.com/Haigutus/Energy-Reference-Data" target="_blank">
        <img src="github-mark-white.svg" alt="GitHub Logo">
      </a>
    </header>
    <main>
      <table typeof="skos:ConceptScheme dcat:Dataset">
        <thead>
          <tr>
            <th property="skos:prefLabel">Label</th>
            <th property="skos:definition" lang="en">Definition</th>
            <th property="dcterms:modified">Modified</th>
            <th property="dcat:version">Version</th>            
            <th property="dcterms:identifier">Identifier</th>
            <th>Serialisation</th>
          </tr>
        </thead>
        <tbody>
          {}
          <!-- Add more rows for each concept scheme -->
        </tbody>
      </table>
    </main>
  </body>
</html>
"""

table_row_html_template = """
<tr typeof="skos:ConceptScheme dcat:Dataset">
    <td property="skos:prefLabel"><a href="{prefLabel}">{prefLabel}</a></td>
    <td property="skos:definition">{definition}</td>
    <td property="dcterms:modified">{modified}</td>
    <td property="dcat:version">{version}</td>
    <td property="dcterms:identifier">{identifier}</td> 
    <td id="publication-column">
        <a href="{prefLabel}.rdf">RDF/XML</a><br>
        <a href="{prefLabel}.jsonld">JSON-LD</a><br>
        <a href="{prefLabel}.ttl">Turtle</a>
    </td>      
</tr>
"""

concept_scheme_html_template = """
<!DOCTYPE html>
<html xmlns:dcat="http://www.w3.org/ns/dcat#" xmlns:skos="http://www.w3.org/2004/02/skos/core#" xmlns:dcterms="http://purl.org/dc/terms/">
  <head>
    <link rel="alternate" type="application/rdf+xml" href="../{identifier}.rdf" title="RDF/XML" />
    <link rel="alternate" type="application/ld+json" href="../{identifier}.jsonld" title="JSON-LD" />
    <link rel="alternate" type="text/turtle" href="../{identifier}.ttl" title="Turtle" />
  
    <!-- Google tag (gtag.js) -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-L1R5VF4NBS"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){{dataLayer.push(arguments);}}
      gtag('js', new Date());

      gtag('config', 'G-L1R5VF4NBS');
    </script>

    <!-- Metadata Section -->
    <meta charset="UTF-8">
    <title>{identifier} SKOS Concept Scheme</title>
    <meta name="description" content="This project aims to create common reference data for energy-related business processes using SKOS, DCAT, and CIM.">
    <meta name="keywords" content="reference data, energy, SKOS, DCAT, CIM, rdf, cim, dcat, skos, entso-e, codelists, EIC, CGMES, meter reading">
    <meta name="robots" content="index,follow">
    <meta name="dc.language" content="en">
    <meta name="dc.title" content="Energy Reference Data SKOS Concept Schemes">
    <meta name="dc.description" content="This project aims to create common reference data for energy-related business processes using SKOS, DCAT, and CIM.">
    <meta name="dc.subject" content="reference data, energy, SKOS, DCAT, CIM, rdf, cim, dcat, skos, entso-e, codelists, EIC, CGMES, meter reading">
    <style>
           body {{
        font-family: Arial, sans-serif;
        margin: 0;
        padding: 0;
        background-color: #fff;
        color: #000;
      }}
      header {{
        background-color: #000;
        color: #fff;
        padding: 20px;
        text-align: center;
        display: flex;
        justify-content: space-between;
        align-items: center;
      }}
      header a {{
        display: flex;
        align-items: center;
        color: #fff;
        text-decoration: none;
      }}
      header img {{
        height: 50px;
        margin-right: 10px;
      }}
      h1 {{
        margin: 0;
        font-size: 2em;
        font-weight: bold;
        text-transform: uppercase;
      }}
      main {{
        max-width: 1600px;
        margin: 0 auto;
        padding: 20px;
        line-height: 1.5;
      }}
      table {{
        border-collapse: collapse;
        width: 100%;
        margin-bottom: 20px;
      }}
      th, td {{
        border: 1px solid #ddd;
        padding: 8px;
        text-align: left;
      }}
      th {{
        background-color: #f2f2f2;
        font-weight: bold;
        text-transform: uppercase;
      }}
      a {{
        color: #000;
        text-decoration: none;
        font-weight: bold;
      }}
      a:hover {{
        color: #f00;
      }}
      .publication-column a {{
        font-size: smaller;
      }}
    </style>
  </head>
  <body>
    <header>
      <div></div>      
      <h1>Energy Reference Data</h1>
      <a href="https://github.com/Haigutus/Energy-Reference-Data" target="_blank">
        <img src="../github-mark-white.svg" alt="GitHub Logo">
      </a>
    </header>
    <main>
      <table>
        <thead>
          <tr typeof="skos:Concept">
            <th property="skos:prefLabel">Label</th>
            <th property="skos:definition" lang="en">Definition</th>           
            <th property="dcterms:identifier">Identifier</th>
            <th>Serialisation</th>
          </tr>
        </thead>
        <tbody>
          {concept_rows}
          <!-- Add more rows for each concept -->
        </tbody>
      </table>
    </main>
  </body>
</html>
"""

concept_table_row_html_template = """
<tr typeof="skos:Concept">
    <td property="skos:prefLabel><a href="{url}.rdf">{prefLabel}</a></td>
    <td property="skos:definition" lang="en">{definition}</td>
    <td property="dcterms:identifier">{identifier}</td> 
    <td id="publication-column">
        <a href="{url}.rdf">RDF/XML</a><br>
        <a href="{url}.jsonld">JSON-LD</a><br>
        <a href="{url}.ttl">Turtle</a>
    </td>      
</tr>
"""



data_to_publish = [
    "../GeneratedData/PowerFlowSettings.rdf",
    "../GeneratedData/BaseVoltage.rdf",
    "../GeneratedData/entsoe-codelist-StandardEicTypeList.rdf",
    "../GeneratedData/entsoe-codelist-StandardMarketProductTypeList.rdf",
    "../GeneratedData/entsoe-codelist-StandardReasonCodeTypeList.rdf",
    "../GeneratedData/entsoe-codelist-StandardRoleTypeList.rdf",
    "../GeneratedData/entsoe-codelist-StandardStatusTypeList.rdf",
    "../GeneratedData/Confidentiality.rdf",
    "../GeneratedData/FaultCauseType.rdf",
    "../GeneratedData/PropertyReference.rdf",
    "../GeneratedData/allocated-eic.rdf"
]

files_to_keep = {
    "CNAME",
    "github-mark-white.svg"
    ".nojekyll"
}

# TODO - add a conf file for data to be published
# TODO - add status to ConceptScheme and Concept so that official and unofficial lists can be differentiated

# Clean
clean_directory(publication_base_path, files_to_keep)
# Generate new content
frontpage_rows = ""
for item in data_to_publish:
    # Parse XML and find relevant elements
    parser = etree.XMLParser(remove_blank_text=True)
    data = etree.parse(item, parser=parser)
    concept_scheme = data.find("{*}ConceptScheme")
    concepts = data.iterfind("{*}Concept")

    # Extract metadata from ConceptScheme
    concept_scheme_metadata = {child.tag.split("}")[1]: child.text for child in concept_scheme.getchildren() if child.text != None}
    if not concept_scheme_metadata.get("version"):
        concept_scheme_metadata["version"] = "1"
    frontpage_rows += table_row_html_template.format(**concept_scheme_metadata)

    # Publish ConceptScheme
    publish_item(data, concept_scheme_metadata["prefLabel"])

    # Publish Concepts
    concept_rows = ""
    for concept in concepts:
        name = concept.attrib.values()[0].split("/")[-1]
        relative_path = concept_scheme_metadata["prefLabel"]

        # Wrap concept in RDF root element
        rdf_root = etree.Element('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}RDF', nsmap=concept.nsmap)
        rdf_root.append(concept)

        publish_item(rdf_root, name, relative_path)

        # Extract concept metadata
        concept_metadata = {child.tag.split("}")[1]: child.text for child in concept.getchildren() if child.text != None}

        concept_metadata["url"] = concept.attrib.values()[0]

        if len(concept_metadata.values()) == 0:
            print(f"ERROR - empty concept {concept.attrib}")
            continue

        if not concept_metadata.get("definition"):
            print(f"WARNING - Concept missing definition {concept_metadata}")
            concept_metadata["definition"] = ""

        if not concept_metadata.get("prefLabel"):
            print(f"WARNING - Concept missing prefLabel {concept_metadata}")
            concept_metadata["prefLabel"] = ""

        if not concept_metadata.get("identifier"):
            print(f"WARNING - Concept missing identifier {concept_metadata}")
            concept_metadata["identifier"] = ""

        concept_rows += concept_table_row_html_template.format(**concept_metadata)

    # Publish Concept Index
    print(f"Generating index fo {publication_base_path}/{relative_path}")
    Path(publication_base_path).joinpath(relative_path).joinpath("index.html").write_text(concept_scheme_html_template.format(concept_rows=concept_rows, identifier=concept_scheme_metadata["prefLabel"]))

print(f"Generating frontpage to {publication_base_path}")
Path(publication_base_path).joinpath("index.html").write_text(frontpage_html_template.format(frontpage_rows))
print("Done")

