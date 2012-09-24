# $Id: master.py 348 2012-09-14 15:23:38Z sweidman $
"""Master run script for Patron Load"""
import os
import sys
import uno
from glob import glob
from com.sun.star.lang import DisposedException
from sis.excel2csv import modify_sid, modify_sis, get_desktop
        
def convert(metadata, **kwargs):
    """Convert SIS and Student ID xls files to csv files, then convert
    them to marc files. metadata parameter should consist of two keys:
    studentfiles and barcodefiles, with the value of each key being a
    list of student or barcode files respectively"""
    ret = 0
    host = kwargs.get('host','localhost')
    port = kwargs.get('port', 2002)
    desktop = get_desktop(host, port)
    for b in metadata['barcodefiles']:
        b = os.path.abspath(os.path.expanduser(b))
        if not os.path.isfile(b):
            sys.stderr.write("File not found: %s\n" % (b,))
            return 3
        modify_sid(b, desktop=desktop, terminate=False)
    for s in metadata['studentfiles']:
        s = os.path.abspath(os.path.expanduser(s))
        if not os.path.isfile(s):
            sys.stderr.write("File not found: %s\n" % (s,))
            return 3
        modify_sis(s, desktop=desktop, terminate=False)
    if desktop:
        try:
            desktop.terminate()
        except DisposedException:
            pass
    return ret

if __name__ == '__main__':

    barcode_dir, student_dir = [os.path.expanduser(i) for i in sys.argv[1:]]
    barcodefiles = glob(os.path.join(barcode_dir, '*.xls'))
    studentfiles = glob(os.path.join(student_dir, '*.xls'))
    metadata = {'barcodefiles':barcodefiles,
                'studentfiles':studentfiles,}
    sys.exit(convert(metadata=metadata))

