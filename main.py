import base64
import logging
import os
import re
import shutil
import time
import sys
import codecs

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (Mail, Attachment, FileContent, FileName, FileType, Disposition)


import xlsxwriter
from flask import Flask, render_template, request, redirect

ALLOWED_EXTENSIONS = {'srt'}
OUTPUT_FOLDER = 'output'
OUTPUT_FOLDER_ARCHIVE = 'archives'


app = Flask(__name__)
app.config.from_pyfile('settings.py')
app.secret_key = 'YOUR KEY'


UPLOAD_FOLDER = app.config.get("UPLOAD_FOLDER")
FROM_EMAIL = app.config.get("FROM_EMAIL")
TO_EMAIL= app.config.get("TO_EMAIL")

app.logger.info(UPLOAD_FOLDER)



def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/process', methods=('GET', 'POST'))
def process():

    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            app.logger.info('No file part')
            return redirect(request.url)

        if not os.path.exists(OUTPUT_FOLDER):
            os.mkdir(OUTPUT_FOLDER)

        if not os.path.exists(OUTPUT_FOLDER_ARCHIVE):
            os.mkdir(OUTPUT_FOLDER_ARCHIVE)

        app.logger.info("adadas " + UPLOAD_FOLDER)

        for f in request.files.getlist('file'):
            f.save(os.path.join(UPLOAD_FOLDER, f.filename))
            convert(input_filename='uploads/' + f.filename, output_filename='output/' + f.filename +'.xls')

        zip_filename = 'output_' + str(int(time.time())) + '.zip'
        shutil.make_archive(zip_filename, 'zip', 'output')

        shutil.rmtree(OUTPUT_FOLDER)

        message = Mail(from_email=FROM_EMAIL,
                        to_emails=TO_EMAIL,
                        subject='Here is your information',
                        html_content='<strong>Please find information attached.</strong>')

        with open(zip_filename + '.zip', 'rb') as f:
            data = f.read()
            f.close()
        encoded_file = base64.b64encode(data).decode()

        attachedFile = Attachment(
            FileContent(encoded_file),
            FileName(zip_filename),
            FileType('application/zip'),
            Disposition('attachment')
        )
        message.attachment = attachedFile


        sendgrid_key = app.config.get("SENDGRID_SECRET")
        sg = SendGridAPIClient(sendgrid_key)
        response = sg.send(message)
        app.logger.info(response.status_code, response.body, response.headers)

        return render_template('processed.html')



def parse_subtitles(lines):

    line_index = re.compile('^\d*$')
    line_timestamp = re.compile('^\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}$')
    line_separator = re.compile('^\s*$')

    current_record = {'index':None, 'timestamp':None, 'subtitles':[]}
    state = 'seeking to next entry'

    for line in lines:
        line = line.strip('\n')
        if state == 'seeking to next entry':
            if line_index.match(line):
                app.logger.debug('Found index: {i}'.format(i=line))
                current_record['index'] = line
                state = 'looking for timestamp'
            else:
                app.logger.debug('HUH: Expected to find an index, but instead found: [{d}]'.format(d=line))

        elif state == 'looking for timestamp':
            if line_timestamp.match(line):
                app.logger.debug('Found timestamp: {t}'.format(t=line))
                current_record['timestamp'] = line
                state = 'reading subtitles'
            else:
                app.logger.debug('HUH: Expected to find a timestamp, but instead found: [{d}]'.format(d=line))

        elif state == 'reading subtitles':
            if line_separator.match(line):
                app.logger.debug('Blank line reached, yielding record: {r}'.format(r=current_record))
                yield current_record
                state = 'seeking to next entry'
                current_record = {'index':None, 'timestamp':None, 'subtitles':[]}
            else:
                app.logger.debug('Appending to subtitle: {s}'.format(s=line))
                current_record['subtitles'].append(line)

        else:
            app.logger.debug('HUH: Fell into an unknown state: `{s}`'.format(s=state))
    if state == 'reading subtitles':
        # We must have finished the file without encountering a blank line. Dump the last record
        yield current_record

def write_dict_to_worksheet(columns_for_keys, keyed_data, worksheet, row):
    """
    Write a subtitle-record to a worksheet.
    Return the row number after those that were written (since this may write multiple rows)
    """
    current_row = row
    #First, horizontally write the entry and timecode
    for (colname, colindex) in columns_for_keys.items():
        if colname != 'subtitles':
            worksheet.write(current_row, colindex, keyed_data[colname])

    #Next, vertically write the subtitle data
    subtitle_column = columns_for_keys['subtitles']
    #for morelines in keyed_data['subtitles']:

    subs = ''

    for sub in keyed_data['subtitles']:
         subs+= sub + '\n'


    worksheet.write(current_row, subtitle_column, subs.rstrip())
    current_row+=1

    return current_row

def convert(input_filename, output_filename):

    workbook = xlsxwriter.Workbook(output_filename)
    worksheet = workbook.add_worksheet('subtitles')
    columns = {'index':0, 'timestamp':1, 'subtitles':2}

    next_available_row = 0
    records_processed = 0
    headings = {'index':"Entries", 'timestamp':"Timecodes", 'subtitles':["Subtitles"]}
    next_available_row=write_dict_to_worksheet(columns, headings, worksheet, next_available_row)

    with open(input_filename, encoding='utf8') as textfile:
        for record in parse_subtitles(textfile):
            next_available_row = write_dict_to_worksheet(columns, record, worksheet, next_available_row)
            records_processed += 1

    app.logger.info('Done converting {inp} to {outp}. {n} subtitle entries found. {m} rows written'.format(inp=input_filename, outp=output_filename, n=records_processed, m=next_available_row))
    workbook.close()
