from django.contrib import admin
from sis.models import ProtoStudent, ProtoBarcode, Student, PatronType

class ProtoStudentAdmin(admin.ModelAdmin):
    search_fields = ['student_id',
                     'first_name',
                     'last_name',
                     'street_address',
                     'email_address',]
    list_display = ['student_id',
                    'first_name',
                    'last_name',
                    'street_address',
                    'email_address',
                    'preferred_email',
                    'telephone1',
                    'telephone_type',
                    'ptype',]
    list_filter = ['email_type',
                   'telephone_type',
                   'ptype',]

class ProtoBarcodeAdmin(admin.ModelAdmin):
    list_display = ['barcode',
                    'card_format',
                    'station',
                    'operator',
                    'card_issued_to',
                    'person_num',]

class StudentAdmin(admin.ModelAdmin):
    search_fields = ['student_id',
                     'first_name',
                     'last_name',
                     'street_address',
                     'email_address',
                     'barcode',]
    list_display = ['student_id',
                    'first_name',
                    'last_name',
                    'street_address',
                    'email_address',
                    'telephone_1',
                    'telephone_2',
                    'barcode',
                    'ptype',]
    list_filter = ['ptype']
    
class PatronTypeAdmin(admin.ModelAdmin):
    list_display = ['ptype', 'pcode', 'pdesc']

admin.site.register(ProtoBarcode, ProtoBarcodeAdmin)
admin.site.register(ProtoStudent, ProtoStudentAdmin)
admin.site.register(Student, StudentAdmin)
admin.site.register(PatronType, PatronTypeAdmin)
