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
load_dotenv(find_dotenv())

import process_factors
import compute_umap
import compute_clusters
import process_statements
import compute_statement_umap
import compute_statement_clusters
import es_setup
from services import es_service

# es_setup.setup_factor_index()
# process_factors.process()
# # TODO: Confirm parameters are correct
# compute_umap.compute_and_update(dim_start=300, dim_end=20, min_dist=0.01)
# compute_clusters.compute_and_update(dim=20, min_cluster_size=15, min_samples=8, cluster_selection_epsilon=0.01)
# compute_umap.compute_and_update(dim_start=20, dim_end=2, min_dist=0.01)


es_setup.setup_statement_index()
process_statements.process()
# TODO: Confirm parameters are correct
compute_statement_umap.compute_and_update(dim_start=300, dim_end=20, min_dist=0.01)
compute_statement_clusters.compute_and_update(dim=20, min_cluster_size=15, min_samples=8, cluster_selection_epsilon=0.01)
compute_statement_umap.compute_and_update(dim_start=20, dim_end=2, min_dist=0.01)
