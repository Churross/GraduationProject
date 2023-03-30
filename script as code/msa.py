import os
import copy
import pickle
import numpy as np
from tqdm import tqdm
from Bio import AlignIO
import scipy.cluster.hierarchy as shc


# File export suffix
start_index = 0
number_of_stays = 1000
display_matrix = False
output_path = "../scripts/output/"
run_test_data = False
output_folder = f"stays-{number_of_stays}/"
file_suffix = '_' + str(number_of_stays)
stay_length = 20
sequences = []
alignments_output = f"{output_folder}alignments/"


print(f'[INFO] number of sequences: {number_of_stays}')


def save_as_pickle(data, file_name, path=output_path):
    file = open(path + file_name, 'wb')
    pickle.dump(data, file)
    file.close()


def get_pickle(file_name, path=output_path):
    return pickle.load(open(path + file_name, 'rb'))


def sequence_to_fasta(sequences: list, sequence_ids, id, path=output_path, folder=output_folder):
    if not os.path.isdir(path + folder):
        os.makedirs(path + folder)

    file_name = f"{path + folder}sequences-{id}.fa"

    if not os.path.exists(file_name):
        file = open(file_name, 'w')
        for i in range(len(sequences)):
            file.write(f">{sequence_ids[i]}\n{sequences[i]}\n")
        file.close()


def sort_by_indexes(list_data, indexes, reverse=False):
    return [val for (_, val) in sorted(zip(indexes, list_data), key=lambda x:
            x[0], reverse=reverse)]


print("[INFO] Loading data")

# data = get_pickle('data_complete_v4')
dist_data = get_pickle("distance_data_v4.1")

# if run_test_data:
#     dist_matrix = get_pickle("distance_matrix_" +
#                              str(number_of_stays) + '_test')
#     links = get_pickle('links' + file_suffix + "_test")
# else:
dist_matrix = get_pickle("distance_matrix_" + str(number_of_stays))
links = get_pickle('links' + file_suffix)

stays = list(dist_data['hadm_id'].unique())[
    start_index: start_index + number_of_stays]

print("[INFO] Data loaded")

dend = shc.dendrogram(links, labels=stays, leaf_rotation=-90)

sequences = []
if run_test_data:
    print("[INFO] Test data")
    for stay in stays:
        events = dist_data[dist_data['hadm_id'] == stay][0:stay_length]
        print(f"length events: {len(events)}")
        sequences.append(''.join(list(events['event_encoded'])))
else:
    print("[INFO] Using complete data")
    for stay in stays:
        events = dist_data[dist_data['hadm_id'] == stay]
        sequences.append(''.join(list(events['event_encoded'])))


