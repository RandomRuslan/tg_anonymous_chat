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


class ChatT(Base):
    """
    userid1 < userid2
    """

    __tablename__ = 'chats'

    id = sa.Column(sa.INT, primary_key=True, autoincrement=True)
    userid1 = sa.Column(sa.INT, nullable=False)
    userid2 = sa.Column(sa.INT, nullable=False)
    startts = sa.Column(sa.DATETIME)
    finishts = sa.Column(sa.DATETIME, default=None)


class DBConnecter:
    def __init__(self):
        self.engine = sa.create_engine(DB_URL)
        self.DBSession = sessionmaker(bind=self.engine)

    def create_user(self, id, username, gender, preference):
        user = UserT(
            id=id,
            username=username,
            gender=gender,
            preference=preference
        )
        self._store(user)

    def create_chat(self, user1, user2):
        user1, user2 = sorted([user1, user2])
        start_ts = datetime.now().replace(microsecond=0)

        chat = ChatT(
            userid1=user1,
            userid2=user2,
            startts=start_ts
        )
        self._store(chat)

    def close_chat(self, user1, user2):
        user1, user2 = sorted([user1, user2])
        finish_ts = datetime.now().replace(microsecond=0)

        session = self.DBSession()
        try:
            session.query(ChatT).\
                filter(sa.and_(ChatT.userid1 == user1, ChatT.userid2 == user2)).\
                update({'finishts': finish_ts})

            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()

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

    def load_users(self):
        users = {}

        session = self.DBSession()
        rows = session.query(UserT).all()
        for row in rows:
            users[row.id] = {
                'gender': row.gender,
                'preference': row.preference
            }

        session.close()
        return users

    def load_pairs(self):
        pairs = {}

        session = self.DBSession()
        rows = session.query(ChatT).filter(ChatT.finishts == None).all()
        for row in rows:
            if row.userid1 not in pairs and row.userid2 not in pairs:
                pairs[row.userid1] = row.userid2
                pairs[row.userid2] = row.userid1

        return pairs
