"""
testing MapIO loading and exporting
"""
import os
import random
import sys
from common.amap import BitMapIOMixin, TextMapIOMixin, MapRef, MapSetting

x_len = 15
y_len = 20


def main():
    print(os.path.dirname(__file__))
    convert_text_to_binary("map-2.txt")


def test_random_map():
    map_io = BitMapIOMixin()
    print("before saving the map")
    map_arr = random_map()
    map_io.save_map("D:/1.txt", map_arr)
    saved_map = map_io.load_map("D:/1.txt")
    print("Read the saved map")
    print_2d(saved_map)


def random_map():
    random_arr = [[random.choice([MapRef.UNKNOWN, MapRef.CLEAR, MapRef.OBSTACLE])
                   for _ in range(x_len)] for __ in range(y_len)]
    print_2d(random_arr)
    return random_arr


def convert_text_to_binary(filename):
    text_io = TextMapIOMixin()
    arr = text_io.load_map(filename)
    bin_file_name = filename.replace(".txt", ".bin")
    bin_io = BitMapIOMixin()
    bin_io.save_map(bin_file_name, td_array=arr)


def print_2d(arr):
    for y in range(len(arr)):
        for x in range(len(arr[0])):
            sys.stdout.write("{},".format(arr[y][x]))
        print()


main()