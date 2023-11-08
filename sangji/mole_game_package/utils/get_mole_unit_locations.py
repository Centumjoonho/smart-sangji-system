
def get_grid_unit_distace(frame, divide_unit) -> tuple:
    r'''입력받은 배경화면에 격자를 그리고, 
    격자에 해당하는 가로 길이와 세로 길이를 
    추출하여 tuple로 리턴합니다.
    
    Args:
        frame [image]: cv2.imread() image, used for molegame background
        divide_unit [int]: the number after dividing baground image
            Examples:
                1. if 'dividie_unit' is two, 
                    we will divde the background image 2 x 2 grids
                2. if 'divide_unit' is three,
                    we will divde the background image 3 x 3 grids
                3. ans so forth
    
    Return:
        unit_distance [tuple]: unit distance, (unit_dist_x, unit_dist_y)
            all unitdistances between grids should be same
    '''
    
    # pos_x, pos_y = loc[0], loc[1]
    frame_height, frame_width, _ = frame.shape

    # Calculate unit-distance
    unit_dist_x = int(frame_width / divide_unit)
    unit_dist_y = int(frame_height / divide_unit)

    return (unit_dist_x, unit_dist_y)


def get_grid_locations(frame, divide_unit) -> list:
    r'''입력받은 배경화면에 격자를 그리고, 
        격자에 해당하는 좌표를 추출하여 list로 리턴합니다.
    
    Args:
        frame [image]: cv2.imread() image, used for molegame background
        divide_unit [int]: the number after dividing baground image
            Examples:
                1. if 'dividie_unit' is two, 
                    we will divde the background image 2 x 2 grids
                2. if 'divide_unit' is three,
                    we will divde the background image 3 x 3 grids
    
    Returns:
        unit_map [list]: the list of tuples
            each element (tuple) of the list is consisted of two Tuple
    
    Return example:
        [((x_0, y_0),(x_1, y_1)), ...]
        x_i: the condinate x of starting point of i-th grid
        y_i: the condinate x of starting point of i-th grid
        The grid numger 'i-th' grid is the index of this list
    '''

    # pos_x, pos_y = loc[0], loc[1]
    frame_height, frame_width, _ = frame.shape

    # Calculate unit-distance
    unit_dist_x = frame_width / divide_unit
    unit_dist_y = frame_height / divide_unit

    unit_dist_x_list = [unit_dist_x] * divide_unit
    unit_dist_y_list = [unit_dist_y] * divide_unit

    # Get mole grid ID
    x_list = []
    for x, unit_x in enumerate(unit_dist_x_list):
        x_start = x * unit_x
        x_end = x_start + unit_x
        x_list.append((x_start, x_end))

    y_list = []
    for y, unit_y in enumerate(unit_dist_y_list):
        y_start = y * unit_y
        y_end = y * unit_y + unit_y
        y_list.append((y_start, y_end))

    unit_map = []
    for y_range in y_list:
        for x_range in x_list:
            unit_map.append((x_range, y_range))

    return unit_map

