'''
My own implementations of functions found in the python
library itertools (https://docs.python.org/3/library/itertools.html) and a QuickSort algorithm
'''

def chain(*iters):
    """
    Appends iterables together and yields each element in sequence

    Yields:
        Any: Each element of the joined-up iterable
    """    
    
    # Soure code taken from:
    # https://python.plainenglish.io/python-itertools-chain-a-deep-dive-26ee5513274e
    for iter in iters:
        for elem in iter:
            yield elem

'''
def product(*iters, repeat=1):
    # Pseudocode from https://docs.python.org/3/library/itertools.html
    tuple_iters = list(map(tuple, iters)) * repeat
    output = [[]]
    
    for iter in tuple_iters:
        output = [curr_prod + [val] for curr_prod in output for val in iter]
    
    for prod in output:
        yield tuple(prod)
'''
 
def combinations(iterable, r):
    """
    Gets all the unique combinations (of length r) of the elements in an iterable

    Args:
        iterable (Iter): The iterable we want to get the combinations from
        r (Int): Length of each combination

    Yields:
        Tuple: A combination
    """    
    # Developed using code from https://docs.python.org/3/library/itertools.html
    if type(r) is not int:
        raise TypeError("r must be an int")
    
    pool = tuple(iterable)
    n = len(pool)
    
    if r > n:
        return
    
    # The indices of the elements from the input iterable in the current combination
    indices = list(range(r))
    
    # Return the most obvious combination (0, 1, 2 ..., r) 
    yield tuple(pool[i] for i in indices)
    
    while True:
        # The final combination is (n-r, n-r+1, ... n)
        # If indices is the above combination, then we have found all combinations
        # The indices of the above combination also indicate the max index that
        # element in the indices list can reach
        for i in reversed(range(r)):
            # By iterating backwards, we increment combinations from right to left
            # When one figure has reached its max, we reset it and increment the one to its left
            # (similar to counting a multi-digit number)
            if indices[i] != i + n - r:
                break
        else:
            return
        
        indices[i] += 1
        
        for j in range(i + 1, r):
            indices[j] = indices[j - 1] + 1
        
        yield tuple(pool[i] for i in indices)

def quickSort(inp_list, key=lambda x: x):
    """
    Implementation of the quick sort algorithm with a key function feature

    Args:
        inp_list (List): The list to be sorted
        key (Func, optional): Maps inp_list to a list of values that we want to sort by. Defaults to lambdax:x.

    Returns:
        List: sorted list
    """    
    # Algorithm from https://www.geeksforgeeks.org/quick-sort/
    if len(inp_list) <= 1:
        return inp_list
    
    keyed_list = list(map(key, inp_list))
    
    pivot = keyed_list[-1]
    left_list = []
    right_list = []
    
    for (i, elem) in enumerate(keyed_list):
        if elem < pivot:
            left_list.append(inp_list[i])
        elif elem > pivot:
            right_list.append(inp_list[i])
        elif elem == pivot and i != len(inp_list) - 1:
            left_list.append(inp_list[i])
    
    return quickSort(left_list, key) + [inp_list[-1]] + quickSort(right_list, key)
    
def deepCopy(data_struct):
    '''
    Creates a copy of everything in a data structure
    '''
    if type(data_struct) is set:
        if type(list(data_struct)[0]) not in [list, set, dict, tuple]:
            return data_struct.copy()
        else:
            return {deepCopy(item) for item in data_struct}
    elif type(data_struct) in [list, tuple]:
        try:
            if type(data_struct[0]) not in [list, set, dict, tuple]:
                try:
                    return data_struct.copy()
                except AttributeError:
                    return data_struct
            else:
                return [deepCopy(item) for item in data_struct]
        except IndexError:
            try:
                return data_struct.copy()
            except AttributeError:
                    return data_struct
    elif type(data_struct) is dict:
        if type(list(data_struct.values())[0]) not in [list, set, dict, tuple]:
            return data_struct.copy()
        else:
            return {key : deepCopy(data_struct[key]) for key in data_struct}
    else:
        return data_struct