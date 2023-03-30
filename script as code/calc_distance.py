import os
import sys
import pickle
from tqdm import tqdm

# from pyfamsa import Aligner, Sequence
from levenstein_dp import levenshteinDistanceDP as ld


# File export suffix
start_index = 0
number_of_stays = 100
display_matrix = True
output_path = "../scripts/output/"
run_test_data = False
output_folder = f"stays-{number_of_stays}/distance/"


file_suffix = '_real_' + str(number_of_stays)


def save_as_pickle(data, file_name, path=output_path):
    file = open(path + file_name, 'wb')
    pickle.dump(data, file)
    file.close()


def get_pickle(file_name, path=output_path):
    return pickle.load(open(path + file_name, 'rb'))


def save_distance_row(row, row_number, path=output_path, folder=output_folder):
    if not os.path.isdir(path+folder):
        os.makedirs(path + folder)

    file_name = f"{path+folder}distances-{number_of_stays}-row-{row_number}"

    if not os.path.exists(file_name):
        file = open(file_name, 'wb')
        pickle.dump(row, file)
        file.close()


print("-- Loading data --")
data = get_pickle('data_complete_v4')
dist_data = get_pickle("distance_data_v4")
print("-- Data loaded --")

stays = list(dist_data['hadm_id'].unique())[
    start_index: start_index + number_of_stays]


def compute_distance_matrix(number_of_stays=number_of_stays):
    stays = list(dist_data['hadm_id'].unique())[
        start_index: start_index + number_of_stays]
    distances = []

    for y in tqdm(range(len(stays))):

        row_data = f"{output_path + output_folder}distances-{number_of_stays}-row-{y}"

        if not os.path.exists(row_data):
            sequence_y = dist_data[dist_data['hadm_id']
                                   == stays[y]]['event_encoded'].tolist()
            distance_row = []

            for x in tqdm(range(y, len(stays))):
                sequence_x = dist_data[dist_data['hadm_id']
                                       == stays[x]]['event_encoded'].tolist()

                # Diagonal
                if stays[y] == stays[x]:
                    distance_row.append(0)
                    continue
                # All other
                else:
                    max_length = max(len(sequence_x), len(sequence_y))
                    distance_row.append(ld(sequence_y, sequence_x)/max_length)

            save_distance_row(distance_row, y)

        else:
            distance_row = get_pickle(row_data, path="")

        distances.append(distance_row)

    # print(distances)
    if display_matrix:
        print('Computed distance matrix:')

        for line in distances:
            print('  '.join(map(str, line)))
    return distances


dist_matrix = compute_distance_matrix()
save_as_pickle(dist_matrix, 'distance_matrix_' + str(number_of_stays))
save_as_pickle(dist_matrix, 'dist_matrix_' + str(number_of_stays))

print("-- Done --")
