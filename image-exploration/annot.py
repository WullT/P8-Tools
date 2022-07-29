import json
import os
import random
import datetime
import fnmatch
from sqlitehelper import *
from tqdm import tqdm


class ImageList:
    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.files = [item for t in get_filepaths() for item in t]
        self.index = 0
        self.listlen = len(self.files)

    def update_filelist_by_selection(
        self,
        node_id=None,
        starttime_h=None,
        endtime_h=None,
        startdate=None,
        enddate=None,
        seen_unseen_not_sure=1,
    ):
        self.files = [
            item
            for t in get_filelist_by_selection(
                node_id,
                starttime_h,
                endtime_h,
                startdate,
                enddate,
                seen_unseen_not_sure,
            )
            for item in t
        ]
        print(len(self.files))
        self.index = 0

    def get_file_by_index(self, index):
        try:
            file = self.files[index]
            if file:
                return file
            else:
                return None
        except IndexError:
            return None

    def get_file(self):
        return self.get_file_by_index(self.index)

    def get_first_file(self):
        self.index = 0
        return self.get_file_by_index(self.index)

    def get_next_file(self):
        self.index += 1
        if self.index >= len(self.files):
            self.index = 0
        return self.get_file_by_index(self.index)

    def get_file_skip_forward(self, n):
        self.index += n
        if self.index >= len(self.files):
            self.index = 0
        return self.get_file_by_index(self.index)

    def get_file_skip_backward(self, n):
        self.index -= n
        if self.index < 0:
            self.index = len(self.files) - 1
        return self.get_file_by_index(self.index)

    def get_previous_file(self):
        self.index -= 1
        if self.index < 0:
            self.index = len(self.files) - 1
        return self.get_file_by_index(self.index)

    def get_random_file(self):
        self.index = random.randint(0, len(self.files) - 1)
        return self.get_file_by_index(self.index)

    def update_filelist(self):
        self.files = get_file_list(self.base_dir)


def get_file_list(base_dir):
    files = []
    i = 0
    for root, dirnames, filenames in os.walk(base_dir):
        for filename in fnmatch.filter(filenames, "*.jpg"):

            files.append(os.path.join(root, filename).replace("\\", "/"))
            i += 1
            if i % 1000 == 0:
                print(i, filename)
    print("Found", len(files), "files on path:", base_dir)
    return files


def update_db(base_path):
    files = get_file_list(base_path)
    if len(files) > 0:
        for i in tqdm(range(len(files))):
            files[i] = files[i].split(base_path)[1]

        insert_from_list(files)
        set_available_from_list(files)
    else:
        print("No files found on path: " + base_path)


def get_file_by_index(index):
    files = get_file_list()
    leng = len(files)
    if index >= leng:
        return None
    return files[index]


def get_metadata_from_filename(filename):
    if "/" in filename:
        filename = filename.split("/")[-1]
    node_id = filename.split("_")[0]
    date = filename.split("_")[1]
    date = date.split(".")[0]
    dt = datetime.datetime.strptime(date, "%Y-%m-%dT%H-%M-%SZ")
    return node_id, dt
