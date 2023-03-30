import io
import json
import pickle
import matplotlib
import math
import numpy as np
import pandas as pd
from flask_cors import CORS
from flask import Flask, Response, request, jsonify
import scipy.cluster.hierarchy as shc
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from spmf import Spmf
from tqdm import tqdm
import os
import copy


matplotlib.use('agg')


app = Flask(__name__)
cors = CORS(app)

# Select which files to load
file_suffix = "_test"


def get_data(file_name):
    return pickle.load(open(file_name, 'rb'))


print('Loading data')
print('[INFO] Loading labels')
if 'test' in file_suffix:
    labels = get_data('../scripts/output/labels' + file_suffix)
else:
    labels = get_data('../scripts/output/labels')
print('[INFO] Loading distance matrix')
distances = get_data('../scripts/output/dist_matrix' + file_suffix)
print('[INFO] Loading links')
links = get_data('../scripts/output/links' + file_suffix)
print('[INFO] Loading stays')
stays = get_data('../scripts/output/stays' + file_suffix)
print('[INFO] Loading events')
events = get_data('../scripts/output/events' + file_suffix)
print('[INFO] Loading clusters')
clusters = get_data('../scripts/output/alignments' + file_suffix)
print('[INFO] Data loaded')

print('[INFO] Calculating dendrogram')
dend = shc.dendrogram(links, labels=stays, leaf_rotation=-90)
print('[INFO] Dendrogram calculated')


def get_all_levels(dend):
    branch_depths = [-1]
    branch_depths.extend(list(set([d[1] for d in dend['dcoord']])))
    branch_depths.sort()
    return branch_depths


def sort_by_indexes(list_data, indexes, reverse=False):
    return [val for (_, val) in sorted(zip(indexes, list_data), key=lambda x:
            x[0], reverse=reverse)]


levels = get_all_levels(dend)
indices = [dend['ivl'].index(i) for i in stays]
calc_patterns = False
MIN_PATTERN_LENGTH = 2
SEGMENT_SIZE = 4000
# FIRST_PERCENTILE = 2183
FIRST_PERCENTILE = 8000
sequence_to_split_pattern_lookup = []
PATTERN_OUTPUT = f"patterns/pattern-{file_suffix[1:]}/"
patterns = pd.DataFrame(columns=['pattern', 'sup', 'encoding'])

for i in range(len(clusters)):
    clusters[i] = sort_by_indexes(clusters[i], indices)

stays_original = stays

stays = sort_by_indexes(copy.deepcopy(stays), indices)


sequences = []
for stay in stays:
    e = events[events['hadm_id'] == stay]
    sequences.append(''.join(list(e['event_encoded'])))


@app.route('/stay-order')
def get_stays_order():
    # TODO: check if not dend['ivl'] needs to be used
    return jsonify([int(i) for i in stays])


def get_clusters_by_level(level):
    return list(shc.fcluster(links, t=level, criterion="distance"))


@app.route('/levels')
def get_available_levels():
    dend_data = {
        'sequences': [int(i) for i in stays_original],
        'levels': []
    }
    for index, level in enumerate(get_all_levels(dend)):
        dend_data['levels'].append({
            'level': level,
            'cluster': [int(i) for i in get_clusters_by_level(level)]
        })

    return jsonify(dend_data)


@ app.route("/events/types")
def get_event_types():
    types = [{
        'label': x['measurement'],
        'type': 'ICU',
        'code': x['value_enc'],
        'unit': x['unit'],
        'values': sorted((y['value'] for y in x['values']), key=lambda z: z if x['unit'] == -1 else float(z))
        # 'encodings': list(dict.fromkeys([y['value_enc'] for y in x['values'] if y['value_enc']]))
    } if x['type'] == 'ICU measurement' else {
        'label': x['care_unit'],
        'code': x['value_enc'],
        'type': "Transfer",
        'values': [str(y['event_type']) for y in x['values']]
    } for x in labels]
    types.sort(key=lambda x: x['type'])
    return jsonify(types)


@ app.route("/events/types/<event_type>")
def get_event_types_values(event_type):
    return jsonify([x for x in labels if x['measurement'] == event_type][0])


@ app.route('/cluster/tree')
def get_cluster_tree():
    fig = plot_dendrogram()
    output = io.BytesIO()
    FigureCanvas(fig).print_png(output)
    return Response(output.getvalue(), mimetype='image/png')


