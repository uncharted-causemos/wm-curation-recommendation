
import time
import os
import argparse
import sys
import traceback

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, dir_path + '/../src')


if __name__ == '__main__':
    # Get CLI args
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--url", type=str,
                        help="URL where ES is hosted")
    parser.add_argument("-i", "--index", type=str,
                        help="Index name in ES to process")
    parser.add_argument("-f", "--factors", action="store_true",
                        help="Remove the factor index")
    parser.add_argument("-s", "--statements", action="store_true",
                        help="Remove the statements index")
    parser.add_argument("-c", "--concepts", action="store_true",
                        help="Remove the concepts index")
    parser.add_argument("-sc", "--scheme", type=str,
                        help="Scheme for host, https or http")
    parser.add_argument("-un", "--username", type=str, help="Username for ES host")
    parser.add_argument("-pw", "--password", type=str, help="Password for ES host")

    args = parser.parse_args()

    print(f'Debugging: {args.url}')

    # Exit if the user did not provide the correct inputs
    if not (args.url and args.index):
        parser.print_help()
        sys.exit(1)

    # Creating the ingestor
    try:
        from elastic.elastic import Elastic
        from ingest.ingestor import Ingestor
    except Exception as e:
        traceback.print_exc(e)
        sys.exit(1)

    start_time = time.time()

    # Create ES connection from args
    es_args = args.url.rsplit(':', 1)
    es_user = args.username
    es_pw = args.password
    es_scheme = args.scheme
    if es_user is None:
        es_user = ""
    if es_pw is None:
        es_pw = ""
    if es_scheme is None:
        es_scheme = "http"
    es = Elastic(es_args[0].strip(), es_args[1].strip(), http_auth=(es_user, es_pw), scheme=es_scheme, timeout=60)

    try:
        print(f'Generating recommendations for index: {args.index}')
        ingestor = Ingestor(
            es=es,
            kb_index=args.index,
            project_index=None,
            statement_ids=[],
            remove_factors=args.factors,
            remove_statements=args.statements,
            remove_concepts=args.concepts
        )
        ingestor.ingest()
    except Exception as e:
        traceback.print_exc(e)
        sys.exit(1)

    print(f'Finished generating recommendations for index: {args.index}')
    print(f'Ingesting took {time.time() - start_time} seconds.')
    sys.exit(0)
