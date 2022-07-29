import shutil
from sqlitehelper import *
from configuration import BASE_PATH
from PIL import Image
import os

IMAGE_SAVE_PATH = "exported_images/"
LABEL_SAVE_PATH = "exported_labels/"
IMAGE_RESOLUTION = 1280

files = [i[0] for i in get_annotated_filenames(2)]
files_t3 = [i[0] for i in get_annotated_filenames(3)]
files_t4 = [i[0] for i in get_annotated_filenames(4)]

for file in files_t3:
    if file not in files:
        print("file is not in files:", file)
        files.append(file)

for file in files_t4:
    if file not in files:
        print("file is not in files:", file)
        files.append(file)

existing_files = [i for i in os.listdir(IMAGE_SAVE_PATH)]
for existing_file in existing_files:
    files.remove(existing_file)
print(files)

# print("files:", files)
def generate_labels(files):
    for fn in files:
        if check_if_file_available(fn):
            try:
                print("file is available:", fn)
                annots = select_annotations(fn, 2)
                annots_type_3 = select_annotations(fn, 3)
                annots_type_4 = select_annotations(fn, 4)
                has_da = False
                has_wm = False
                has_fl = False
                print("annots:", annots)
                print("annots_type_3:", annots_type_3)
                lines = []
                if annots is not None:
                    if len(annots) == 0:
                        print("no annotations t2 found for", fn)
                    else:
                        has_da = True
                        # iterate over rows
                        for index, row in annots.iterrows():
                            image_height = row["image_height"]
                            image_width = row["image_width"]
                            cx = row["cx"]
                            cy = row["cy"]
                            w = row["w"]
                            h = row["h"]
                            cy_norm = cy / image_height
                            cx_norm = cx / image_width
                            w_norm = w / image_width
                            h_norm = h / image_height

                            print(
                                row["cx"],
                                row["cy"],
                                row["w"],
                                row["h"],
                                row["image_width"],
                                row["image_height"],
                            )
                            print(cx_norm, cy_norm, w_norm, h_norm)
                            lines.append(
                                "0 "
                                + str(cx_norm)
                                + " "
                                + str(cy_norm)
                                + " "
                                + str(w_norm)
                                + " "
                                + str(h_norm)
                            )
                if annots_type_3 is not None:
                    print("found annotations t3 for", fn)
                    print(annots_type_3)
                    if len(annots_type_3) == 0:
                        print("no annotations t3 found for", fn)
                    else:
                        has_wm = True
                        for index, row in annots_type_3.iterrows():
                            image_height = row["image_height"]
                            image_width = row["image_width"]
                            cx = row["cx"]
                            cy = row["cy"]
                            w = row["w"]
                            h = row["h"]
                            cy_norm = cy / image_height
                            cx_norm = cx / image_width
                            w_norm = w / image_width
                            h_norm = h / image_height

                            print(
                                row["cx"],
                                row["cy"],
                                row["w"],
                                row["h"],
                                row["image_width"],
                                row["image_height"],
                            )
                            print(cx_norm, cy_norm, w_norm, h_norm)
                            lines.append(
                                "1 "
                                + str(cx_norm)
                                + " "
                                + str(cy_norm)
                                + " "
                                + str(w_norm)
                                + " "
                                + str(h_norm)
                            )
                if annots_type_4 is not None:
                    print("found annotations t4 for", fn)
                    print(annots_type_4)
                    if len(annots_type_4) == 0:
                        print("no annotations t4 found for", fn)
                    else:
                        has_fl = True
                        for index, row in annots_type_4.iterrows():
                            image_height = row["image_height"]
                            image_width = row["image_width"]
                            cx = row["cx"]
                            cy = row["cy"]
                            w = row["w"]
                            h = row["h"]
                            cy_norm = cy / image_height
                            cx_norm = cx / image_width
                            w_norm = w / image_width
                            h_norm = h / image_height

                            print(
                                row["cx"],
                                row["cy"],
                                row["w"],
                                row["h"],
                                row["image_width"],
                                row["image_height"],
                            )
                            print(cx_norm, cy_norm, w_norm, h_norm)
                            lines.append(
                                "2 "
                                + str(cx_norm)
                                + " "
                                + str(cy_norm)
                                + " "
                                + str(w_norm)
                                + " "
                                + str(h_norm)
                            )

                if len(lines) > 0:
                    with open(LABEL_SAVE_PATH + fn.split(".jpg")[0] + ".txt", "w") as f:
                        f.write("\n".join(lines))
                    print(
                        "wrote",
                        len(lines),
                        "lines to",
                        LABEL_SAVE_PATH + fn.split(".jpg")[0] + ".txt",
                    )
            except Exception as e:
                print("error:", e)
                print("file is not available:", fn)
                pass
        else:
            print("file is not available:", fn)


def resize_image(img, size):
    w, h = img.size
    if w > h:
        h = int(h * size / w)
        w = size
    else:
        w = int(w * size / h)
        h = size
    img = img.resize((w, h), Image.ANTIALIAS)
    print(img.size)
    return img


def copy_files(files):
    for fn in files:
        try:
            if check_if_file_available(fn):
                img = Image.open(BASE_PATH + get_path_from_filename(fn))
                img = resize_image(img, IMAGE_RESOLUTION)
                img.save(IMAGE_SAVE_PATH + fn)
            else:
                print("file is not available:", fn)
        except Exception as e:
            print("error:", e)
            print("file is not available:", fn)
            pass


generate_labels(files)

copy_files(files)