@app.route('/patterns')
def get_patterns():
    return Response(patterns.to_json(orient="records"), mimetype='application/json')


@ app.route('/cluster/tree/max-level')
def get_max_cluster_level():
    return Response(json.dumps(max(shc.maxdists(links).tolist())))


@ app.route('/sequence/<hadm_id>')
def get_event_from_sequence(hadm_id):
    # TODO: Fix for fp sequences

    event_index = request.args.get('index')

    if event_index:
        event = get_event_details(hadm_id, int(event_index))
    else:
        event = get_event_details(hadm_id, 0)

    drop_columns = ['event', 'event_encoded']

    if 'label' in event.columns:
        if event.iloc[0].at['param_type'] == 'Text':
            drop_columns = drop_columns + ['param_type']
            if 'valuenum' in event.columns:
                drop_columns = drop_columns + ['valuenum']
            if 'value_categorical' in event.columns:
                drop_columns = drop_columns + ['value_categorical']

        else:
            drop_columns = drop_columns + \
                ['value', 'param_type', 'value_categorical']

    return Response(event.drop(columns=drop_columns).to_json(orient="records"), mimetype="application/json")


@app.route('/sequence/aggregate')
def get_aggregate_event_from_sequence():
    sequences = request.args.get('sequences').split(",")

    agg_events = pd.DataFrame(columns=events.columns)

    for sequence in sequences:
        params = sequence.split(':')
        agg_events = pd.concat(
            [agg_events, get_event_details(params[0], int(params[1]))])

    return Response(agg_events.drop(columns=['event', 'event_encoded']).to_json(orient='records'), mimetype="application/json")


@app.route('/sequence/aggregate/pattern')
def get_aggregate_pattern_event_from_sequence():
    event_index = request.args.get('index')
    sequences = request.args.get('sequences').split(",")

    agg_patt_events = pd.DataFrame(columns=events.columns)

    for sequence in sequences:
        params = sequence.split(':')
        agg_patt_events = pd.concat(
            [agg_patt_events, get_event_details(params[0], int(params[1]), int(params[2]))])

    return Response(agg_patt_events.drop(columns=['event', 'event_encoded']).to_json(orient='records'), mimetype="application/json")


@app.route('/sequence/pattern/<hadm_id>')
def get_pattern_event_from_sequence(hadm_id):
    event_index = request.args.get('index')
    length_pattern = request.args.get('num_events')

    if not event_index:
        event_index = 0

    if not length_pattern:
        length_pattern = 0

    patt_events = get_event_details(
        hadm_id, int(event_index), int(length_pattern))

    return Response(patt_events.drop(columns=['event', 'event_encoded']).to_json(orient='records'), mimetype="application/json")


def plot_dendrogram():
    fig = matplotlib.pyplot.figure(tight_layout=True)
    dend = shc.dendrogram(links, labels=stays,
                          leaf_rotation=-90, leaf_font_size=10,)
    return fig


def get_event_details(hadm_id, event_index, num_events=1):
    event = copy.deepcopy(events[events['hadm_id'] == int(
        hadm_id)].iloc[event_index: event_index + num_events])

    event = event[event.columns[~event.isnull().all()]]

    drop_columns = ['event', 'event_encoded']

    if 'label' in event.columns:
        if event.iloc[0].at['param_type'] == 'Text':
            drop_columns = drop_columns + ['param_type']
            if 'valuenum' in event.columns:
                drop_columns = drop_columns + ['valuenum']
            if 'value_categorical' in event.columns:
                drop_columns = drop_columns + ['value_categorical']

        else:
            drop_columns = drop_columns + \
                ['value', 'param_type', 'value_categorical']

    return event


def get_frequent_patterns(input: list = [], min_sup: float = 0.4, max_gap: int = 1, max_pat_length=""):
    spmf = Spmf("VMSP", input_direct=input,
                input_type="text",
                output_filename="output.txt", spmf_bin_location_dir="/Users/youri/Downloads",
                arguments=[min_sup, max_pat_length, str(max_gap)])
    spmf.run()
    return spmf.to_pandas_dataframe()


