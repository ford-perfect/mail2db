from flask import session
from sqlalchemy import Column, DateTime, Boolean, Integer, String, ForeignKey, Table, create_engine
from sqlalchemy.orm import relationship, declarative_base, Session, mapped_column, Mapped

Base = declarative_base()


to = Table('to', Base.metadata,
           Column('contact_id', String(50), ForeignKey('contact.email')),
    Column('message_id', Integer, ForeignKey('message.id'))
)
cc = Table('cc', Base.metadata,
    Column('contact_id', String(50), ForeignKey('contact.email')),
    Column('message_id', Integer, ForeignKey('message.id'))
)
bcc = Table('bcc', Base.metadata,
    Column('contact_id', String(50), ForeignKey('contact.email')),
    Column('message_id', Integer, ForeignKey('message.id'))
)

class Contact(Base):
    __tablename__ = 'contact'
    name = Column(String(50), nullable=False)
    email = mapped_column(String(50), nullable=False, primary_key=True)
    phone = Column(String(50), nullable=True)
    address = Column(String(50), nullable=True)
    to_relationship = relationship('Message', secondary=to, back_populates='to')
    cc_relationship = relationship('Message', secondary=cc, back_populates='cc')
    bcc_relationship = relationship('Message', secondary=bcc, back_populates='bcc')

class EmailFolder(Base):
    __tablename__ = 'emailFolder'
    id = Column(Integer, nullable=False, primary_key=True, autoincrement=True)
    sub = Column(String(100), nullable=False, unique=True)
    processed = Column(Boolean, nullable=False, default=False)
class Message(Base):
    __tablename__ = 'message'
    id = mapped_column(Integer, nullable=False, primary_key=True, autoincrement=True)
    ffrom = Column(Integer, ForeignKey('contact.email'), nullable=False)
    to = relationship('Contact', secondary=to, back_populates='to_relationship')
    cc = relationship('Contact', secondary=cc, back_populates='cc_relationship')
    bcc = relationship('Contact', secondary=bcc, back_populates='bcc_relationship')
    subject = Column(String(50), nullable=False)
    body = Column(String(1500), nullable=False)
    attachmentNumber = Column(Integer, nullable=True)
    spam = Column(Integer, nullable=True)
    read = Column(Integer, nullable=True)
    date = Column(DateTime, nullable=False)
    filepath = Column(String(150), nullable=True, unique=True)

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
    import datetime
    engine = create_engine('sqlite:///test.db')
    Base.metadata.create_all(engine)
    c1 = Contact(name='John', email='john@example.com')
    q1 = PromptQuestions(question='What is your name?')
    with Session(engine) as ok:
        ok.add(c1)
        ok.add(q1)
        ok.commit()
        m1 = Message(ffrom=c1.email, subject='Hello', body='Hello World', date=datetime.now())
        m1.to.append(c1)
        m1.cc.append(c1)
        m1.bcc.append(c1)
        d1 = Question(question=q1.id, contact=c1.email, response='John')
        ok.add(m1)
        ok.add(d1)
        ok.commit()
