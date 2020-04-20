import yaml
import requests

class OntologyService:
    ontology_file_path = '/data/wm_with_flattened_interventions_metadata.yml'
    concepts = []
    examples = []
    
    def __init__(self, ontology_file_url):
        ontology_file_path = download_ontology(ontology_file_url)
        ontology_yml = read_ontology_yaml_file(ontology_file_path)
        ontology = recursively_build_ontology(ontology_yml, '', concepts, examples)
        
    def download_ontology(ontology_file_url):
        # TODO: Download ontology file
    
    def recursively_build_ontology(ontology_yml, sofar, concept_names, examples):
        for component in ontology_yml:
            if 'OntologyNode' in component.keys():
                concept_names.append(sofar + '/' + component['name'])
                examples.append(component['examples'])
                continue

            
            component_name = list(component.keys())[0]

            recursively_build_concepts(component[component_name], sofar + '/' + component_name, concept_names, examples)

    def read_ontology_yaml_file():
        ontology_yml = None
        with open(ontology_file_path, 'r') as stream:
            try:
                ontology_yml = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)
        return ontology_yml