def find_clustered_events(input_level):
    cluster_level = get_closest_cluster_level(input_level)
    level = levels.index(cluster_level)
    cluster_row = copy.deepcopy(clusters[level])
    alignment_levels = list(dict.fromkeys(cluster_row))

    alignment_data = {}
    for alignment_level in [i for i in alignment_levels if not i == -1]:
        file_param = alignment_level.split("-")
        alignment_data[alignment_level] = get_data(
            f'../scripts/output/stays-{file_suffix[1:]}/alignments/alignment-info-{file_suffix[1:]}-level-{file_param[0]}-count-{file_param[1]}.p')
        alignment_data[alignment_level]['aggregated'] = True
        for aligned_sequence in alignment_data[alignment_level]['alignment']:
            aligned_sequence['sequence'] = "".join(
                aligned_sequence['sequence'])

    cluster_data = []
    for index, clust in enumerate(cluster_row):
        if clust == -1:
            # return sequence data
            cluster_data.append({
                'stays': [int(stays[index])],
                'sequence': sequences[index],
                'aggregated': False
            })
        else:
            if not alignment_data[clust] in cluster_data:
                cluster_data.append(alignment_data[clust])

    return cluster_data


def fp_transform_cluster(c):
    for c_index, cluster in enumerate(c):
        for e_index, event in enumerate(cluster):
            if isinstance(event, list):
                for index, e in enumerate(event):
                    if e == '-':
                        c[c_index][e_index][index] = 100
                    else:
                        c[c_index][e_index][index] = int(e)
            else:
                c[c_index][e_index] = int(event)


def get_closest_cluster_level(level):
    keys = copy.deepcopy(levels)

    cluster_level = 0
    level = float(level)

    if level == 1:
        cluster_level = 1.0
    else:
        for clustered_level in keys:
            if (level >= cluster_level and level < clustered_level):
                break
            else:
                cluster_level = clustered_level

    return cluster_level


def store_frequent_patterns(patterns: list, file_name: str, output_path=PATTERN_OUTPUT):
    if not os.path.isdir(output_path):
        os.makedirs(output_path)

    file = open(output_path + file_name, 'wb')
    pickle.dump(patterns, file)
    file.close()


def load_frequent_patterns(file_name, path=PATTERN_OUTPUT):
    return pickle.load(open(path + file_name, 'rb'))


@ app.route("/cluster/<level>/events/")
def get_clustered_events_v2(level):
    min_sup = request.args.get('min_sup')

    level_events = find_clustered_events(level)

    if not min_sup:
        return Response(json.dumps(level_events), mimetype="application/json")

    else:
        global patterns

        min_sup = max(0.1, float(min_sup))
        c = [seq['sequence'] for seq in level_events]

        print('[INFO] preparing sequences')
        split_sequences = split_long_sequences(copy.deepcopy(c))

        pattern_file_name = 'patterns' + file_suffix + \
            "-" + level + "-" + str(min_sup)
        level_cluster_events = 'sequences' + file_suffix + \
            "-" + level + "-" + str(min_sup)

        if not os.path.isfile(PATTERN_OUTPUT + pattern_file_name):
            print('[INFO] computing patterns')
            patterns = get_frequent_patterns(
                input=split_sequences, min_sup=min_sup)

            if len(patterns) > 0:
                patterns = patterns[patterns['pattern'].apply(
                    lambda x: len(x) > 1)]
            if (len(patterns) > 0):
                patterns['encoding'] = range(300, len(patterns) + 300)
                patterns['aggregated'] = patterns.apply(lambda row: any(
                    len(i.strip()) > 1 for i in row.pattern), axis=1)
                patterns['seq_length'] = patterns.apply(
                    lambda row: len(row.pattern), axis=1)
                patterns = patterns.sort_values(
                    by=['seq_length', 'sup'], ascending=False)
                patterns = patterns.drop(columns=['seq_length'])

                seq = replace_frequent_patterns(c, patterns)
                seq = translate_fp_combined_sequences(seq)

                for index, s in enumerate(level_events):
                    # s['alignment'] = seq[index]
                    s['sequence'] = seq[index]

                store_frequent_patterns(
                    patterns=level_events, file_name=level_cluster_events)
                store_frequent_patterns(
                    patterns=patterns, file_name=pattern_file_name)

        else:
            print('[INFO] loading stored patterns')
            patterns = load_frequent_patterns(pattern_file_name)
            print(f"[INFO] level_events: {len(level_events)}")
            level_events = load_frequent_patterns(level_cluster_events)
            print(f"[INFO] level_events loaded: {len(level_events)}")

        print(f"\n#patterns found: {len(patterns)}")

        return Response(json.dumps(level_events), mimetype="application/json")


