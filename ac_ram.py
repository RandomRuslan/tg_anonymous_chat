# -*- coding: utf-8 -*-


class Manager:
    users = None
    pairs = None
    queue = None

    def __init__(self, db_conn):
        self.users = db_conn.load_users()
        self.pairs = {}
        self.queue = set()
