import sys
import pickle
import matplotlib
import scipy.cluster.hierarchy as shc


matplotlib.use('agg')

# File export suffix
start_index = 0
number_of_stays = 0
stay_length = 20
display_matrix = True
output_path = "../scripts/output/"
run_test_data = False


def save_as_pickle(data, file_name, path=output_path):
    file = open(path + file_name, 'wb')
    pickle.dump(data, file)
    file.close()


def get_pickle(file_name, path=output_path):
    return pickle.load(open(path + file_name, 'rb'))


def sequence_to_fasta(sequences: list, file_name, path=output_path):
    file = open(path + file_name + '.fa', 'w')
    for i in range(len(sequences)):
        file.write(f">sequence_{i}\n{sequences[i]}\n")
    file.close()


def get_sequence_distance_list(u, v):
    index_u, index_v = stays.index(u[0]), stays.index(v[0])
    return dist_matrix[min(index_u, index_v)][max(index_u, index_v) - min(index_u, index_v)]


def get_sequence_distance_matrix(u, v):
    index_u, index_v = stays.index(u[0]), stays.index(v[0])
    return dist_matrix[index_u][index_v]


def main(argv):
    global dist_matrix
    global stays

    number_of_stays = argv[0]

    # if run_test_data:
    #     file_suffix = '_' + str(number_of_stays) + "_test"
    # else:
    file_suffix = '_' + str(number_of_stays)

    print(f"[INFO] Number of sequences: {number_of_stays}")
    print("[INFO] Loading data")

    data = get_pickle('data_complete_v4.1')
    dist_data = get_pickle("distance_data_v4.1")
    # if run_test_data:
    #     print("[INFO] Getting test dist data")
    #     dist_matrix = get_pickle(
    #         "distance_matrix_" + str(number_of_stays) + "_test")
    # else:
    print("[INFO] Using complete dist data")
    dist_matrix = get_pickle("distance_matrix_" + str(number_of_stays))

    stays = list(dist_data['hadm_id'].unique())[
        start_index: start_index + int(number_of_stays)]

    print("[INFO] Data loaded")

    clust_data = data.drop_duplicates(subset=['hadm_id'])[
        start_index: start_index + int(number_of_stays)]

    clust_data = clust_data.drop(columns=['event_id', 'subject_id', 'transfer_id', 'eventtype',
                                          'careunit', 'intime', 'outtime', 'charttime', 'event',
                                          'value', 'valuenum', 'valueuom',
                                          'label', 'category', 'param_type',
                                          'value_categorical',
                                          'event_encoded'])

    # links = shc.linkage(clust_data, metric=get_sequence_distance_list)
    links = shc.linkage(clust_data, metric=get_sequence_distance_matrix)
    dend = shc.dendrogram(links, labels=stays, leaf_rotation=-90)

    print("[INFO] Saving data")

    print(f"[INFO] File suffix: {file_suffix}")
    save_as_pickle(links, 'links' + file_suffix)
    save_as_pickle(stays, 'stays' + file_suffix)
    if run_test_data:
        print("[INFO] Saving test data")
        save_as_pickle(data[data['hadm_id'].isin(stays)].head(
            n=stay_length), 'events' + file_suffix)
    else:
        print("[INFO] Saving complete data")
        save_as_pickle(data[data['hadm_id'].isin(stays)],
                       'events' + file_suffix)

    print("Dend info")
    print(dend['ivl'])
    print(stays)

    print("[INFO] Done")


if __name__ == "__main__":
    main(sys.argv[1:])