'''
-----
Frequent pattern mining functions
-----
'''


def sequence_to_list_of_strings(c):
    transformed_sequences = copy.deepcopy(c)

    for c_index, cluster in enumerate(transformed_sequences):
        for e_index, event in enumerate(cluster):

            if isinstance(event, list):
                for index, e in enumerate(event):
                    if e == '-':
                        transformed_sequences[c_index][e_index][index] = 'x'
                    else:
                        transformed_sequences[c_index][e_index][index] = e

                s = transformed_sequences[c_index][e_index]
                s.sort()
                transformed_sequences[c_index][e_index] = "".join(s)
            else:
                transformed_sequences[c_index][e_index] = event

        transformed_sequences[c_index] = " ".join(
            transformed_sequences[c_index])

    return transformed_sequences


def replace_frequent_patterns(c, patterns):
    num_patterns_inserted = 0
    inserted_patterns = []

    seq = replace_gaps_and_to_string(copy.deepcopy(c))
    average_reduction = 0

    for index, sequence in tqdm(enumerate(seq)):
        seq_inserted = 0
        seq_length = len(sequence)
        seq_length_reduction = 0

        s = " " + sequence + " "
        if s[0] != " ":
            s = s.ljust(len(s) + 1, " ")
        if s[-1] != " ":
            s = s.rjust(len(s) + 1, " ")

        for pattern in patterns.itertuples():
            pat = " " + " ".join(pattern.pattern) + " "

            if pat[0] != " ":
                pat = pat.ljust(len(pat) + 1, " ")
            if pat[-1] != " ":
                pat = pat.rjust(len(pat) + 1, " ")

            s_old = s
            s = s.replace(pat, str(pattern.encoding).center(
                len(str(pattern.encoding)) + 2, " "))

            if not s_old == s:
                seq[index] = s

                seq_inserted += 1
                num_patterns_inserted += 1
                seq_length_reduction += len(pattern.pattern) - 1
                inserted_patterns.append(pattern.encoding)

        reduction = (seq_length-(seq_length-seq_length_reduction)) / \
            (seq_length-seq_length_reduction) * 100

        print(
            f"Sequence length reduction by: {reduction}%")
        average_reduction += reduction

    print(f"number of patterns inserted: {num_patterns_inserted}")
    print(f"average sequence reduction: {average_reduction/len(seq)}%")

    return seq


def translate_fp_combined_sequences(seq):
    for index, sequence in tqdm(enumerate(seq)):
        if isinstance(sequence, str):
            seq[index] = sequence.strip().split(" ")

            for e_index, event in enumerate(seq[index]):
                if event.isdigit():
                    if patterns.iloc[np.where(patterns.encoding.values == int(event))].aggregated.values[0]:
                        seq[index][e_index] = [int(event)]
                    else:
                        seq[index][e_index] = int(event)
                else:
                    if len(event) > 1:
                        seq[index][e_index] = [e for e in event]
                    else:
                        seq[index][e_index] = event
        else:
            print(f'[ERROR] detected other type: {type(sequence)}')
    return seq


def split_long_sequences(sequences):
    segmented_sequences = []

    for s_index, sequence in enumerate(sequences):
        #     # print(type(sequence))
        #     # print(sequence[0:100])
        #     if len(sequence) > FIRST_PERCENTILE:
        #         for i in range(0, math.ceil(len(sequence) / SEGMENT_SIZE)):
        #             segmented_sequences.append(
        #                 sequence[i * SEGMENT_SIZE: (i + 1) * SEGMENT_SIZE - 1])
        #         sequence_to_split_pattern_lookup.append(s_index +
        #                                                 math.ceil(len(sequence) / SEGMENT_SIZE) - 1)
        #     else:
        segmented_sequences.append(sequence)
        sequence_to_split_pattern_lookup.append(s_index)

        # Transform (segmented) list sequences to (segmented) string sequences
    return replace_gaps_and_to_string(segmented_sequences)


def replace_gaps_and_to_string(c):
    seqs = copy.deepcopy(c)
    for s_index, sequence in enumerate(seqs):
        for e_index, event in enumerate(sequence):
            if isinstance(event, list):
                s_temp = [e if e != "-" else 'x' for e in event]
                s_temp.sort()
                seqs[s_index][e_index] = "".join(s_temp)

        seqs[s_index] = " ".join(seqs[s_index])
    return seqs
