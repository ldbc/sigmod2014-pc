from pygraphblas import *


def pattern_vec(vec):
    res=Vector.from_type(BOOL, vec.size)
    vec.apply(BOOL.ONE, out=res)
    return res


def naive_bfs_levels(matrix, source):
    '''
    Input:
        matrix: adjacency matrix describing the graph
        source: source node index
    Returns:
        result_vector: vector of hops to all other nodes
    '''

    result_vector = Vector.from_type(UINT64, matrix.nrows)
    known_nodes_vector = Vector.from_type(BOOL, matrix.nrows)

    known_nodes_vector[source] = True
    not_done = True
    level = 1

    while not_done and level <= matrix.nrows:
        result_vector[:, known_nodes_vector] = level
        known_nodes_vector = result_vector.vxm(matrix, mask=result_vector, desc=descriptor.ooco)
        not_done = known_nodes_vector.reduce_bool()
        level += 1
    return result_vector


def naive_bfs_parents(matrix, source):
    '''
    Input:
        matrix: adjacency matrix describing the graph
        source: source node index
    Returns:
        parent_vertices_vector: parent vertices vector
    '''
    wavefront_vector = Vector.from_type(INT64, matrix.nrows)
    vertex_index_vector = Vector.from_list([x for x in range(matrix.nrows)])
    parent_vertices_vector = Vector.from_type(INT64, matrix.nrows)
    wavefront_vector[source] = source
    level = 1
    not_done = True
    print(F'SOURCE: {source}')
    while not_done and level <= matrix.nrows:
        parent_vertices_vector_boolean_1 = pattern_vec(parent_vertices_vector)
        with semiring.MIN_FIRST:
            parent_vertices_vector = wavefront_vector.vxm(matrix, mask=parent_vertices_vector_boolean_1, desc=descriptor.ooco)
        parent_vertices_vector_boolean_2 = pattern_vec(parent_vertices_vector)
        wavefront_vector = vertex_index_vector.emult(parent_vertices_vector_boolean_2, mask=parent_vertices_vector_boolean_1.vector[0], desc=descriptor.ooco)
        level += 1
        not_done = wavefront_vector.reduce_bool()
    return parent_vertices_vector


def push_pull_bfs_levels(matrix, source):
    level = 1
    push = True

    result_vector = Vector.from_type(UINT64, matrix.nrows)
    frontier_vector = Vector.from_type(BOOL, matrix.nrows)
    frontier_vector[source] = True

    # Heuristic to decide if we need to switch between push and pull
    r_before = frontier_vector.nvals / matrix.nrows
    # Threshold to switch between push and pull
    threshold = 0.2

    not_done = True
    while not_done and level <= matrix.nrows:
        result_vector[:, frontier_vector] = level

        if (push):
            with semiring.ANY_PAIR:
                next_vector = frontier_vector.vxm(matrix, mask=result_vector, desc=descriptor.ooco)
        if (not push):
            with semiring.ANY_PAIR:
                next_vector = matrix.mxv(frontier_vector, mask=result_vector, desc=descriptor.ooco)

        frontier_vector = next_vector

        r = frontier_vector.nvals / matrix.nrows

        if r > r_before and r > threshold: push = False
        if r < r_before and r < threshold: push = True

        r_before = r

        not_done = frontier_vector.reduce_bool()
        level += 1

    return result_vector


def msbfs_levels(matrix, sourceVertices):
    frontier = sourceVertices
    resultMatrix = Matrix.from_type(UINT64,sourceVertices.nrows,sourceVertices.ncols)
    level = 0
    not_done = True
    while not_done and level < matrix.nrows:
        resultMatrix.assign_scalar(level,mask=frontier)
        with semiring.LOR_LAND_BOOL:
            frontier = frontier.mxm(matrix,mask=resultMatrix.pattern(),desc=descriptor.ooco)
        not_done = frontier.reduce_bool()
        level += 1
    return resultMatrix


def push_pull_msbfs_levels(matrix, sourceVertices):
    frontier = sourceVertices
    resultMatrix = Matrix.from_type(UINT64, sourceVertices.nrows, sourceVertices.ncols)
    level = 0
    not_done = True
    push = True

    # Heuristic to decide if we need to switch between push and pull
    r_before = frontier.nvals / (matrix.nrows * sourceVertices.nrows)
    # Threshold to switch between push and pull
    threshold = 0.2

    while not_done and level < matrix.nrows:
        resultMatrix.assign_scalar(level, mask=frontier)

        if push:
            with semiring.ANY_PAIR:
                frontier = frontier.mxm(matrix, mask=resultMatrix.pattern(), desc=descriptor.ooco)
        if not push:
            with semiring.ANY_PAIR:
                frontier = matrix.mxm(frontier, mask=resultMatrix.pattern(), desc=descriptor.ooco)

        r = frontier.nvals / (matrix.nrows * sourceVertices.nrows)

        if r > r_before and r > threshold: push = False
        if r < r_before and r < threshold: push = True

        r_before = r

        not_done = frontier.reduce_bool()
        level += 1
    return resultMatrix


def bidirectional_bfs(matrix, src_idx1, src_idx2):
    # If we want to start the BFS from the same two nodes, the length of path is 0
    if src_idx1 == src_idx2:
        return 0

    node_count = matrix.ncols
    frontier1 = Vector.from_lists([src_idx1], [True], node_count)
    frontier2 = Vector.from_lists([src_idx2], [True], node_count)
    seen1 = frontier1
    seen2 = frontier2
    for level in range(1, node_count // 2):
        # frontier 1
        next1 = seen1.vxm(matrix, mask=seen1, desc=descriptor.ooco)
        # emptied the component of src1
        if next1.nvals == 0:
            return -1

        # has frontier1 intersected frontier2's previous state?
        intersection1 = next1 * seen2
        if intersection1.nvals > 0:
            return level * 2 - 1

        # frontier 2
        next2 = seen2.vxm(matrix, mask=seen2, desc=descriptor.ooco)
        # emptied the component of src2
        if next2.nvals == 0:
            return -1

        # do frontier1 and frontier2's current states intersect?
        intersection2 = next1 * next2
        if intersection2.nvals > 0:
            return level * 2

        seen1 = seen1 + next1
        seen2 = seen2 + next2


