"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""
import os
from glob import glob
from django.test import TestCase
from sis import sis_import
from sis.excel2csv import get_new_extension
from sis.convert import convert
from sis.models import Student, ProtoBarcode, ProtoStudent, PatronType

curdir = os.path.dirname(os.path.abspath(__file__))
datadir = os.path.join(curdir,'testdata')
barcode_dir = os.path.join(datadir,'barcodes')
student_dir = os.path.join(datadir, 'students')

class SimpleTest(TestCase):

    def setUp(self):
        self.barcodefiles = glob(os.path.join(barcode_dir, '*.xls'))
        self.studentfiles = glob(os.path.join(student_dir, '*.xls'))
        self.barcodecsv = [get_new_extension(i,'.csv') for i in self.barcodefiles]
        self.studentcsv = [get_new_extension(i,'.csv') for i in self.studentfiles]
        self.metadata = {'barcodefiles': self.barcodefiles,
                         'studentfiles': self.studentfiles,}

    def test_write_marc_utf8(self):
        """Make sure we can write unicode to utf-8"""
        sis_import.write_marc('/tmp/testdata.lfts','2')

    def test_convert(self):
        """Test converting xls files to csv"""
        convert(self.metadata)
        for f in self.studentcsv:
            assert os.path.isfile(f)
        for f in self.barcodecsv:
            assert os.path.isfile(f)

    def test_patron_types(self):
        """Check that we have all the right patron types"""
        ptypes = PatronType.objects.all()
        assert len(ptypes) == 3
        for i in ptypes:
            assert i.pcode in ['uow', 'col', 'grad']

    def test_student_model(self):
        """Make sure the student model works as expected"""
        ptype = PatronType.objects.get(ptype='1')
        student = Student(student_id = '3025768', first_name = 'john', last_name = 'smith', ptype=ptype)
        assert student.first_name == 'john'
        student.save()
        
    def test_create_student_recs(self):
        """Test generating student records from csv files"""
        convert(self.metadata)
        sis_import.do_barcodes(self.barcodecsv)
        assert len(ProtoBarcode.objects.all())
        sis_import.do_students(self.studentcsv)
        assert len(ProtoStudent.objects.all())
        sis_import.normalize_students()
        assert len(Student.objects.all())
        sis_import.write_marc('/tmp/testdata.lfts')
        
    def tearDown(self):
        try:
            os.unlink('/tmp/testdata.lfts')
        except OSError:
            pass
        for d in [student_dir, barcode_dir]:
            for i in glob(os.path.join(d, '*.csv')):
                try:
                    os.unlink(i)
                except OSError:
                    pass

