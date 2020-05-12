import yaml
import os

_ONTOLOGY_FILE_PATH = os.getenv("ONTOLOGY_FILE_PATH")
_concepts = []
_examples = []


def get_concept_examples():
    return _examples


def get_concept_names():
    return _concepts


def _init_ontology():
    global _concepts
    global _examples
    print("Processing ontology.")
    ontology_yml = _read_ontology_yaml_file()
    _recursively_build_ontology(ontology_yml, "", _concepts, _examples)
    print("Finished processing ontology.")


def _recursively_build_ontology(ontology_yml, sofar, concept_names, examples):
    for component in ontology_yml:
        if "OntologyNode" in component.keys():
            current = "/" + component["name"] if sofar != "" else component["name"]
            concept_names.append(sofar + current)
            examples.append(component["examples"])
            continue

        component_name = list(component.keys())[0]
        current = "/" + component_name if sofar != "" else component_name

        _recursively_build_ontology(component[component_name], sofar + current, concept_names, examples)


def _read_ontology_yaml_file():
    ontology_yml = None
    with open(_ONTOLOGY_FILE_PATH, "r") as stream:
        try:
            ontology_yml = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
    return ontology_yml


_init_ontology()
