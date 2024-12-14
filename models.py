import json

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class Note(Base):
    __tablename__ = 'note'

    id = Column(Integer, primary_key=True)
    content = Column(String)
    user_id = Column(Integer, ForeignKey('user.id'))


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    f_name = Column(String)
    password = Column(String)
    email = Column(String)
    notes = relationship('Note')

    def toJSON(self):
        return json.dumps(
            self,
            default=lambda o: o._asdict(),
            sort_keys=True,
            indent=4)

