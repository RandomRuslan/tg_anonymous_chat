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

    def create_user(self, user_id, username, gender, preference):
        user = UserT(
            id=user_id,
            username=username,
            gender=gender,
            preference=preference
        )
        self._store(user)

    def update_user(self, user_id, preference):
        session = self.DBSession()
        try:
            session.query(UserT).filter(UserT.id == user_id).update({'preference': preference})
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()

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
        session = self.DBSession()
        rows = session.query(UserT).all()
        session.close()

        for row in rows:
            yield {'id': row.id, 'gender': row.gender, 'preference': row.preference}

    def load_pairs(self):
        session = self.DBSession()
        rows = session.query(ChatT).filter(ChatT.finishts == None).all()
        session.close()

        for row in rows:
            yield (row.userid1, row.userid2)
