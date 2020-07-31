import os
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
import sys

# Since the ingestor runs outside the scope of the app
# we need to add the root path of the app in order to have access to app packages
script_dir, script_path = os.path.split(os.path.abspath(sys.argv[0]))
app_root_path = Path(script_dir) / '../'
sys.path.insert(1, str(app_root_path.resolve()))

# Load env
load_dotenv(find_dotenv(), override=True)

from ingestor import process_kb
from ingestor import compute_umap
from ingestor import compute_clusters
from ingestor import es_setup
from helpers.es import es_recommendations_helper

# TODO: Read these in from args
kb_index_id = os.getenv('KB_INDEX_NAME')
delete_factor_reco_index_if_exists = os.getenv('DELETE_FACTOR_RECOMMENDATION_INDEX_IF_EXISTS')
delete_statement_reco_index_if_exists = os.getenv('DELETE_STATEMENT_RECOMMENDATION_INDEX_IF_EXISTS')
factor_reco_index_id = es_recommendations_helper.get_factor_recommendation_index_name(kb_index_id)
statement_reco_index_id = es_recommendations_helper.get_statement_recommendation_index_name(kb_index_id)


print("Processing entire KB into factor recommendations and statement recommendations...")
print("=================================================================================")
es_setup.setup_recommendation_indices(factor_reco_index_id,
                                      statement_reco_index_id,
                                      delete_factor_reco_index_if_exists,
                                      delete_statement_reco_index_if_exists)
process_kb.process(kb_index_id, factor_reco_index_id, statement_reco_index_id)
print("==========================================================================================")
print("Finished processing entire KB into factor recommendations and statement recommendations...")

# TODO: Confirm parameters are correct
print("Starting umap + hdbscan process for factor recommendations...")
print("========================================================")
compute_umap.compute_and_update(dim_start=300,
                                dim_end=20,
                                min_dist=0.01,
                                reco_index_id=factor_reco_index_id)
compute_clusters.compute_and_update(dim=20,
                                    min_cluster_size=15,
                                    min_samples=8,
                                    cluster_selection_epsilon=0.01,
                                    reco_index_id=factor_reco_index_id)
compute_umap.compute_and_update(dim_start=20,
                                dim_end=2,
                                min_dist=0.01,
                                reco_index_id=factor_reco_index_id)

print("======================================================")
print("Finished umap + hdbscan process for factor recommendations.")

print("Starting umap + hdbscan process for statement recommendations...")
print("===========================================================")
compute_umap.compute_and_update(dim_start=300,
                                dim_end=20,
                                min_dist=0.01,
                                reco_index_id=statement_reco_index_id)
compute_clusters.compute_and_update(dim=20,
                                    min_cluster_size=15,
                                    min_samples=8,
                                    cluster_selection_epsilon=0.01,
                                    reco_index_id=statement_reco_index_id)
compute_umap.compute_and_update(dim_start=20,
                                dim_end=2,
                                min_dist=0.01,
                                reco_index_id=statement_reco_index_id)
print("=========================================================")
print("Finished umap + hdbscan process for statement recommendations.")
