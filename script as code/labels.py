import sys
import pandas as pd
import pickle
from tqdm import tqdm

# File export suffix
start_index = 0
number_of_stays = 100
output_path = "../scripts/output/"


def save_as_pickle(data, file_name, path=output_path):
    file = open(path + file_name, 'wb')
    pickle.dump(data, file)
    file.close()


def get_pickle(file_name, path=output_path):
    return pickle.load(open(path + file_name, 'rb'))


print("-- Loading data --")

data = get_pickle('data_complete_v4.1')
dist_data = get_pickle("distance_data_v4.1")


stays = list(dist_data['hadm_id'].unique())[
    start_index: start_index + number_of_stays]

print("-- Data loaded --")

labels = []

transfer_label_data = data[['eventtype', 'careunit', 'event_encoded']]
icu_label_data = data[['label', 'value',
                       'valuenum',	'valueuom', 'event_encoded']]


for event_type in tqdm(transfer_label_data['eventtype'].unique()):
    # values = data[data['eventtype'] == event_type].drop_duplicates()
    values = transfer_label_data[transfer_label_data['eventtype']
                                 == event_type].drop_duplicates()
    if len(values) == 0:
        continue
    else:
        label = {
            'type': 'Transfer',
            'care_unit': event_type,
            'value_enc': values.iloc[0, 2],
            'values': [{'event_type': v.careunit} for v in values.itertuples(index=True)]
        }

    labels.append(label)

for label in tqdm(icu_label_data['label'].unique()):
    values = icu_label_data[icu_label_data['label'] == label].drop_duplicates()
    if len(values) == 0:
        continue
    else:
        label = {
            'type': 'ICU measurement',
            'measurement': label,
            'value_enc': values.iloc[0, 4],
            'unit': values.iloc[0, 3] if not pd.isnull(values.iloc[0, 3]) else -1,
            'values': [{'value': v.value} for v in values.itertuples(index=True)]
        }
    labels.append(label)


save_as_pickle(labels, 'labels')

print("-- Done --")
