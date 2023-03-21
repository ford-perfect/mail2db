import os
import sqlite3
import time
import emlx
import csv
import re
import email
#import pymysql
#
from datetime import datetime
from model import Contact, Message, PromptQuestions, Question, Base, EmailFolder
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy import exc as sa_exc
import tqdm

import warnings
people  = {}
log_file = open('log.txt', 'w')
header_regex = re.compile(r'^(?P<name>[^<]*)<(?P<email>[^>]*)>$')

def insert_contact(session, name, email):
    # db_contact = session.query(Contact).filter_by(email=email).first()
    # if not db_contact:
    db_contact = Contact(name=name, email=email)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=sa_exc.SAWarning)
        try:
            session.add(db_contact)
            session.commit()
        except sa_exc.IntegrityError:
            session.rollback()
            db_contact = session.query(Contact).filter_by(email=email).first()
            log_file.write(f"Duplicate entry for {email} with name {name} and {db_contact.name}")
    return db_contact
    if db_contact.name != name:
        log_file.write(f"For {email}, previously known as {db_contact.name} is a.k.a. {name}")
    return db_contact

def insert_message(session, msg, ffrom, to, cc, bcc, date, filepath):
    body = ''
    for part in msg.walk():
        if part.get_content_type() == 'text/plain':
            body = part.get_payload(decode=True).decode(part.get_content_charset())
            break
    e_message = Message(
        ffrom = ffrom.email,
        subject = msg.headers['Subject'],
        body = body,
        date = date,
        filepath = filepath
    )
    for contact in to:
        e_message.to.append(contact)
    for contact in cc:
        e_message.cc.append(contact)
    for contact in bcc:
        e_message.bcc.append(contact)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=sa_exc.SAWarning)
        try:
            session.add(e_message)
            session.commit()
        except sa_exc.IntegrityError:
            session.rollback()
            log_file.write(f"Duplicate entry for {msg.headers['Subject']} from {ffrom.email} on {date}")

def get_dt(date_string):
    fmt =  '%a, %d %b %Y %H:%M:%S %z'
    dt = None
    try:
        dt = datetime.strptime(date_string, fmt)
    except ValueError as v:
        ulr = len(v.args[0].partition('unconverted data remains: ')[2])
        try:
            if ulr > 0:
                dt = datetime.strptime(date_string[:-ulr], fmt)
            else:
                dt = datetime.now()
                log_file.write(f"Could not parse date {date_string} for {file_path} using {fmt} so using {dt}, url = {ulr}")
        except ValueError as w:
                dt = datetime.now()
                log_file.write(f"Could not parse date {date_string} for {file_path} using {fmt} so using {dt}, second try")
    return dt
def extract_headers(session, file_path):
    msg = emlx.read(file_path)
    date_string = msg.headers['Date']
    dt = get_dt(date_string, file_path)
    subject = msg.headers['Subject']
    to = []
    cc = []
    bcc = []
    ffrom = None
    for header in ['From', 'To', 'Bcc', 'Cc']:
        if header in msg.headers:
            for email in msg.headers[header].split(','):
                match = header_regex.match(email)
                name = ''
                if match:
                    name = match.group('name').strip()
                    email = match.group('email')
                email = email.strip()
                contact = insert_contact(session, name, email)
                if(header == 'To'):
                    to.append(contact)
                elif header == 'Cc':
                    cc.append(contact)
                elif header == 'Bcc':
                    bcc.append(contact)
                elif header == 'From':
                    ffrom = contact
    insert_message(session, msg, ffrom, to, cc, bcc, dt, file_path)


def write_to_csv(file_name):
    data = []
    for p in people:
        data.append({
            'name':people[p]['Name'],
            'email':p,
            'from':people[p]['From'],
            'to':people[p]['To'],
            'last date':people[p]['Last Date'].strftime('%Y-%m-%d'),
            'subject':people[p]['Subject'],
            'first date':people[p]['First Date'].strftime('%Y-%m-%d')
            })
    with open(file_name, 'w', newline='') as csvfile:
        fieldnames = data[0].keys()
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            writer.writerow(row)
def walk_sub(sub, session):

    emailFolder = session.query(EmailFolder).filter_by(sub=sub).first()
    if not emailFolder:
        emailFolder = EmailFolder(sub=sub)
        session.add(emailFolder)
        session.commit()
    if emailFolder.processed:
        return

    for root, dirs, files in os.walk(sub):
        for file in files:
            if file.endswith('.emlx') and not re.match(r"\._.*$", file):
                file_path = os.path.join(root, file)
                headers = extract_headers(session, file_path)
    emailFolder = session.query(EmailFolder).filter_by(sub=sub).first()
    emailFolder.processed = True
    session.commit()

def main():
    engine  = create_engine('sqlite:///output.db')

    Base.metadata.create_all(engine)
    data_path = "data"
    with Session(engine) as session:
    # Iterate over files in subdirectory
        # Iterate over the two top level folder
        subs = []
        max_path = 0
        for s1 in os.listdir(data_path):
            f1 = os.path.join(data_path, s1)
            if os.path.isdir(f1):
                for s2 in os.listdir(f1):
                    f2 = os.path.join(f1, s2)
                    if os.path.isdir(f2):
                        subs.append(f2)
                        max_path = max(max_path, len(f2))
        max_path -= len(data_path)
        progress_bar = tqdm.tqdm(total=len(subs), desc="Progress")
        progress_bar.desc = f"{'Starting'.ljust(max_path,' ')}"
        for sub in subs:
            #progress_bar.pos = i
            # time.sleep(2)
            progress_bar.unit = "Folder"
            sub_text = sub[len(data_path):] if sub.startswith(data_path) else sub
            progress_bar.desc = f"{sub_text.ljust(max_path,' ')}"
            progress_bar.update()
            walk_sub(sub, session)
        progress_bar.desc = f"{'Finished'.ljust(max_path,' ')}"
        # for loop with index
        #List of top-level directories>>

        #            insert_headers(headers, conn)
    # write_to_csv('kontakte.csv')

if __name__ == '__main__':
    main()
