from pathlib import Path
from zipfile import ZipFile
from lxml import etree
import sys
import subprocess

if __package__:
    from .publish import (
        publish_item,
        concept_scheme_html_template,
        concept_table_row_html_template,
        frontpage_html_template,
        table_row_html_template,
    )
else:
    from publish import (
        publish_item,
        concept_scheme_html_template,
        concept_table_row_html_template,
        frontpage_html_template,
        table_row_html_template,
    )

PUBLISHED_CODELISTS = {
    "StandardEicTypeList",
    "StandardMarketProductTypeList",
    "StandardReasonCodeTypeList",
    "StandardRoleTypeList",
    "StandardStatusTypeList",
    }

def find_main_xsd(zip_file: ZipFile):
    xsd_files = [name for name in zip_file.namelist() if name.lower().endswith(".xsd")]

    for name in xsd_files:
        if name.endswith("urn-entsoe-eu-wgedi-codelists.xsd"):
            return name

    raise FileNotFoundError(
        "Could not find urn-entsoe-eu-wgedi-codelists.xsd in the ZIP package."
    )

def read_repository_version(repo_xsd_path: Path):
    if not repo_xsd_path.exists():
        return None, None, None

    tree = etree.parse(str(repo_xsd_path))

    version = tree.findtext(".//{*}Version")
    release = tree.findtext(".//{*}Release")
    release_date = tree.findtext(".//{*}ReleaseDate")

    return version, release, release_date

def read_codelist_metadata(zip_path: Path, preview_mode=False):
    with ZipFile(zip_path, "r") as zip_file:
        main_xsd = find_main_xsd(zip_file)

        with zip_file.open(main_xsd) as xsd_file:
            tree = etree.parse(xsd_file)

        version = tree.findtext(".//{*}Version")
        release = tree.findtext(".//{*}Release")
        release_date = tree.findtext(".//{*}ReleaseDate")

        if not version or not release or not release_date:
            raise ValueError(
                "Incoming Code List XSD is missing Version, Release, or ReleaseDate metadata."
        )

        print(f"Code List file : {main_xsd}")
        print(f"Version        : {version}")
        print(f"Release        : {release}")
        print(f"Release date   : {release_date}")

        repo_xsd_path = Path(__file__).parent / "urn-entsoe-eu-wgedi-codelists.xsd"
        
        repo_version, repo_release, repo_release_date = read_repository_version(
             repo_xsd_path
        )
        
        print("\nRepository version:")

        if repo_version is None:
            print("  No existing repository Code List XSD found.")
        else:
            print(f"  Version      : {repo_version}")
            print(f"  Release      : {repo_release}")
            print(f"  Release date : {repo_release_date}")

            try:
                incoming_version = (int(version), int(release))
                current_version = (int(repo_version), int(repo_release))   

                if incoming_version > current_version:
                    print("  Status       : NEWER VERSION")

                elif incoming_version == current_version:
                    print("  Status       : SAME VERSION")

                    if not preview_mode:
                        print("\nSTOP: Repository already contains this Code List version.")
                        return

                else:
                    print("  Status       : OLDER VERSION")
                    print("\nSTOP: Incoming Code List is older than the repository version.")
                    return

            except (TypeError, ValueError) as exc:
                raise ValueError(
                    "Could not compare incoming and repository Code List versions."
                ) from exc


        # Check XSD dependencies referenced by the main Code List XSD
        root = tree.getroot()

        dependencies = []

        for element in root.findall(".//{http://www.w3.org/2001/XMLSchema}include"):
            schema_location = element.get("schemaLocation")
            if schema_location:
                dependencies.append(schema_location)

        for element in root.findall(".//{http://www.w3.org/2001/XMLSchema}import"):
            schema_location = element.get("schemaLocation")
            if schema_location:
                dependencies.append(schema_location)

        print("\nXSD dependencies:")

        if not dependencies:
            print("  None found")
        else:
            zip_files = set(zip_file.namelist())
            main_directory = Path(main_xsd).parent

            for dependency in dependencies:
                dependency_path = (main_directory / dependency).as_posix()

                if dependency_path in zip_files:
                    print(f"  [OK] {dependency}")
                else:
                    print(f"  [MISSING] {dependency}")

        if preview_mode:
            preview_update_files(zip_file, main_xsd, tree)

        elif repo_version is not None:
            copy_update_files(zip_file, main_xsd, tree)
            run_codelist_generator()
            verify_generated_rdf(version, release_date)
            publish_codelists_only()
            rebuild_frontpage()
            verify_protected_files()
            report_publication_changes()
            print("\nREADY FOR REVIEW")

