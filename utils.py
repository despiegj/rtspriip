import pandas as pd

def get_index_name(selected_index,index_options):
    df_label = pd.DataFrame(index_options)
    idx = df_label.value == selected_index
    return df_label.loc[idx,'label'].values[0]

