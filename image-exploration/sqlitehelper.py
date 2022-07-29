import sqlite3
import datetime
import time
import pandas as pd

from configuration import DB_PATH

def create_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS images (
            filename TEXT PK UNIQUE,
            path TEXT,
            node_id TEXT,
            date datetime,
            flower int,
            pollinator int,
            capture_type int,
            favorite int,
            available boolean
        )
        """
    )
    conn.commit()
    conn.close()

def create_annot_table():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS annot (
            filename TEXT,
            annot_id int,
            cx int,
            cy int,
            w int,
            h int,
            x0 int,
            y0 int,
            x1 int,
            y1 int,
            image_width int,
            image_height int,
            annot_type int
        )
        """
    )
    conn.commit()
    conn.close()


def get_annotated_filenames(annot_type=2):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        SELECT DISTINCT filename FROM annot where annot_type = ?
        """, (annot_type,),
    )
    data = c.fetchall()
    conn.close()
    if len(data) > 0:
        return data
    return None



def get_all_annotations(annot_type=2):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        SELECT * FROM annot where annot_type = ?
        """, (annot_type,),
    )
    data = c.fetchall()
    conn.close()
    if len(data) > 0:
        df = pd.DataFrame(
            data,
            columns=[
                "filename",
                "annot_id",
                "cx",
                "cy",
                "w",
                "h",
                "x0",
                "y0",
                "x1",
                "y1",
                "image_width",
                "image_height",
                "annot_type",
            ],
        )
        return df
    return None

create_db()
create_annot_table()

def select_annotations(filename, annot_type = None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if annot_type is None:
        c.execute(
            """
            SELECT * FROM annot WHERE filename = ?
            """,
            (filename,),
        )
    else:
        c.execute(
            """
            SELECT * FROM annot WHERE filename = ? and annot_type = ?
            """,
            (filename, annot_type),
        )
    data = c.fetchall()
    conn.close()
    if len(data) > 0:
        df = pd.DataFrame(
            data,
            columns=[
                "filename",
                "annot_id",
                "cx",
                "cy",
                "w",
                "h",
                "x0",
                "y0",
                "x1",
                "y1",
                "image_width",
                "image_height",
                "annot_type",
            ],
        )
        return df
    return None

def get_all_data_as_df():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        SELECT * FROM images order by date desc
        """
    )
    data = c.fetchall()
    conn.close()
    if len(data) > 0:
        df = pd.DataFrame(
            data,
            columns=[
                "filename",
                "path",
                "node_id",
                "date",
                "flower",
                "pollinator",
                "capture_type",
                "favorite",
                "available",
            ],
        )
        return df
    return None

def insert_annotation(filename, annot_id, cx, cy, w, h, x0, y0, x1, y1,image_width, image_height, annot_type=1):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        INSERT OR IGNORE INTO annot (filename, annot_id, cx, cy, w, h, x0, y0, x1, y1, image_width, image_height, annot_type)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        
        """,
        (filename, annot_id, cx, cy, w, h, x0, y0, x1, y1,image_width, image_height, annot_type),
    )
    conn.commit()
    conn.close()

def remove_annotations(filename, annot_type):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if annot_type is None:
        c.execute(
            """
            DELETE FROM annot WHERE filename = ?
            """,
            (filename,),
        )
    else:
        c.execute(
            """
            DELETE FROM annot WHERE filename = ? and annot_type = ?
            """,
            (filename, annot_type),
        )
    conn.commit()
    conn.close()

def insert_from_list(filenames):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    i = 0
    t0 = time.time()
    for filename in filenames:
        node_id, date = get_metadata_from_filename(filename)
        c.execute(
            """
                INSERT OR IGNORE INTO images (filename, path, node_id, date,flower, pollinator, capture_type, favorite, available)
                VALUES (?, ?, ?, ?,?,?,?,?,?)
                
                """,
            (filename.split("/")[-1], filename, node_id, date, None, None, None, None, True),
        )

        i += 1
        if i % 1000 == 0:
            conn.commit()
            print(time.time() - t0, i, filename)
    conn.close()

def set_available_from_list(filenames):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    i = 0
    t0 = time.time()
    for filename in filenames:
        c.execute(
            """
                UPDATE images SET available = true WHERE filename = ?
                """,
            (filename.split("/")[-1],),
        )
        i += 1
        if i % 100 == 0:
            conn.commit()
            print(time.time() - t0, i, filename)
    conn.close()

def get_categorized_as_df():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        SELECT * FROM images where flower is not null
        """
    )
    data = c.fetchall()
    conn.close()
    df = pd.DataFrame(
        data,
        columns=[
            "filename",
            "path",
            "node_id",
            "date",
            "flower",
            "pollinator",
            "capture_type",
            "favorite",
            "available",
        ],
    )
    return df


def insert_data(
    filename,
    path,
    node_id,
    date,
    flower=None,
    pollinator=None,
    capture_type=None,
    favourite=None,
):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        INSERT OR REPLACE INTO images (filename, path, node_id, date,  flower, pollinator, capture_type, favorite)
        VALUES (?, ?, ?, ?,?,?,?,?)
        
        """,
        (filename, path, node_id, date, flower, pollinator, capture_type, favourite),
    )
    conn.commit()
    conn.close()


def get_data():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        SELECT * FROM images order by date desc
        """
    )
    data = c.fetchall()
    conn.close()
    return data


def print_data():
    i = 0
    data = get_data()
    for row in data:
        print(i, row)
        i += 1


def get_counts():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        SELECT count(*) FROM images
        """
    )
    all_images = c.fetchone()[0]
    c.execute(
        """
        SELECT count(*) FROM images where available = 1
        """
    )
    available_images = c.fetchone()[0]
    conn.close()
    return {"all": all_images, "available": available_images}

