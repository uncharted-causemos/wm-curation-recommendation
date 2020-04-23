from services.elasticsearch_client import *

ontology_url = None # TODO: Read in url to ontology

es_service = new ElasticsearchService();
fe_service = new FactorEmbeddingService();
ontology_service = new OntologyService(ontology_url);
cluster_service = new ClusterService();

# Get ES Record curusor
# Iterate over all documents
# Use FactorEmbeddingService to compute vectors for each factor
# Insert documents

# For each concept
## Compute concept embedding
## Insert into concept collection

# Grab all vectors from ES
# Reduce using UMap (fit)
# Compute reduced values (transform)
# Update all docs with their respective reduced factor vectors, x,y using the bulk api

# For each concept
## Grab all 2d_factor_vectors for that concept
## Compute cluster ids
## Update cluster ids using bulk api






