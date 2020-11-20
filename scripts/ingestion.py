import os
import argparse
import sys
import traceback

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, dir_path + '/../src')


def ingest(nlp, remove_factors, remove_statements):
    def _ingest(index, es):
        recommendations(index, nlp, remove_factors, remove_statements, es)
        return f'Successfully ingested {index}'
    return _ingest


if __name__ == '__main__':
    # Get CLI args
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--nlp", type=str,
                        default="../data/en_core_web_lg-2.2.5/en_core_web_lg/en_core_web_lg-2.2.5", help="NLP dir")
    parser.add_argument("-u", "--url", type=str,
                        help="URL where ES is hosted")
    parser.add_argument("-i", "--index", type=str,
                        help="Index name in ES to process")
    parser.add_argument("-f", "--factors", action="store_true",
                        help="Remove the factor index")
    parser.add_argument("-s", "--statements", action="store_true",
                        help="Remove the statements index")

    args = parser.parse_args()

    print(f'Debugging: {args.url}')

    # Exit if the user did not provide the correct inputs
    if not (args.url and args.index):
        parser.print_help()
        sys.exit(1)

    # Creating the ingestor
    try:
        from elastic.elastic import Elastic
        from services.recommendation import recommendations
    except Exception as e:
        traceback.print_exc(e)
        sys.exit(1)

    ingestor = ingest(args.nlp.strip(), args.factors, args.statements)

    # Create ES connection from args
    es_args = args.url.rsplit(':', 1)
    es = Elastic(es_args[0].strip(), es_args[1].strip())

    try:
        print(f'Generating recommendations for index: {args.index}')
        ingestor(args.index.strip(), es)
    except Exception as e:
        traceback.print_exc(e)
        sys.exit(1)

    print(f'Finished generating recommendations for index: {args.index}')
    sys.exit(0)
