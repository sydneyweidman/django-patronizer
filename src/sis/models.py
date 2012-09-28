from django.db import models
from django.core.validators import RegexValidator
from pymarc.record import Record
from pymarc.field import Field
from sis.utils import get_next_date

# Create your models here.

exp_date = get_next_date(8,31)

HOMELIB_DEFAULT = 'uw'

SNLEN = 7

student_id_validator = RegexValidator('\d{%d}' % (SNLEN,), message="Student numbers must be %d digits long" % (SNLEN,))
barcode_validator = RegexValidator('\d{13,14}', message="Barcodes must be 14 digits long")

class PatronType(models.Model):
    ptype = models.CharField("patron type", max_length=2, primary_key=True)
    pcode = models.CharField("patron code", max_length=5)
    pdesc = models.CharField("patron description", max_length=50)

    def __unicode__(self):
        return self.pcode
    
class Student(models.Model):

    student_id = models.CharField(max_length=SNLEN, primary_key=True, validators=[student_id_validator])
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    street_address = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    province = models.CharField(max_length=50, null=True, blank=True)
    postal_code = models.CharField(max_length=50, null=True, blank=True)
    email_address = models.CharField(max_length=100, null=True, blank=True)
    telephone_1 = models.CharField(max_length=20, null=True, blank=True)
    telephone_2 = models.CharField(max_length=20, null=True, blank=True)    
    barcode = models.CharField(max_length=15, null=True, blank=True)
    ptype = models.ForeignKey(PatronType)
    created = models.DateField(auto_now_add=True)
    modified = models.DateField(auto_now=True)

    def full_name(self):
        """Get the name as required for innopac"""
        return u"%s, %s" % (self.last_name, self.first_name)

    def get_address(self):
        """Return address2 Patron MARC field:
        street_address$city prov$postal code
        """
        address = u"%s$%s %s$%s" % (self.street_address,
                                   self.city,
                                   self.province,
                                   self.postal_code)
        return address
    
    def as_marc(self):
        """Return a MARC21 representation of this person"""
        record = Record(force_utf8=True)
        record.add_field(Field(tag=u'080',
                               indicators=[u' ',u' '],
                               subfields=[u'a', exp_date]))
        record.add_field(Field(tag=u'084',
                               indicators=[u' ',u' '],
                               subfields=[u'a', self.ptype.ptype]))
        record.add_field(Field(tag=u'085',
                               indicators=[u' ',u' '],
                               subfields=[u'a', HOMELIB_DEFAULT]))
        record.add_field(Field(tag=u'020',
                               indicators=[u' ',u' '],
                               subfields=[u'a', self.student_id]))
        record.add_field(Field(tag=u'100',
                               indicators=[u' ',u' '],
                               subfields=[u'a',self.full_name()]))
        record.add_field(Field(tag=u'220',
                               indicators=[u' ',u' '],
                               subfields=[u'a',self.get_address()]))
        record.add_field(Field(tag=u'225',
                               indicators=[u' ',u' '],
                               subfields=[u'a',self.telephone_1]))
        record.add_field(Field(tag=u'235',
                               indicators=[u' ',u' '],
                               subfields=[u'a',self.telephone_2]))
        record.add_field(Field(tag=u'550',
                               indicators=[u' ',u' '],
                               subfields=[u'a',self.email_address]))
        if self.barcode:
            record.add_field(Field(tag=u'030',
                                   indicators=[u' ',u' '],
                                   subfields=[u'a',self.barcode]))
        return record

class ProtoStudent(models.Model):

    student_id = models.CharField(max_length=SNLEN, validators=[student_id_validator])
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    street_address = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    province = models.CharField(max_length=50, null=True, blank=True)
    postal_code = models.CharField(max_length=50, null=True, blank=True)
    email_type = models.CharField(max_length=3, null=True, blank=True)
    email_address = models.CharField(max_length=100)
    preferred_email = models.CharField(max_length=1, null=True, blank=True, choices=[('Y','Y'),('N','N')])
    telephone1 = models.CharField(max_length=25, null=True, blank=True)
    telephone_type = models.CharField(max_length=5, null=True, blank=True)
    ptype = models.ForeignKey(PatronType)
    created = models.DateField(auto_now_add=True)
    modified = models.DateField(auto_now=True)
    
    def __unicode__(self):
        return "%s, %s %s" % (self.last_name, self.first_name, self.student_id,)
    
class ProtoBarcode(models.Model):

    barcode = models.CharField(max_length=15, unique=True, validators=[barcode_validator])
    card_format = models.CharField(max_length=30, null=True, blank=True)
    station = models.CharField(max_length=15, null=True, blank=True)
    operator = models.CharField(max_length=50, null=True, blank=True)
    card_issued_to = models.CharField(max_length=255)
    person_num = models.CharField(max_length=20)
    created = models.DateField(auto_now_add=True)
    modified = models.DateField(auto_now=True)
    
    def __unicode__(self):
        return u'barcode: %s, sn: %s' % (self.barcode, self.person_num,)
