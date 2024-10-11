from colour import Color


def evaluate_color(percentage):
    red = Color("#ff0D0D")
    yellow = Color("#FAB733")
    green = Color("#69B34C")

    # 25 entries
    gradient = list(red.range_to(yellow, 15)) + \
        list(yellow.range_to(green, 10))

    index = int(percentage / 100 * 24)
    return gradient[index].get_hex()