def cluster_events(level, stays, links):
    clusters = get_clusters_by_level(level, links)
    unique_levels = list(set(clusters))

    cluster_level = copy.deepcopy(level)

    for count, level in enumerate(unique_levels):
        cluster = [i for i, x in enumerate(clusters) if x == level]
        bidx = branch_depths.index(cluster_level)

        sequence_ids = [int(stays[i]) for i in cluster]

        alignment_levels = []
        if (cluster_level > 0):
            alignment_levels = list(dict.fromkeys([
                sequence_alignments[bidx - 1][stays.index(s)] for s in sequence_ids]))

        if len(sequence_ids) == 1:
            # base case: sequence need not to be merged
            # print("[INFO] base case, no alignment")
            pass

        elif (len(alignment_levels) == 1 and alignment_levels[0] == -1) or (len(alignment_levels) == 0 and cluster_level == 0):
            # case sequences need to be merged, no prior alignment
            print("[INFO] sequences need to be aligned, no alignment present")

            sequence_to_fasta(sequences=[sequences[stays.index(s)] for s in sequence_ids],
                              sequence_ids=sequence_ids, id=f"{cluster_level}-{count}")

            sequences_file_path = f"{output_path + output_folder}sequences-{cluster_level}-{count}.fa"
            base_alignment_file_path = f"{output_path + output_folder}alignment-{cluster_level}-{count}.fasta"

            # mafft_align = f"/usr/local/bin/mafft --reorder --anysymbol --maxiterate 0 --retree 1 --6merpair --quiet --thread 4 {sequences_file_path} > {base_alignment_file_path}"
            mafft_align = f"/usr/local/bin/mafft --text --reorder --maxiterate 0 --retree 1 --6merpair --quiet --thread 4 {sequences_file_path} > {base_alignment_file_path}"
            # mafft_align = f"/usr/local/bin/mafft --text --thread 4 {sequences_file_path} > {base_alignment_file_path}"
            os.system(mafft_align)

            alignment = AlignIO.read(base_alignment_file_path, "fasta")
            aggregated_sequence = get_aggregated_sequence(alignment)

            cluster_alignment = {
                'file': base_alignment_file_path,
                'stays': sequence_ids,
                'sequence': aggregated_sequence,
                'alignment': [{'hadm_id': aligned_seq.id, "sequence": [
                    event for event in aligned_seq.seq]} for aligned_seq in alignment]
            }

            save_as_pickle(
                cluster_alignment, f"alignment-info-{number_of_stays}-level-{cluster_level}-count-{count}.p", path=output_path + alignments_output)

            for s in sequence_ids:
                sidx = stays.index(s)
                sequence_alignments[bidx][sidx] = f"{cluster_level}-{count}"

        elif len(alignment_levels) == 1 and alignment_levels[0] != -1:
            # case sequences have already been merged, no action needed
            print("[INFO] have been merged, no action needed")
            for s in sequence_ids:
                sidx = stays.index(s)
                sequence_alignments[bidx][sidx] = sequence_alignments[bidx - 1][sidx]

        else:
            # merging and or alignment needs to happen
            # print("[INFO] merge needed and optional alignment")

            not_aligned_sequences = [
                s for s in sequence_ids if sequence_alignments[bidx - 1][stays.index(s)] == -1]

            sequence_to_fasta(sequences=[sequences[stays.index(s)] for s in not_aligned_sequences],
                              sequence_ids=not_aligned_sequences, id=f"{cluster_level}-{count}")

            sequences_file_path = f"{output_path + output_folder}sequences-{cluster_level}-{count}.fa"
            base_alignment_file_path = f"{output_path + output_folder}alignment-{cluster_level}-{count}.fasta"

            # Get alignment files of previous merged
            aligned_sequences = [
                s for s in sequence_ids if sequence_alignments[bidx - 1][stays.index(s)] != -1]

            print(
                f"[INFO] merge needed ({len(aligned_sequences)}) and optional alignment ({len(not_aligned_sequences)})")

            aligned_files = []

            for a in aligned_sequences:
                file_details = sequence_alignments[bidx -
                                                   1][stays.index(a)].split('-')
                aligned_files.append(
                    f"{output_path + output_folder}alignment-{file_details[0]}-{file_details[1]}.fasta")

            aligned_files = list(dict.fromkeys(
                aligned_files))  # Remove duplicates
            table_files = " ".join(aligned_files)
            aligned_files.append(sequences_file_path)
            input_files = " ".join(aligned_files)

            # Create merge table for MAFFT
            merge_table = f"/usr/bin/ruby makemergetable.rb {table_files} > subMSAtable"
            os.system(merge_table)

            # Create input file
            input_command = f"cat {input_files} > inputFile"

            os.system(input_command)

            # mafft_merge = f"/usr/local/bin/mafft --merge subMSAtable --text --thread 4 inputFile > {base_alignment_file_path}"
            # mafft_merge = f"/usr/local/bin/mafft --merge subMSAtable --reorder --anysymbol --maxiterate 0 --retree 1 --6merpair --quiet --thread 4 inputFile > {base_alignment_file_path}"
            mafft_merge = f"/usr/local/bin/mafft --merge subMSAtable --text --reorder --maxiterate 0 --retree 1 --6merpair --quiet --thread 4 inputFile > {base_alignment_file_path}"
            os.system(mafft_merge)

            alignment = AlignIO.read(base_alignment_file_path, "fasta")
            aggregated_sequence = get_aggregated_sequence(alignment)

            cluster_alignment = {
                'file': base_alignment_file_path,
                'stays': sequence_ids,
                'sequence': aggregated_sequence,
                'alignment': [{'hadm_id': aligned_seq.id, "sequence": [
                    event for event in aligned_seq.seq]} for aligned_seq in alignment]
            }

            save_as_pickle(
                cluster_alignment, f"alignment-info-{number_of_stays}-level-{cluster_level}-count-{count}.p", path=output_path + alignments_output)

            for s in sequence_ids:
                sidx = stays.index(s)
                sequence_alignments[bidx][sidx] = f"{cluster_level}-{count}"


def get_clusters_by_level(level, links):
    return list(shc.fcluster(links, t=level, criterion="distance"))


def get_aggregated_sequence(al_seq):
    agg_sequence = list(
        zip(*[sequence.seq for sequence in al_seq]))
    # Remove duplicates
    agg_sequence = [list(set(agg_event)) for agg_event in agg_sequence]
    # Convert characters to numbers
    agg_sequence = [[event for event in agg_event]
                    for agg_event in agg_sequence]

    # Only have lists when aggregate event
    agg_sequence = [event[0] if len(
        event) == 1 else event for event in agg_sequence]

    return agg_sequence


branch_depths = [-1]
for d in dend['dcoord']:
    branch_depths.append(d[1])
branch_depths = list(dict.fromkeys(branch_depths))
branch_depths.sort()


if not os.path.isdir(output_path + alignments_output):
    os.makedirs(output_path + alignments_output)

sequence_alignments = [[-1] * len(stays) for i in range(len(branch_depths))]

for index, branch_depth in enumerate(tqdm(branch_depths)):
    # Calculate sequence alignment
    print(f"Aligning level {index, branch_depth}")
    cluster_events(branch_depth, stays, links)

print("[INFO] Saving alignment")
# if run_test_data:
#     save_as_pickle(sequence_alignments, 'alignments_' +
#                    str(number_of_stays) + "_test")
# else:
save_as_pickle(sequence_alignments, 'alignments_' + str(number_of_stays))
# save_as_pickle(alignments, 'alignments' + file_suffix)


print("[INFO] Done")
