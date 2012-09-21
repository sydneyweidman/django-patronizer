"""unicodecsv.py Unicode csv reader"""
import csv

def unicode_csv_reader(utf8_data, dialect=csv.excel, **kwargs):
    csv_reader = csv.reader(utf8_data, dialect=dialect, **kwargs)
    for row in csv_reader:
        yield [unicode(cell, 'utf-8') for cell in row]

def unicode_csv_dictreader(utf8_data, fieldnames=None, restkey=None, restval=None, dialect='excel', *args, **kwds):
    dictreader = csv.DictReader(utf8_data, fieldnames=fieldnames, restkey=restkey,
                                restval=restval, dialect=dialect, *args, **kwds)
    for row in dictreader:
        for k,v in row.iteritems():
            row[k] = unicode(row[k], 'utf-8')
        yield row
