from dbmanager import DbManager

if __name__ == "__main__":

    dbm = DbManager(
        url="https://canvas-f06e2-default-rtdb.europe-west1.firebasedatabase.app"
    )
    dbm.serve_requests()
