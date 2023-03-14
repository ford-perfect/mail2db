from flask import session
from sqlalchemy import Column, DateTime, Integer, String, ForeignKey, Table, create_engine
from sqlalchemy.orm import relationship, declarative_base, Session

Base = declarative_base()

class Contact(Base):
    __tablename__ = 'contact'
    name = Column(String(50), nullable=False)
    email = Column(String(50), nullable=False, primary_key=True)
    phone = Column(String(50), nullable=True)
    address = Column(String(50), nullable=True)

to = Table('to', Base.metadata,
    Column('contact', Integer, ForeignKey('contact.email'), primary_key=True),
    Column('message', Integer, ForeignKey('message.id'), primary_key=True)
)
cc = Table('cc', Base.metadata,
    Column('contact', Integer, ForeignKey('contact.email'), primary_key=True),
    Column('message', Integer, ForeignKey('message.id'), primary_key=True)
)
bcc = Table('bcc', Base.metadata,
    Column('contact', Integer, ForeignKey('contact.email'), primary_key=True),
    Column('message', Integer, ForeignKey('message.id'), primary_key=True)
)

class Message(Base):
    __tablename__ = 'message'
    id = Column(Integer, nullable=False, primary_key=True, autoincrement=True)
    ffrom = Column(Integer, ForeignKey('contact.email'), nullable=False)
    to = relationship('Contact', secondary=to)
    cc = relationship('Contact', secondary=cc)
    bcc = relationship('Contact', secondary=bcc)
    subject = Column(String(50), nullable=False)
    body = Column(String(1500), nullable=False)
    attachmentNumber = Column(Integer, nullable=True)
    spam = Column(Integer, nullable=True)
    read = Column(Integer, nullable=True)
    date = Column(DateTime, nullable=False)


class PromptQuestions(Base):
    __tablename__ = 'promptQuestions'
    id = Column(Integer, nullable=False, primary_key=True, 
    autoincrement=True)
    question = Column(String(50), nullable=False)
    moreDetailedQuestion = Column(String(50), nullable=True)

class Question(Base):
    __tablename__ = 'question'
    question = Column(Integer, ForeignKey('promptQuestions.id'), primary_key=True, nullable=False)
    contact = Column(Integer, ForeignKey('contact.email'), primary_key=True, nullable=False) 
    response = Column(String(50), nullable=False)


if __name__ == '__main__':
    engine = create_engine('sqlite:///test.db')
    Base.metadata.create_all(engine)
    c1 = Contact(name='John', email='john@example.com')
    q1 = PromptQuestions(question='What is your name?')
    with Session(engine) as ok:
        ok.add(c1)
        ok.add(q1)
        ok.commit()
        m1 = Message(ffrom=c1.id, subject='Hello', body='Hello World')
        m1.to.append(c1)
        m1.cc.append(c1)
        m1.bcc.append(c1)
        d1 = Question(question=q1.id, contact=c1.id, response='John')
        ok.add(m1)
        ok.add(d1)
        ok.commit()