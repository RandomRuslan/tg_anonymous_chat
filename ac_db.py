import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from constants import DB_URL


Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = sa.Column(sa.INT, primary_key=True)
    username = sa.Column(sa.VARCHAR(64), nullable=False)
    gender = sa.Column(sa.VARCHAR(2))
    preference = sa.Column(sa.VARCHAR(2))


class DBConnecter:
    def __init__(self):
        self.engine = sa.create_engine(DB_URL)
        self.DBSession = sessionmaker(bind=self.engine)

    def create_user(self, id, username, gender, preference):
        session = self.DBSession()
        user = User(
            id=id,
            username=username,
            gender=gender,
            preference=preference
        )
        try:
            session.add(user)
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()

    def load_users(self):
        users = {}

        session = self.DBSession()
        rows = session.query(User).all()
        for row in rows:
            users[row.id] = {
                'gender': row.gender,
                'preference': row.preference
            }

        session.close()
        return users
