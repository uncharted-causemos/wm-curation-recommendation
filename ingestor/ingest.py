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

from ingestor import process_kb
from ingestor import compute_umap
from ingestor import compute_clusters
from ingestor import es_setup

# FIXME: Read kb_index_name here in order to make it easier to move towarda an API endpoint

es_setup.setup_recommendation_index()
process_kb.process()

# TODO: Confirm parameters are correct
compute_umap.compute_and_update(dim_start=300, dim_end=20, min_dist=0.01, entity_type='factor')
compute_clusters.compute_and_update(dim=20, min_cluster_size=15, min_samples=8, cluster_selection_epsilon=0.01, entity_type='factor')
compute_umap.compute_and_update(dim_start=20, dim_end=2, min_dist=0.01, entity_type='factor')


# TODO: Confirm parameters are correct
compute_umap.compute_and_update(dim_start=300, dim_end=20, min_dist=0.01, entity_type='statement')
compute_clusters.compute_and_update(dim=20, min_cluster_size=15, min_samples=8, cluster_selection_epsilon=0.01, entity_type='statement')
compute_umap.compute_and_update(dim_start=20, dim_end=2, min_dist=0.01, entity_type='statement')
