import random
import numpy as np
from tqdm import tqdm

# User settings
series_length = 25 # length of the sequence; longer sequences take longer to calculate
items = 5 # size of the number pool; must be at least 2

# Penalty terms (see readme.md for a detailed explanation)
penalty_setting_repetition = 1.8
penalty_setting_mirror = 1.3
penalty_setting_ascending = 1.1

def detect_immediate_repetition(derivative_1):
	return derivative_1 == 0

def measure_consecutive_true_blocks(bool_array):
	first_item = bool_array[0]
	derivative_1 = bool_array[:-1] != bool_array[1:]
	padded_derivative_1 = np.concatenate(([first_item],derivative_1,[True]))
	value_change_locations = np.where(padded_derivative_1)[0]
	block_lengths = np.diff(value_change_locations)[::2]
	return block_lengths

# Trying a few thousand candidates should be enough to find a good one
bestSeries = None
bestScore = None
iterations = int(series_length * 100 * 10/items) # this number is mostly guesswork
for i in tqdm(range(iterations)):

	# Generate a completely random candidate
	penalty_duplicate = 0
	duplicate_block_count = 0
	series = np.random.randint(1,items+1,series_length)
	derivative_1 = np.diff(series)
	
	# Search for linear increases or decreases like [5,6] or [4,3,2]
	penalty_ascending = 0
	ascending_block_count = 0
	ascending_block_sizes = measure_consecutive_true_blocks(derivative_1 == 1)
	descending_block_sizes = measure_consecutive_true_blocks(derivative_1 == -1)
	penalty_block_sizes = np.concatenate((ascending_block_sizes, descending_block_sizes))
	# Penalize these patterns much more with increasing length
	for penalty_block_size in penalty_block_sizes:
		if penalty_block_size > 1:
			ascending_block_count += 1
			penalty_ascending += penalty_setting_ascending ** penalty_block_size - 1

	# Search for "mirror" patterns, (back-forward-back) like [3,4,3] or [6,2,6]
	# The derivative of this pattern looks like [1,-1] or [-4,4]
	penalty_mirror = 0
	mirror_block_count = 0
	# First step: change every second sign of the derivative, so that the patterns look like [1,1] or [-4,-4]
	oscillating_derivative_1 = np.multiply(derivative_1, np.resize([1,-1],len(derivative_1)))
	# Second step: find repeating blocks within this new series
	mirror_pattern = detect_immediate_repetition(np.diff(oscillating_derivative_1))
	# Third step: measure the length of these blocks
	mirror_block_sizes = measure_consecutive_true_blocks(mirror_pattern)
	# Penalize this pattern more with increasing length
	for mirror_block_size in mirror_block_sizes:
		if mirror_block_size == 1:
			mirror_block_count += 1
			penalty_mirror += penalty_setting_mirror ** mirror_block_size - 1

	# Search for repeating subpatterns
	penalty_repetition = 0
	repetition_block_count = 0
	# Check for immediate repetitions first
	for start_index in range(0,int(series_length/3)):
		repetition_locations = detect_immediate_repetition(derivative_1)
		repetition_block_lengths = measure_consecutive_true_blocks(repetition_locations)
		for repetition_block_length in repetition_block_lengths:
			penalty_repetition += penalty_setting_repetition ** repetition_block_length - 1
	# Next, only check for fairly short patterns since duplicates of longer ones are really unlikely
	for pattern_length in range(2,int(series_length/3)):
		# Make a list of all possible sub-patterns with this length
		end_index = (series_length - pattern_length) - 1
		patterns = np.zeros((end_index, pattern_length))
		for start_index in range(0,end_index):
			stop_index = start_index + pattern_length
			pattern = series[start_index:stop_index]
			patterns[start_index,:] = pattern
		# Search for matches between subpatterns
		match_elements = patterns[:, np.newaxis] == patterns
		match_matrix = match_elements.all(2)
		# Determine indices of duplicates in rows with more than one match
		rows_with_duplicates = np.greater(np.count_nonzero(match_matrix, axis=0), 1)
		repetition_block_count += np.count_nonzero(match_matrix[rows_with_duplicates])
		if np.count_nonzero(rows_with_duplicates) > 0:
			row_indices, duplicate_indices = np.where(match_matrix[rows_with_duplicates])
			# Measure distance between duplicates
			for row_index in np.unique(row_indices):
				duplicates_row = duplicate_indices[row_indices == row_index]
				duplicates_distances = np.diff(duplicates_row)
				# Calculate a mitigation term that relieves the penalty with distance
				for duplicates_distance in duplicates_distances:
					mitigation = 1 / duplicates_distance ** 1.5
					# Apply penalty from this duplicate
					penalty_repetition += (penalty_setting_repetition ** pattern_length - 1) * mitigation

	penalty = penalty_mirror + penalty_ascending + penalty_repetition
	if bestScore is None:
		bestScore = penalty
		penalties = [penalty_mirror, penalty_ascending, penalty_repetition]
		violations = [mirror_block_count, ascending_block_count, repetition_block_count]
		bestSeries = series
	if penalty < bestScore:
		bestScore = penalty
		penalties = [penalty_mirror, penalty_ascending, penalty_repetition]
		violations = [mirror_block_count, ascending_block_count, repetition_block_count]
		repetitions = [row_indices, duplicate_indices, mirror_block_sizes]
		bestSeries = series

print('Best sequence with a length of {:d} and a number pool with size {:d}:'.format(series_length, items))
print(bestSeries)
print('Flaws of this sequence:')
print('{:d} directly mirrored patterns (e.g. 1 2 3 2 1)'.format(violations[0]))
print('{:d} steadly increasing or decreasing series (e.g. 1 2 3)'.format(violations[1]))
print('{:d} repeating sub-patterns (e.g. 1 2 3 1 2)'.format(violations[2]))
print('Total score: {:.2f} (zero would be ideal)'.format(bestScore))
print('Penalties: mirror: {:.2f}, ascending: {:.2f}, repetition:{:.2f}'.format(*penalties))