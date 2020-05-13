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
import process_concepts
import compute_and_update_umap
import compute_and_update_clusters
import es_setup

es_setup.setup_outgoing_kb_index()
es_setup.setup_concept_index()

process_factors.process()
process_concepts.process()
compute_and_update_umap.compute_and_update()
compute_and_update_clusters.compute_and_update()
