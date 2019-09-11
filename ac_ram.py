# -*- coding: utf-8 -*-


class Manager:

    def __init__(self, db_conn):
        self.users = db_conn.load_users()
        self.pairs = db_conn.load_pairs()
        self.queue = set()
