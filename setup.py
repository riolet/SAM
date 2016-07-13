import dbaccess


def setup():
    dbaccess.create_database()
    # add any other setup tasks here


if __name__ == "__main__":
    setup();
