def create_walk_forward_splits(df, train_size, test_size, step_size):

    splits = []
    start = 0
    n = len(df)

    while start + train_size + test_size <= n:

        train_idx = list(range(start, start + train_size))
        test_idx  = list(range(start + train_size,
                               start + train_size + test_size))

        splits.append((train_idx, test_idx))

        start += step_size

    return splits
