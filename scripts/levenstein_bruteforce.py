# from functools import lru_cache

# Adapted from https://towardsdatascience.com/text-similarity-w-levenshtein-distance-in-python-2f7478986e75


def levenstein_distance(a, b):
    '''
    This function will calculate the levenshtein distance between two input
    lists a and b

    params:
        a (List) : The first list you want to compare
        b (List) : The second strinlistg you want to compare

    returns:
        This function will return the distance between list a and b.

    example:
        a = 'stamp'
        b = 'stomp'
        lev_dist(a,b)
        >> 1.0
    '''

    # @lru_cache(None)  # for memorization
    def min_dist(s1, s2):

        if s1 == len(a) or s2 == len(b):
            return len(a) - s1 + len(b) - s2

        # no change required
        if a[s1] == b[s2]:
            return min_dist(s1 + 1, s2 + 1)

        return 1 + min(
            min_dist(s1, s2 + 1),      # insert character
            min_dist(s1 + 1, s2),      # delete character
            min_dist(s1 + 1, s2 + 1),  # replace character
        )

    return min_dist(0, 0)
