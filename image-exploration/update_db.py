from annot import *
from configuration import BASE_PATH

print("updating DB")
print("set_all_not_available()")
set_all_not_available()
print("update_db from BASE_PATH", BASE_PATH)
update_db(BASE_PATH)

print("available node id's:", get_node_ids())
