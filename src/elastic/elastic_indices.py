def _recommendation_indices(name, kb_id):
    return f'curation-{name}-{kb_id}'


def get_concept_index_id(kb_id):
    return _recommendation_indices('concept', kb_id)


def get_factor_recommendation_index_id(kb_id):
    return _recommendation_indices('factor', kb_id)


def get_statement_recommendation_index_id(kb_id):
    return _recommendation_indices('statement', kb_id)
