import re
import xlsxwriter

class Subtitles:

    app = None

    # parameterized constructor
    def __init__(self, data):
        self.app = data

    def parse_subtitles(self, lines):
        line_index = re.compile('^\d*$')
        line_timestamp = re.compile('^\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}$')
        line_separator = re.compile('^\s*$')

        current_record = {'index': None, 'timestamp': None, 'subtitles': []}
        state = 'seeking to next entry'

        for line in lines:
            line = line.strip('\n')
            if state == 'seeking to next entry':
                if line_index.match(line):
                    self.app.logger.debug('Found index: {i}'.format(i=line))
                    current_record['index'] = line
                    state = 'looking for timestamp'
                else:
                    self.app.logger.debug('HUH: Expected to find an index, but instead found: [{d}]'.format(d=line))

            elif state == 'looking for timestamp':
                if line_timestamp.match(line):
                    self.app.logger.debug('Found timestamp: {t}'.format(t=line))
                    current_record['timestamp'] = line
                    state = 'reading subtitles'
                else:
                    self.app.logger.debug('HUH: Expected to find a timestamp, but instead found: [{d}]'.format(d=line))

            elif state == 'reading subtitles':
                if line_separator.match(line):
                    self.app.logger.debug('Blank line reached, yielding record: {r}'.format(r=current_record))
                    yield current_record
                    state = 'seeking to next entry'
                    current_record = {'index': None, 'timestamp': None, 'subtitles': []}
                else:
                    self.app.logger.debug('Appending to subtitle: {s}'.format(s=line))
                    current_record['subtitles'].append(line)

            else:
                self.app.logger.debug('HUH: Fell into an unknown state: `{s}`'.format(s=state))
        if state == 'reading subtitles':
            # We must have finished the file without encountering a blank line. Dump the last record
            yield current_record

    def write_dict_to_worksheet(self, columns_for_keys, keyed_data, worksheet, row):
        """
        Write a subtitle-record to a worksheet.
        Return the row number after those that were written (since this may write multiple rows)
        """
        current_row = row
        # First, horizontally write the entry and timecode
        for (colname, colindex) in columns_for_keys.items():
            if colname != 'subtitles':
                worksheet.write(current_row, colindex, keyed_data[colname])

        # Next, vertically write the subtitle data
        subtitle_column = columns_for_keys['subtitles']
        # for morelines in keyed_data['subtitles']:

        subs = ''

        for sub in keyed_data['subtitles']:
            subs += sub + '\n'

        worksheet.write(current_row, subtitle_column, subs.rstrip())
        current_row += 1

        return current_row

    def convert(self, input_filename, output_filename):
        workbook = xlsxwriter.Workbook(output_filename)
        worksheet = workbook.add_worksheet('subtitles')
        columns = {'index': 0, 'timestamp': 1, 'subtitles': 2}

        next_available_row = 0
        records_processed = 0
        headings = {'index': "Entries", 'timestamp': "Timecodes", 'subtitles': ["Subtitles"]}
        next_available_row =self.write_dict_to_worksheet(columns, headings, worksheet, next_available_row)

        with open(input_filename, encoding='utf8') as textfile:
            for record in self.parse_subtitles(textfile):
                next_available_row = self.write_dict_to_worksheet(columns, record, worksheet, next_available_row)
                records_processed += 1

        self.app.logger.info(
            'Done converting {inp} to {outp}. {n} subtitle entries found. {m} rows written'.format(inp=input_filename,
                                                                                                   outp=output_filename,
                                                                                                   n=records_processed,
                                                                                                   m=next_available_row))
        workbook.close()