"""
Import runner
"""
import os
import sys
from optparse import OptionParser
from glob import glob
from sis import sis_import
from sis.sis_import import log
from django.db import connection, transaction
from sis.excel2csv import get_new_extension
from sis.convert import convert

ARGS = ('BARCODE_DIR', 'STUDENT_DIR', 'OUTFILE')
USAGE = """%%prog [options] %s

    Run the script that will create patron records from SIS and
    Student ID system data. BARCODE_DIR and STUDENT_DIR contain the
    Student ID system files (barcodes) and the Student Information
    System files respectively. Patron MARC records will be written to
    OUTFILE.
""" % ' '.join(ARGS)

parser = OptionParser(usage=USAGE)

parser.add_option('-v','--verbose', action="store_true", default=False,
                  help="Be verbose")
parser.add_option('-p', '--ptype', metavar='PTYPE', default=None,
                   help="Only process patron type PTYPE")

class ImportRunner(object):

    def __init__(self, barcode_dir, student_dir, outfile):
        """Convert input data (excel files) into csv
        files. barcode_dir and student_dir contain the Student ID
        system files (barcodes) and the Student Information System
        files respectively. Patron MARC records will be written to
        outfile."""
        log.info('Running with barcode files from %s' % (barcode_dir,))
        log.info('Running with student files from %s' % (student_dir,))
        self.barcodefiles = glob(os.path.join(barcode_dir, '*.xls'))
        log.info("Barcodes: %s" % (self.barcodefiles,))
        self.studentfiles = glob(os.path.join(student_dir, '*.xls'))
        log.info("Student Records: %s" % (self.studentfiles,))
        self.outfile = outfile
        self.barcodecsv = [get_new_extension(i,'.csv') for i in self.barcodefiles]
        self.studentcsv = [get_new_extension(i,'.csv') for i in self.studentfiles]
        self.metadata = {'barcodefiles': self.barcodefiles,
                         'studentfiles': self.studentfiles,}

    def _delete_proto(self):
        cursor = connection.cursor()
        cursor.execute("DELETE from sis_protobarcode;")
        cursor.execute("DELETE FROM sis_protostudent;")
        transaction.commit_unless_managed()
        
    def run(self, ptype=None):
        """Create/Update student records from csv files"""
        # We need to clear out ProtoStudent and ProtoBarcode
        self._delete_proto()
        convert(self.metadata)
        sis_import.do_barcodes(self.barcodecsv)
        sis_import.do_students(self.studentcsv)
        sis_import.normalize_students()
        sis_import.write_marc(self.outfile, ptype=ptype)
        return 0

if __name__ == '__main__':

    opts, args = parser.parse_args()
    if len(args) != len(ARGS):
        parser.print_help()
        sys.exit(2)
    ir = ImportRunner(barcode_dir = args[0],
                      student_dir = args[1],
                      outfile     = args[2])
    sys.exit(ir.run(opts.ptype))
