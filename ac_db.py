import json
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from constants import DB_URL


Base = declarative_base()


class UserT(Base):
    __tablename__ = 'users'

    id = sa.Column(sa.INT, primary_key=True)
    username = sa.Column(sa.VARCHAR(64), nullable=False)
    gender = sa.Column(sa.VARCHAR(2))
    preference = sa.Column(sa.VARCHAR(2))
    prev_partners = sa.Column(sa.TEXT)
    partner = sa.Column(sa.INT, default=None)   # 0 - in queue


class MessageT(Base):
    """
    chat_id = userid1_userid2
    userid1 < userid2

    sender = userid
    """

    __tablename__ = 'messages'

    id = sa.Column(sa.INT, primary_key=True)
    chat_id = sa.Column(sa.VARCHAR(64), nullable=False)
    sender = sa.Column(sa.INT)
    kind = sa.Column(sa.VARCHAR(64), nullable=False)
    content = sa.Column(sa.TEXT, nullable=False)
    creation_ts = sa.Column(sa.DATETIME)


# class ChatT(Base):
#     """
#     userid1 < userid2
#     """
#
#     __tablename__ = 'chats'
#
#     id = sa.Column(sa.INT, primary_key=True, autoincrement=True)
#     userid1 = sa.Column(sa.INT, nullable=False)
#     userid2 = sa.Column(sa.INT, nullable=False)
#     startts = sa.Column(sa.DATETIME)
#     finishts = sa.Column(sa.DATETIME, default=None)


class DBConnecter:

    def __init__(self):
        self.engine = sa.create_engine(DB_URL)
        self.DBSession = sessionmaker(bind=self.engine)

    def store_user(self, user_id, username, gender, preference):
        user = UserT(
            id=user_id,
            username=username,
            gender=gender,
            preference=preference
        )
        self._store(user)

    def update_user(self, user_id, updated_data):
        session = self.DBSession()
        try:
            session.query(UserT).filter(UserT.id == user_id).update(updated_data)
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()

    def store_message(self, user1, user2, content, kind='text'):
        message = MessageT(
            chat_id='_'.join(sorted([str(user1), str(user2)])),
            sender=user1,
            kind=kind,
            content=content,
            creation_ts=datetime.now().replace(microsecond=0)
        )

        self._store(message)

    # def create_chat(self, user1, user2):
    #     user1, user2 = sorted([user1, user2])
    #     start_ts = datetime.now().replace(microsecond=0)
    #
    #     chat = ChatT(
    #         userid1=user1,
    #         userid2=user2,
    #         startts=start_ts
    #     )
    #     self._store(chat)

    # def close_chat(self, user1, user2):
    #     user1, user2 = sorted([user1, user2])
    #     finish_ts = datetime.now().replace(microsecond=0)
    #
    #     session = self.DBSession()
    #     try:
    #         session.query(ChatT).\
    #             filter(sa.and_(ChatT.userid1 == user1, ChatT.userid2 == user2)).\
    #             update({'finishts': finish_ts})
    #
    #         session.commit()
    #     except:
    #         session.rollback()
    #         raise
    #     finally:
    #         session.close()

    def _store(self, obj):
        session = self.DBSession()
        try:
            session.add(obj)
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()

    def load_user_by_id(self, user_id):
        session = self.DBSession()
        row = session.query(UserT).filter(UserT.id == user_id).first()
        session.close()

        return DBConnecter._user_row_to_dict(row) if row else None

    def load_users(self):
        session = self.DBSession()
        rows = session.query(UserT).filter(UserT.partner != None).all()
        session.close()

        for row in rows:
            yield DBConnecter._user_row_to_dict(row)

    @staticmethod
    def _user_row_to_dict(user):
        return {
            'id': user.id,
            'gender': user.gender,
            'preference': user.preference,
            'prev_partners': json.loads(user.prev_partners) if user.prev_partners else [],
            'partner': user.partner
        }

    # def load_pairs(self):
    #     session = self.DBSession()
    #     rows = session.query(ChatT).filter(ChatT.finishts == None).all()
    #     session.close()
    #
    #     for row in rows:
    #         yield (row.userid1, row.userid2)