def verify_protected_files():
    docs_directory = Path(__file__).parent.parent / "docs"

    protected_files = [
        "CNAME",
        ".nojekyll",
        "github-mark-white.svg",
    ]

    print("\nChecking protected publication files...")

    missing_files = []

    for filename in protected_files:
        path = docs_directory / filename

        if path.exists():
            print(f"  [OK] {filename}")
        else:
            print(f"  [MISSING] {filename}")
            missing_files.append(filename)

    if missing_files:
        raise RuntimeError(
            "Protected publication files are missing: "
            + ", ".join(missing_files)
        )

    print("Protected publication files verified.")

def preview_update_files(zip_file: ZipFile, main_xsd: str, tree):
    root = tree.getroot()

    dependencies = []

    for element in root.findall(".//{http://www.w3.org/2001/XMLSchema}include"):
        schema_location = element.get("schemaLocation")
        if schema_location:
            dependencies.append(schema_location)

    for element in root.findall(".//{http://www.w3.org/2001/XMLSchema}import"):
        schema_location = element.get("schemaLocation")
        if schema_location:
            dependencies.append(schema_location)

    main_directory = Path(main_xsd).parent
    zip_files = set(zip_file.namelist())

    files_to_copy = [main_xsd]

    for dependency in dependencies:
        dependency_path = (main_directory / dependency).as_posix()

        if dependency_path not in zip_files:
            raise FileNotFoundError(
                f"Required XSD dependency is missing from ZIP: {dependency}"
            )

        files_to_copy.append(dependency_path)

    print("\nFiles that would be copied to Tools:")

    for source_file in files_to_copy:
        target = Path(__file__).parent / Path(source_file).name
        print(f"  {source_file}")
        print(f"    -> {target}")

    print("\nPREVIEW ONLY: No repository files were changed.")

def copy_update_files(zip_file: ZipFile, main_xsd: str, tree):
    root = tree.getroot()

    dependencies = []

    for element in root.findall(".//{http://www.w3.org/2001/XMLSchema}include"):
        schema_location = element.get("schemaLocation")
        if schema_location:
            dependencies.append(schema_location)

    for element in root.findall(".//{http://www.w3.org/2001/XMLSchema}import"):
        schema_location = element.get("schemaLocation")
        if schema_location:
            dependencies.append(schema_location)

    main_directory = Path(main_xsd).parent
    zip_files = set(zip_file.namelist())
    tools_directory = Path(__file__).parent

    files_to_copy = [main_xsd]

    for dependency in dependencies:
        dependency_path = (main_directory / dependency).as_posix()

        if dependency_path not in zip_files:
            raise FileNotFoundError(
                f"Required XSD dependency is missing from ZIP: {dependency}"
            )

        files_to_copy.append(dependency_path)

    for source_file in files_to_copy:
        target = tools_directory / Path(source_file).name

        with zip_file.open(source_file) as source:
            target.write_bytes(source.read())

        print(f"  [COPIED] {target.name}")

def run_codelist_generator():
    tools_directory = Path(__file__).parent
    generator_path = tools_directory / "entsoe_codelist.py"

    if not generator_path.exists():
        raise FileNotFoundError(
            f"Could not find Code List generator: {generator_path}"
        )

    print("\nRunning Code List generator...")

    result = subprocess.run(
        [sys.executable, str(generator_path)],
        cwd=tools_directory,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Code List generator failed with exit code {result.returncode}"
        )

    print("Code List generator completed successfully.")

