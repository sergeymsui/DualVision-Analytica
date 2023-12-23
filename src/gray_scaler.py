

import os
import cv2

from os import listdir
from os.path import isfile, join

images = []
file_paths = []

def load(path):
    onlyfiles = [f for f in listdir(path) if isfile(join(path, f))]
    
    global file_paths
    
    file_paths = [str(n) for n in onlyfiles]
    file_paths.sort()
    os.chdir(path)
    for image in file_paths:
        images.append(cv2.imread(image))

    if file_paths.__len__() == images.__len__():
        print("== READY ==")

def main():
    load("./data/RGB")

    os.chdir("../../data/GRY/")

    for i in range(images.__len__()):
        path = file_paths[i]
        # path = path.replace('jpg', 'png')
        frame_rgb = images[i]

        gray_frame_rgb = cv2.cvtColor(frame_rgb, cv2.COLOR_BGR2GRAY)
        flag = cv2.imwrite(path, gray_frame_rgb)

        print(path, flag)
    

if __name__ == "__main__":
    main()