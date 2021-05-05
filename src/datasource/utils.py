import pandas as pd


def dedupe_recommendations(recos, vector_field_name, text_field_name, list_agg_fields):
    # These are all the fields supplied by the user. i.e: everything
    # we want to filter on
    existing_fields = {'text_original', vector_field_name, text_field_name}.union(set(list_agg_fields))

    # Get the remaining fields to keep in the DataFrame
    fields = set(recos[0].keys())
    fields = list(fields - existing_fields)

    # TODO: Maybe worth moving away from pandas here in the future
    reco_df = pd.DataFrame(recos)
    reco_df = reco_df.groupby(text_field_name, as_index=False).agg({
        vector_field_name: lambda x: x.iloc[0],
        'text_original': lambda x: x.tolist(),
        **{field: (lambda x: x.tolist()) for field in list_agg_fields},
        **{field: (lambda x: x.iloc[0]) for field in fields}
    })
    deduped_recos = reco_df.to_dict(orient='records')
    return deduped_recos
