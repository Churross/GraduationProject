
from ast import arg
import os
import sys
import pickle
from tqdm import tqdm
from tqdm.contrib.concurrent import thread_map  # or thread_map
from multiprocessing import Pool
from levenstein_dp import levenshteinDistanceDP as ld

# File export suffix
start_index = 0
number_of_stays = 1000
display_matrix = True
output_path = "../scripts/output/"
run_test_data = False
output_folder = f"stays-{number_of_stays}/distance/"
file_suffix = '_real_' + str(number_of_stays)
sequence_y = ''
index_y = 0
NUM_WORKERS = 4
global data
global dist_data
global stays


# st = [1, 2, 3, 4, 5, 6]
# st = [1, 2, 3]


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


def compute_distance(y):
    # print(f"\ny: {y}")

    row_data = f"{output_path + output_folder}distances-{number_of_stays}-row-{y}"
    distance_row = []

    if not os.path.exists(row_data):
        sequence_y = dist_data[dist_data['hadm_id']
                               == stays[y]]['event_encoded'].tolist()

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
                distance_row.append(
                    ld(sequence_y, sequence_x)/max_length)

        save_distance_row(distance_row, y)

    else:
        distance_row = get_pickle(row_data, path="")

    return distance_row
    # return x*x


def init_worker(data_dist, stay_data):
    global stays
    global dist_data
    # data = get_pickle('data_complete_v3')
    dist_data = data_dist
    stays = stay_data


# def get_result(result):
#     global distances
#     distances.append(result)


if __name__ == '__main__':
    distances = []

    print("-- Loading data --")

    data = get_pickle('data_complete_v3')
    dist_data = get_pickle("distance_data_v3")

    stays = list(dist_data['hadm_id'].unique())[
        start_index: start_index + number_of_stays]

    print("-- Data loaded --")

    with Pool(NUM_WORKERS, initializer=init_worker, initargs=(dist_data, stays)) as p:

        # for i in range(len(stays)):
        #     p.apply_async(compute_distance, args=(i), callback=get_result)
        # p.close()
        # p.join()

        # for distance_row in tqdm(p.imap(compute_distance, range(len(stays)))):
        for distance_row in thread_map(p.map(compute_distance, range(len(stays))), max_workers=NUM_WORKERS):
            print("-----")
            print(f"result: {distance_row}")
            distances.append(distance_row)

    if display_matrix:
        print('Computed distance matrix:')

        for line in distances:
            print('  '.join(map(str, line)))

    save_as_pickle(distances, 'distance_matrix_' + str(number_of_stays))
    save_as_pickle(distances, 'dist_matrix_' + str(number_of_stays))
    print("-- Done --")
