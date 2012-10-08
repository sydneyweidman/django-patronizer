"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""
import os
import re
from csv import DictReader
from sis.unicodecsv import unicode_csv_reader as csvreader
from cStringIO import StringIO
from datetime import datetime
from pytz import utc
from glob import glob
from django.test import TestCase
from django.db import IntegrityError
from sis import sis_import
from sis.excel2csv import get_new_extension
from sis.convert import convert
from sis.models import Student, ProtoBarcode, ProtoStudent, PatronType
from sis.unoservice import UnoService, Options

curdir = os.path.dirname(os.path.abspath(__file__))
datadir = os.path.join(curdir,'testdata')
barcode_dir = os.path.join(datadir,'barcodes')
student_dir = os.path.join(datadir, 'students')
env = dict(PYTHONPATH=os.getenv('PYTHONPATH'), PATH=os.getenv('PATH'))

student_id_pattern = re.compile('\d{7}')

bcdata = """"barcode","card_format","station","operator","card_issued_to","person_num"
,,,,,
2188800107388,"Students","INFOCENTER-05","photoid","W. KELLIE MAYO",1163427
2188800107389,"Students","INFOCENTER-05","photoid","RICARDO JOAQUIN BRAVO IZQUIERDO",3048077
2188800107390,"Students","INFOCENTER-05","photoid","CARA BARTZ-EDGE","STAFF"
2188800107391,"Students","INFOCENTER-05","photoid","SHAYAN MIRHOSSEINI",3046632
2188800107392,"Students","INFOCENTER-05","photoid","ZHANAY SAGINTAYEV",3046636
2188800107393,"Students","INFOCENTER-05","photoid","ZIRDUM ANTO",1004324
2188800107394,"Students","INFOCENTER-05","photoid","LIDIYA PURTOVA",3048456
2188800107394,"Students","INFOCENTER-05","photoid","LIDIYA PURTOVA",3048456
2188800107395,"Students","INFOCENTER-05","photoid","EUSEBIO MANGONON",3048270
2188800107396,"Students","INFOCENTER-05","photoid","JANNA BARKMAN",1161235
2188800107397,"Students","INFOCENTER-05","photoid","LUPITA RODRIGUEZ",3047331
2188800107398,"Students","INFOCENTER-05","photoid","MUBAMBE TSHIANI",3047898
2188800107399,"Students","INFOCENTER-05","photoid","DANIEL HERPAI",3047886
381,"Bee Clean Staff ID","INFOCENTER-05","photoid","GHEBRESTINSAE ARAYA","BEE CLEAN"
"""

protobarcodes = DictReader(StringIO(bcdata))

class TestUnoService(TestCase):

    def setUp(self):
        self.instance = UnoService()
        self.defaults = UnoService.defaults
        self.options = Options(self.defaults['options'])
        self.env = env

    def test_options(self):
        """Check that the command line flags are properly handled"""
        for i in self.defaults['options']:
            assert getattr(self.options, i)

    def test_default_accept(self):
        """Make sure the accept string is set correctly"""
        assert self.instance.accept == self.defaults['accept'].format(host=self.defaults['host'],
                                                                      port=self.defaults['port'])

    def test_connect_string(self):
        """Make sure the connect string is set correctly"""
        assert self.instance.connectstr == self.defaults['connectstr'].format(host=self.defaults['host'],
                                                                      port=self.defaults['port'])
    def test_start_and_connect(self):
        """Make sure LibreOffice starts"""
        pid = self.instance.start()
        assert pid > 0
        desktop = self.instance.connect(try_start=False)
        assert desktop is not None

    def tearDown(self):
        try:
            self.instance.terminate()
        except:
            pass
        
class TestSis(TestCase):

    fixtures = ['patrontypes.json']

    def setUp(self):
        self.barcodefiles = glob(os.path.join(barcode_dir, '*.xls'))
        self.samplebarcodes = protobarcodes
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

    def test_student_model_insert(self):
        """Make sure the student model insert works as expected"""
        ptype = PatronType.objects.get(ptype='1')
        student = Student(student_id = '3025768', first_name = 'john', last_name = 'smith', ptype=ptype)
        assert student.first_name == 'john'
        student.save()
        
    def test_student_model_update(self):
        """Make sure the student model update works as expected"""
        ptype = PatronType.objects.get(ptype='1')
        student = Student(student_id = '3025768', first_name = 'john', last_name = 'smith', ptype=ptype)
        assert student.first_name == 'john'
        student.save()
        st2 = Student(student_id = '3025768', first_name = 'bill', last_name = 'smith', ptype=ptype)
        st2.save()
        bill = Student.objects.get(student_id='3025768')
        assert bill.first_name == 'bill'
        
    def test_student_model_created(self):
        """Make sure the student model auto_add_now works as expected
        for the created field"""
        now = datetime.now(tz=utc)
        ptype = PatronType.objects.get(ptype='1')
        student = Student(student_id = '3025768', first_name = 'john', last_name = 'smith', ptype=ptype)
        assert student.created is None
        student.save()
        assert student.created > now
        
    def test_student_model_modified(self):
        """Make sure the student model auto_add_now works as expected
        for the created field"""
        ptype = PatronType.objects.get(ptype='1')
        student = Student(student_id = '3025768', first_name = 'john', last_name = 'smith', ptype=ptype)
        student.save()
        t1 = student.created
        st2 = Student(student_id = '3025768', first_name = 'bill', last_name = 'smith', ptype=ptype, created=t1)
        st2.save()
        bill = Student.objects.get(student_id='3025768')
        assert bill.modified > t1
        
    def test_protobarcode_model_insert(self):
        """We should be able to insert ProtoBarcode records"""
        for i in self.samplebarcodes:
            if i['barcode']:
                bc = ProtoBarcode(**i)
                try:
                    bc.save()                    
                except IntegrityError, e:
                    if e.message.endswith(u'not unique'):
                        pass
                    else:
                        print "Problem with barcode %s" % (i['barcode'],)
                        print "Error: %s" % (e,)
        assert len(ProtoBarcode.objects.all()) == 13

    def test_create_student_recs(self):
        """Test generating student records from csv files"""
        convert(self.metadata)
        sis_import.do_barcodes(self.barcodecsv)
        assert len(ProtoBarcode.objects.all())
        sis_import.do_students(self.studentcsv)
        assert len(ProtoStudent.objects.all())
        sis_import.normalize_students()
        # compare ptype from csv to ptype in ProtoStudent
        ptype = sis_import.get_ptype_for_file('uow.csv')
        uowcsv = csvreader(open(os.path.join(student_dir,'uow.csv')))
        for row in uowcsv:
            if not student_id_pattern.match(row[0]):
                continue
            ps = ProtoStudent.objects.filter(student_id=row[0])[0]
            try:
                assert ps.ptype == ptype
            except AssertionError:
                import pdb; pdb.set_trace()
        # check that records from ProtoStudent have the same ptype as
        # the corresponding record in Student
        uow = ProtoStudent.objects.filter(ptype=ptype)
        for r in uow:
            s = Student.objects.get(student_id=r.student_id)
            assert s.ptype == ptype 
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

