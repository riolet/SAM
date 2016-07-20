import dbaccess


def setup():
    dbaccess.create_database()
    # add any other setup tasks here

    print("\n--- Setup completed successfully ---")


if __name__ == "__main__":
    setup()