def get_filepaths():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        SELECT path FROM images order by node_id, date asc
        """
    )
    data = c.fetchall()
    conn.close()
    return data


def check_if_exists(filename):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        SELECT flower FROM images WHERE filename = ?
        """,
        (filename,),
    )
    data = c.fetchall()
    conn.close()
    if len(data) > 0:
        print(data[0][0])
        return True, data[0][0]
    else:
        return False, None


def get_metadata_from_filename(filename):
    if "/" in filename:
        filename = filename.split("/")[-1]
    node_id = filename.split("_")[0]
    date = filename.split("_")[1]
    date = date.split(".")[0]
    # parse date from this format: 2021-06-26T11-04-04Z
    dt = datetime.datetime.strptime(date, "%Y-%m-%dT%H-%M-%SZ")
    return node_id, dt




def set_all_not_available():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        UPDATE images SET available = false
        """
    )
    conn.commit()
    conn.close()

def get_node_ids(include_unavailable=False):

    query = "SELECT DISTINCT node_id FROM images"
    if not include_unavailable:
        query += " WHERE available = true"
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute(
        query
    )
    data = c.fetchall()
    conn.close()
    return data


def get_filelist_by_selection(
    node_id=None,
    starttime_h=None,
    endtime_h=None,
    startdate=None,
    enddate=None,
    seen_unseen_not_sure=1,
):

    condition_string = ""
    if node_id is not None:
        if condition_string == "":

            condition_string += "WHERE node_id = '{}'".format(node_id)
        else:
            condition_string += " AND node_id = '{}'".format(node_id)
    if starttime_h is not None:
        starttime_h_str = str(starttime_h)+":00"
        if starttime_h<10:
            starttime_h_str = "0"+starttime_h_str

        if condition_string == "":
            condition_string += "WHERE strftime('%H:%M', date) >= '{}'".format(starttime_h_str)
        else:
            condition_string += " AND strftime('%H:%M', date) >= '{}'".format(starttime_h_str)
    if endtime_h is not None:
        endtime_h_str = str(endtime_h)+":00"
        if endtime_h<10:
            endtime_h_str = "0"+endtime_h_str
        if condition_string == "":
            condition_string += "WHERE strftime('%H:%M', date) <= '{}'".format(endtime_h_str)
        else:
            condition_string += " AND strftime('%H:%M', date) <= '{}'".format(endtime_h_str)

    if seen_unseen_not_sure == 2:
        if condition_string == "":
            condition_string += "WHERE flower IS NULL"
        else:
            condition_string += " AND flower IS NULL"
    if seen_unseen_not_sure == 3:
        if condition_string == "":
            condition_string += "WHERE flower IS NOT NULL"
        else:
            condition_string += " AND flower IS NOT NULL"
    if seen_unseen_not_sure == 4:
        if condition_string == "":
            condition_string += "WHERE flower = 0"
        else:
            condition_string += " AND flower = 0"
    if seen_unseen_not_sure == 5:
        if condition_string == "":
            condition_string += "WHERE favorite = 1"
        else:
            condition_string += " AND favorite = 1"
    
    if condition_string == "":
        condition_string = "WHERE available = true"
    else:
        condition_string += " AND available = true"

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    print(condition_string)

    c.execute(
        """
            SELECT path FROM images {} ORDER BY node_id, date asc
            """.format(
            condition_string
        )
    )
    data = c.fetchall()
    conn.close()
    return data

def set_favorite(filename, favorite):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        UPDATE images SET favorite = ? WHERE filename = ?
        """,
        (favorite, filename),
    )
    conn.commit()
    conn.close()

def set_flower(filename, flower):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        UPDATE images SET flower = ? WHERE filename = ?
        """,
        (flower, filename),
    )
    conn.commit()
    conn.close()


def get_counts_by_node_as_df():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    select node_id,
        count(*) ,
        count(flower),
        count(case flower when 1 then 1 else null end),
        count(case flower when 0 then 1 else null end),
        count(case flower when -1 then 1 else null end) 
        
        FROM images GROUP BY node_id
    """
    )
    data = c.fetchall()
    conn.close()
    df = pd.DataFrame(data, columns=["node_id", "count_images", "count_classified", "count_flower", "count_not_sure","count_no_flower"])
    return df

def get_image_dates_by_node_as_df(node_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    select distinct(strftime('%Y-%m-%d', date)) from images where node_id = ? order by date asc
    """,
    (node_id,)
    )
    data = c.fetchall()
    conn.close()
    df = pd.DataFrame(data, columns=["date"])
    return df

def get_data_by_node_as_df(node_id, excludeNaN=False):
    query = "SELECT * FROM images WHERE node_id = ?"
    if excludeNaN:
        query+=" AND flower IS NOT NULL"
    query+=" order by date asc"
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
       query,
        (node_id,),
    )
    data = c.fetchall()
    conn.close()
    df = pd.DataFrame(
        data,
        columns=[
            "filename",
            "path",
            "node_id",
            "date",
            "flower",
            "pollinator",
            "capture_type",
            "favorite",
            "available"
        ],
    )

    return df

def check_if_file_available(filename):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        SELECT available FROM images WHERE filename = ?
        """,
        (filename,),
    )
    data = c.fetchall()
    conn.close()
    if len(data) == 0:
        return False
    else:
        return data[0][0]

def get_path_from_filename(filename):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        SELECT path FROM images WHERE filename = ?
        """,
        (filename,),
    )
    data = c.fetchall()
    conn.close()
    if len(data) == 0:
        return None
    else:
        return data[0][0]