def verify_generated_rdf(expected_version, expected_release_date):
    generated_directory = Path(__file__).parent.parent / "GeneratedData"

    rdf_files = list(
        generated_directory.glob("entsoe-codelist-*.rdf")
    )

    if not rdf_files:
        raise FileNotFoundError(
            "No generated Code List RDF files were found."
        )

    print("\nVerifying generated RDF metadata...")

    errors = []

    for rdf_file in rdf_files:
        tree = etree.parse(str(rdf_file))

        version = tree.findtext(".//{http://www.w3.org/ns/dcat#}version")
        modified = tree.findtext(
            ".//{http://purl.org/dc/terms/}modified"
        )

        if version != expected_version:
            errors.append(
                f"{rdf_file.name}: version is {version}, expected {expected_version}"
            )

        if modified != expected_release_date:
            errors.append(
                f"{rdf_file.name}: modified date is {modified}, "
                f"expected {expected_release_date}"
            )

    if errors:
        print("  [FAILED] Generated RDF metadata verification")

        for error in errors:
            print(f"    {error}")

        raise RuntimeError(
            "Generated RDF metadata does not match the incoming Code List."
        )

    print(f"  [OK] {len(rdf_files)} RDF files verified")
    print(f"  [OK] Version: {expected_version}")
    print(f"  [OK] Modified date: {expected_release_date}")

def publish_codelists_only():
    generated_directory = Path(__file__).parent.parent / "GeneratedData"
    docs_directory = Path(__file__).parent.parent / "docs"

    print("\nPublishing configured Code Lists only...")

    for codelist_name in sorted(PUBLISHED_CODELISTS):
        source_path = (
            generated_directory
            / f"entsoe-codelist-{codelist_name}.rdf"
        )

        if not source_path.exists():
            raise FileNotFoundError(
                f"Could not find generated Code List RDF: {source_path}"
            )

        parser = etree.XMLParser(remove_blank_text=True)
        data = etree.parse(str(source_path), parser=parser)

        concept_scheme = data.find("{*}ConceptScheme")
        concepts = data.iterfind("{*}Concept")

        concept_scheme_metadata = {
            child.tag.split("}")[1]: child.text
            for child in concept_scheme.getchildren()
            if child.text is not None
        }

        if not concept_scheme_metadata.get("version"):
            concept_scheme_metadata["version"] = "1"

        publish_item(
            data,
            concept_scheme_metadata["prefLabel"],
            base_path=docs_directory,
        )

        concept_rows = ""

        for concept in concepts:
            name = concept.attrib.values()[0].split("/")[-1]
            relative_path = concept_scheme_metadata["prefLabel"]

            rdf_root = etree.Element(
                "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}RDF",
                nsmap=concept.nsmap,
            )
            rdf_root.append(concept)

            publish_item(
                rdf_root,
                name,
                relative_path,
                base_path=docs_directory,
            )

            concept_metadata = {
                child.tag.split("}")[1]: child.text
                for child in concept.getchildren()
                if child.text is not None
            }

            concept_metadata["url"] = concept.attrib.values()[0]

            if not concept_metadata.get("definition"):
                concept_metadata["definition"] = ""

            if not concept_metadata.get("prefLabel"):
                concept_metadata["prefLabel"] = ""

            if not concept_metadata.get("identifier"):
                concept_metadata["identifier"] = ""

            concept_rows += concept_table_row_html_template.format(
                **concept_metadata
            )

        index_path = (
            docs_directory
            / relative_path
            / "index.html"
        )

        index_path.write_text(
            concept_scheme_html_template.format(
                concept_rows=concept_rows,
                identifier=concept_scheme_metadata["prefLabel"],
            )
        )

    print("Configured Code Lists published successfully.")

