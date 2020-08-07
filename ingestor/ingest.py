import getopt
import os
import sys

from pathlib import Path
from dotenv import load_dotenv, find_dotenv


# Since the ingestor runs outside the scope of the app we need to add the root
# path of the app in order to have access to app packages
script_dir, script_path = os.path.split(os.path.abspath(sys.argv[0]))
app_root_path = Path(script_dir) / '../'
sys.path.insert(1, str(app_root_path.resolve()))

# Load env
load_dotenv(find_dotenv(), override=True)

# Usage statement
usage = """
    usage: python3 ingest.py [-f] [-s] [-i knoweldge base index]

    -i knowledge base index: the indra index id in ES we wish to calculate
    stats for
    -f: delete the factor recommendation index if it exists
    -s: delete the statements recommendation index if it exists
"""


# Helper function to return the values from the getopt
def get_param(params, param):
    filtered = list(filter(lambda x: x[0] == param, params))

    if not len(filtered):
        return None
    return filtered[0][1].strip() or True


if __name__ == '__main__':
    argv = sys.argv[1:]
    opts, args = getopt.getopt(argv, 'hfsi:')

    # Get the user provided arguments
    help = get_param(opts, "-h")
    if help:
        print(usage)
        sys.exit(1)

    index = get_param(opts, "-i")
    factors = get_param(opts, "-f")
    statements = get_param(opts, "-s")

    # Imports are weird...
    try:
        from ingestor import process_kb
        from ingestor import compute_umap
        from ingestor import compute_clusters
        from ingestor import es_setup
        from helpers.es import es_recommendations_helper
    except Exception:
        sys.exit(1)

    try:
        # Overwrite these if command line arguments are provided
        kb_index_id = index or os.getenv('KB_INDEX_NAME')
        delete_factor_reco_index_if_exists = factors or os.getenv('DELETE_FACTOR_RECOMMENDATION_INDEX_IF_EXISTS')
        delete_statement_reco_index_if_exists = statements or os.getenv('DELETE_STATEMENT_RECOMMENDATION_INDEX_IF_EXISTS')

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
    except Exception:
        sys.exit(1)

    sys.exit(0)
