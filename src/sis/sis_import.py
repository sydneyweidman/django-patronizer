import os
import sys
import logging
from sis.unicodecsv import unicode_csv_dictreader as DictReader
from pymarc import MARCWriter
from django.db import transaction, IntegrityError
from django.db.models import Max
from sis.models import ProtoStudent, ProtoBarcode, Student, PatronType
from sis.utils import get_next_date, calc_checkdigit
from django.core.validators import ValidationError

def get_ptype_for_file(sisfile):
    """If the filename is numeric, return the digit(s) as a str. If
    non-numeric, use a ptype map. KeyError will be raised if the name
    of the file isn't found"""
    b = os.path.splitext(sisfile)[0]
    fname = os.path.basename(b)
    log.info('Getting patron type from filename %s' % (fname,))
    if fname.isdigit() and fname in [i.ptype for i in PatronType.objects.all()]:
        return fname
    else:
        return PatronType.objects.filter(pcode__exact=fname)[0]

exp_date = get_next_date(8,31)

log = logging.getLogger(__name__)
logging.basicConfig()
log.setLevel(logging.INFO)

def write_marc(outfile, ptype=None):
    """Write Student MARC records to outfile"""
    ecount = count = 0
    writer = MARCWriter(open(outfile,'w'))
    if ptype:
        # filter on patron type
        students = Student.objects.filter(ptype=ptype)
    else:
        students = Student.objects.all()
    for s in students:
        try:
            writer.write(s.as_marc())
            count += 1
        except (TypeError, UnicodeDecodeError, UnicodeEncodeError), e:
            log.info("%s: %s" % (s.student_id,s.full_name()))
            log.info("%s" % (s.as_marc().as_marc(),))
            log.exception("Error: %s" % (e,))
            ecount += 1
    log.info("Valid records: %s" % (count,))
    log.info("Invalid records: %s" % (ecount,))
    
@transaction.commit_on_success()
def do_barcodes(barcodefiles):
    """Load data from one or more barcode files"""
    for b in barcodefiles:
        barcodefile = DictReader(open(b))
        for row in barcodefile:
            barcode = ProtoBarcode(**row)
            try:
                barcode.barcode += calc_checkdigit(barcode.barcode)
            except ValueError:
                log.warn('File: %s Value: %s Invalid barcode' % (b, barcode.barcode))
                continue
            try:
                barcode.full_clean()
                barcode.save()
            except ValidationError, e:
                for key in e.message_dict:
                    log.debug("File: %s Value: %s" % (b, barcode.barcode,))
                    log.debug("%s: %s" % (key, e.message_dict[key],))
                continue
            
@transaction.commit_on_success()
def do_students(studentfiles):
    """Load data from one or more student files"""
    for s in studentfiles:
        ptype = get_ptype_for_file(s)
        studentfile = DictReader(open(s))
        for row in studentfile:
            student = ProtoStudent(**row)
            student.ptype = ptype
            try:
                student.clean_fields(exclude=['email_address','created'])
                try:
                    student.save()
                except IntegrityError:
                    pass
            except ValidationError, e:
                log.warn('File: %s Error: %s' % (s, student.student_id,))
                for key in e.message_dict:
                    log.warn("%s: %s" % (key, e.message_dict[key],))
                continue

@transaction.commit_on_success()
def normalize_students(ptype=None):
    """Normalize the data from the import file. Pre: multiple records
    with the same student_id, one for each different email and
    phone. Post: Email and Phone have been saved to related records
    and student_id is unique"""
    if not ptype:
        students = ProtoStudent.objects.values('student_id')
    else:
        subset = ProtoStudent.objects.filter(ptype=ptype)
        students = subset.values('student_id')
    stlist = [s['student_id'] for s in students]
    stlist = list(set(stlist))
    stlist.sort()
    for student in stlist:
        recs = ProtoStudent.objects.filter(student_id=student)
        if not ptype:
            # if we're not specifying a ptype, it is possible that
            # recs contains records with different patron types
            rank = recs.aggregate(rank=Max('ptype__rank'))['rank']
            ptype = recs.filter(ptype__rank=rank)[0].ptype
        proto = recs[0]
        barcodes = ProtoBarcode.objects.filter(person_num=student).aggregate(Max('barcode'))
        barcode = barcodes['barcode__max']
        phones = [(r.telephone_type, r.telephone1) for r in recs if not r.telephone1.isspace()]
        emails = [(r.email_type, r.email_address, r.preferred_email) for r in recs]
        phones = list(set(phones))
        emails = list(set(emails))

        # Construct MARC record base
        s = Student()
        s.student_id = student
        s.first_name = proto.first_name
        s.last_name = proto.last_name
        s.street_address = proto.street_address
        s.city = proto.city
        s.province = proto.province
        s.postal_code = proto.postal_code
        log.debug("%s, %s" % (student,barcode))
        try:
            s.telephone_1 = phones[0][1]
            s.telephone_2 = phones[1][1]
        except IndexError:
            if s.telephone_1 is None:
                s.telephone_1 = u''
            if s.telephone_2 is None:
                s.telephone_2 = u''
        for t,e,p in emails:
            if t.upper() == 'UWE':
                uwe = e
        s.email_address = uwe
        s.barcode = barcode
        s.ptype = ptype
        try:
            s.clean_fields(exclude=['created'])
        except ValidationError, e:
            for key in e.message_dict:
                log.info("%s: %s" % (key, e.message_dict[key],))
        s.save()
        
if __name__ == '__main__':

    if sys.argv[1] == 'students':
        do_students(sys.argv[2:])
    elif sys.argv[1] == 'barcodes':
        do_barcodes(sys.argv[2:])
    elif sys.argv[1] == 'normalize':
        try:
            normalize_students(sys.argv[2])
        except IndexError:
            normalize_students()
    elif sys.argv[1] == 'marc':
        try:
            write_marc(sys.argv[2], sys.argv[3])
        except IndexError:
            write_marc(sys.argv[2])