def rebuild_frontpage():
    generated_directory = Path(__file__).parent.parent / "GeneratedData"
    docs_directory = Path(__file__).parent.parent / "docs"

    data_to_publish = [
        generated_directory / "PowerFlowSettings.rdf",
        generated_directory / "BaseVoltage.rdf",
        generated_directory / "entsoe-codelist-StandardEicTypeList.rdf",
        generated_directory / "entsoe-codelist-StandardMarketProductTypeList.rdf",
        generated_directory / "entsoe-codelist-StandardReasonCodeTypeList.rdf",
        generated_directory / "entsoe-codelist-StandardRoleTypeList.rdf",
        generated_directory / "entsoe-codelist-StandardStatusTypeList.rdf",
        generated_directory / "Confidentiality.rdf",
        generated_directory / "FaultCauseType.rdf",
        generated_directory / "PropertyReference.rdf",
        generated_directory / "allocated-eic.rdf",
    ]

    print("\nRebuilding publication front page...")

    frontpage_rows = ""

    for item in data_to_publish:
        if not item.exists():
            raise FileNotFoundError(
                f"Could not find publication source: {item}"
            )

        parser = etree.XMLParser(remove_blank_text=True)
        data = etree.parse(str(item), parser=parser)

        concept_scheme = data.find("{*}ConceptScheme")

        if concept_scheme is None:
            raise ValueError(
                f"Could not find ConceptScheme in: {item}"
            )

        concept_scheme_metadata = {
            child.tag.split("}")[1]: child.text
            for child in concept_scheme.getchildren()
            if child.text is not None
        }

        if not concept_scheme_metadata.get("version"):
            concept_scheme_metadata["version"] = "1"

        frontpage_rows += table_row_html_template.format(
            **concept_scheme_metadata
        )

    frontpage_path = docs_directory / "index.html"

    frontpage_path.write_text(
        frontpage_html_template.format(frontpage_rows),
        encoding="utf-8",
    )

    print("Publication front page rebuilt successfully.")

def get_changed_doc_datasets():
    repo_root = Path(__file__).parent.parent

    paths_to_check = [
        "docs/BaseVoltage.jsonld",
        "docs/Confidentiality.jsonld",
        "docs/EIC.jsonld",
        "docs/EIC.rdf",
        "docs/EIC.ttl",
        "docs/FaultCauseType.jsonld",
        "docs/PowerFlowSettings.jsonld",
        "docs/PropertyReference.jsonld",
        "docs/StandardEicTypeList.jsonld",
        "docs/StandardMarketProductTypeList.jsonld",
        "docs/StandardReasonCodeTypeList.jsonld",
        "docs/StandardRoleTypeList.jsonld",
        "docs/StandardStatusTypeList.jsonld",
        "docs/index.html",
    ]

    result = subprocess.run(
        ["git", "diff", "--name-only", "--", *paths_to_check],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )

    changed_datasets = set()

    for line in result.stdout.splitlines():
        path = Path(line)

        if len(path.parts) < 2:
            continue

        name = path.parts[1]

        if name == "index.html":
            name = "index"
        elif "." in name:
            name = Path(name).stem

        changed_datasets.add(name)

    return changed_datasets

def classify_publication_changes():
    changed_datasets = get_changed_doc_datasets()

    expected_names = PUBLISHED_CODELISTS | {"index"}

    expected = changed_datasets & expected_names
    unexpected = changed_datasets - expected_names

    return expected, unexpected

def report_publication_changes():
    expected, unexpected = classify_publication_changes()

    print("\nPublication change check:")

    if expected:
        print("  Expected Code List changes:")
        for dataset in sorted(expected):
            print(f"    [OK] {dataset}")
    else:
        print("  Expected Code List changes: none")

    if unexpected:
        print("  Unrelated publication changes:")
        for dataset in sorted(unexpected):
            print(f"    [WARNING] {dataset}")
    else:
        print("  Unrelated publication changes: none")

def main():
    if len(sys.argv) not in (2, 3):
        print("Usage:")
        print("  python update_codelist.py <path-to-codelist-zip>")
        print("  python update_codelist.py <path-to-codelist-zip> --preview")
        sys.exit(1)

    if len(sys.argv) == 3 and sys.argv[2] != "--preview":
        print(f"ERROR: Unknown option: {sys.argv[2]}")
        print("Only --preview is supported.")
        sys.exit(1)

    zip_path = Path(sys.argv[1])
    preview_mode = len(sys.argv) == 3

    if not zip_path.exists():
        print(f"ERROR: File does not exist: {zip_path}")
        sys.exit(1)

    if zip_path.suffix.lower() != ".zip":
        print("ERROR: Input file must be a ZIP file.")
        sys.exit(1)

    try:
        read_codelist_metadata(zip_path, preview_mode)
    except Exception as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()