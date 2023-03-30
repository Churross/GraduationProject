import os
import sys
import pickle
import pandas as pd
import editdistance
from tqdm import tqdm

number_of_stays = 0
start_index = 0
display_matrix = True
run_test_data = False
stay_length = 20
output_path = "../scripts/output/"
global output_folder
global file_suffix


def save_as_pickle(data, file_name, path=output_path):
    file = open(path + file_name, 'wb')
    pickle.dump(data, file)
    file.close()


def get_pickle(file_name, path=output_path):
    return pickle.load(open(path + file_name, 'rb'))


def main(argv):
    number_of_stays = argv[0]
    output_folder = f"stays-{number_of_stays}/distance/"
    file_suffix = '_real_' + str(number_of_stays)

    print(f"Number of stays: {number_of_stays}")

    print("[INFO] Loading data ")
    # data = get_pickle('data_complete_v4')
    dist_data = get_pickle("distance_data_v4.1")

    stays = list(dist_data['hadm_id'].unique())[
        start_index: start_index + int(number_of_stays)]

    if run_test_data:
        print(f"[INFO] Generating sequences of max length: {stay_length}")
        test_data_dist = pd.DataFrame(columns=dist_data.columns)
        for stay in stays:
            events_dist = dist_data[dist_data['hadm_id'] == stay]
            # test_data = pd.concat([test_data, events.head()])
            test_data_dist = pd.concat(
                [test_data_dist, events_dist.head(n=stay_length)])

        test_data_dist = test_data_dist.reset_index()
        test_data_dist = test_data_dist.drop(columns=['index'])
        dist_data = test_data_dist

    sequences = [dist_data[dist_data['hadm_id']
                           == hadm_id]['event_encoded'].tolist() for hadm_id in stays]

    print("[INFO] Data Loaded ")

    length = len(sequences)
    outputMatrix = [[0] * length for _i in range(length)]

    progress = 0
    updateStep = 100
    with tqdm(total=0.5*(length * length)) as pbar:
        for idxA in range(0, length):
            for idxB in range(idxA, length):
                max_length = max(len(sequences[idxA]), len(sequences[idxB]))
                distance = editdistance.eval(
                    sequences[idxA], sequences[idxB])/max_length
                outputMatrix[idxA][idxB] = distance
                outputMatrix[idxB][idxA] = distance
                if (progress % updateStep == 0):
                    pbar.update(updateStep)
                progress += 1

    # for line in outputMatrix:
    #     print('  '.join(map(str, line)))
    # if run_test_data:
    #     save_as_pickle(outputMatrix, 'distance_matrix_' +
    #                    str(number_of_stays) + '_test')
    #     save_as_pickle(outputMatrix, 'dist_matrix_' +
    #                    str(number_of_stays) + '_test')
    # else:
    save_as_pickle(outputMatrix, 'distance_matrix_' + str(number_of_stays))
    save_as_pickle(outputMatrix, 'dist_matrix_' + str(number_of_stays))

    print("[INFO] Done")


if __name__ == "__main__":
    main(sys.argv[1:])
