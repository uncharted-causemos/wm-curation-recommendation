
class ConceptTextPreProcessor:
    @classmethod
    def clean(cls, concept):
        original_concept_nodes = concept.split('/')

        # Drop the first 2 slashes across the board
        cleaned_concept_nodes = original_concept_nodes[2:]

        # Filter out generic repeating words
        def filter_generic_nodes(node):
            if node == 'base_path':
                return False

            if node == 'event':
                return False

            if node == 'process':
                return False

            if node == 'property':
                return False

            if node == 'concept':
                return False

            if node == 'entity':
                return False

            return True

        cleaned_concept_nodes = list(filter(filter_generic_nodes, cleaned_concept_nodes))

        # Split words on underscores
        split_concept_nodes = []
        for n in cleaned_concept_nodes:
            split_concept_nodes.extend(n.split('_'))
        cleaned_concept_nodes = split_concept_nodes

        return ' '.join(cleaned_concept_nodes)
