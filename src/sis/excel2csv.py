import os
import sys
import uno
import logging
import subprocess
from multiprocessing import Process
from time import sleep
from com.sun.star.connection import ConnectionSetupException
from com.sun.star.connection import NoConnectException
from com.sun.star.lang import DisposedException
from django.conf import settings

CONN_DFLT = settings.CONN_DFLT
ENV_DFLT = settings.ENV_DFLT

LOCATIONS = ['/usr/bin/soffice', '/usr/bin/ooffice']
OOBIN_DFLT = None
try:
    OOBIN_DFLT = settings.OOBIN_DFLT
except AttributeError:
    for l in LOCATIONS:
        if os.access(l, os.F_OK and os.X_OK):
            OOBIN_DFLT = l
if OOBIN_DFLT is None:
    raise AttributeError("Please set OOBIN_DFLT to the LibreOffice executable in settings.py")

basecmd = "%s --headless --invisible --accept=\"socket,host=localhost,port=%s;urp;StarOffice.ComponentContext\""

def get_new_extension(orig, ext):
    d = os.path.dirname(orig)
    b = os.path.basename(os.path.splitext(orig)[0])
    return os.path.join(d, b + ext)

def make_property_array(**kwargs):
    """convert the keyword arguments to a tuple of PropertyValue uno
    structures"""
    array = []
    for name, value in kwargs.iteritems():
        prop = uno.createUnoStruct("com.sun.star.beans.PropertyValue")
        prop.Name = name
        prop.Value = value
        array.append(prop)
    return tuple(array)

def save_to_csv(doc, filename, props="44,34,76,1"):
    # filter options string:
    #  Elem 1: ascii code for field separator (44 = ,)
    #  Elem 2: ascii code for text delimiter  (34 = ")
    #  Elem 3: Mysterious code for charset (76 = utf-8)
    #  Elem 4: 1-based number of line from which to start export
    # see http://wiki.services.openoffice.org/wiki/Documentation/DevGuide/Spreadsheets/Filter_Options
    filter_props = make_property_array(
        FilterName="Text - txt - csv (StarCalc)",
        FilterOptions=props)
    csvname = get_new_extension(filename, ".csv")
    logging.info('Storing file to : %s' % (csvname,))
    doc.storeToURL('file://' + csvname, filter_props)
    
def bash_escape(cmd):
    """Return a command escaped for passing to the shell"""
    ret = cmd.replace(';','\;')
    return ret

def deleteRow(doc, sheet=0, row=0):
    """Delete specified row from first sheet of doc"""
    logging.info('Delete row %d sheet %d in %s' % \
                 (row, sheet, doc.getLocation()))
    sheets = doc.getSheets()
    targ_sheet = sheets.getByIndex(sheet)
    rows = targ_sheet.getRows()
    rows.removeByIndex(row,1) # remove 1 rows starting at row row

def deleteColumn(doc, sheet=0, col=0):
    """Delete the specified column in the specified sheet"""
    logging.info('Deleting col %d sheet %d in %s' % \
                 (col, sheet, doc.getLocation()))
    sheets = doc.getSheets()
    targ_sheet = sheets.getByIndex(sheet)
    cols = targ_sheet.getColumns()
    cols.removeByIndex(col,1) # remove 1 column starting a column col

def uno_start(oobin=OOBIN_DFLT, port=2002, env=ENV_DFLT):
    """Start the uno listener so that we can get a context"""
    cmd = basecmd % (oobin, port)
    args = (cmd,)
    kwargs = {'env':env, 'stdout':subprocess.PIPE, 'stderr':subprocess.STDOUT, 'shell':True }
    proc = Process(target=subprocess.Popen, args=args, kwargs=kwargs)
    proc.start()

def uno_init(connstr, try_start=True):
    """Start OpenOffice.org as a service using connstr as the -accept
    arg and return the desktop object."""
    try:
        localContext = uno.getComponentContext()

        resolver = localContext.ServiceManager.createInstanceWithContext(
                   "com.sun.star.bridge.UnoUrlResolver", localContext )

        smgr = resolver.resolve( "uno:socket,host=localhost,port=2002;urp;StarOffice.ServiceManager" )
        remoteContext = smgr.getPropertyValue( "DefaultContext" )

        desktop = smgr.createInstanceWithContext( "com.sun.star.frame.Desktop",remoteContext)
        return desktop
    except (NoConnectException, ConnectionSetupException):
        if try_start:
            sleep(2)
            uno_start()
            sleep(2)
            uno_init(connstr, try_start=False)
        else:
            logging.exception("UNO server not started.")
            raise 
    
def get_desktop(host='localhost', port=2002):
    """Get an instance of the UNO Desktop"""
    return uno_init(CONN_DFLT % (host, port))

def modify_sid(filename, host='localhost', port=2002, desktop=None, terminate=True):
    """Open and modify the Student ID file (delete some rows and
    columns and save it as a csv file
    Parameters:
     
      * filename - absolute path (or use ~ for userdir)

      * host - the host on which the UNO server is listening

      * port - the port on which the UNO server is listening

      * desktop - a connection to the running UNO desktop
    """
    filename = os.path.expanduser(filename)
    if desktop is None:
        desktop = uno_init(CONN_DFLT % (host, port))
    document = desktop.loadComponentFromURL('file://' + filename,'_blank',0,())
    logging.info('Loaded file %s' % (filename,))
    # delete the first row
    deleteRow(document)
    # delete first column if cell A1 is "Field49"
    sheets = document.getSheets()
    sheet0 = sheets.getByIndex(0)

    # Arguments for getCellByPosition: column, row
    cell = sheet0.getCellByPosition(0,0)
    if cell.getString() == 'Field49':
        deleteColumn(document)
    # delete the first column if the text in A1 is 'txtDate'
    cell = sheet0.getCellByPosition(0,0)
    if cell.getString() == 'txtDate':
        deleteColumn(document)
    # delete the first column if the text in A1 is 'Field40'
    cell = sheet0.getCellByPosition(0,0)
    if cell.getString() == 'Field40':
        deleteColumn(document)
    # change Card_code cell (now at 0,0) to barcode
    cell = sheet0.getCellByPosition(0,0)
    cell.setString('barcode')
    # change Format_Name to card_format
    cell = sheet0.getCellByPosition(1,0)
    cell.setString('card_format')
    # change Station_ID to station
    cell = sheet0.getCellByPosition(2,0)
    cell.setString('station')
    # change txtOperator to operator
    cell = sheet0.getCellByPosition(3,0)
    cell.setString('operator')
    # change Name to card_issued_to
    cell = sheet0.getCellByPosition(4,0)
    cell.setString('card_issued_to')
    # change Name to card_issued_to
    cell = sheet0.getCellByPosition(5,0)
    cell.setString('person_num')
    # save current sheet as csv
    controller = document.getCurrentController()
    controller.setActiveSheet(sheet0)
    save_to_csv(document, filename)
    document.dispose()
    # ignore the DisposedException when terminating
    if terminate:
        try:
            desktop.terminate()
        except DisposedException:
            pass

def modify_sis(filename, host='localhost', port=2002, desktop=None, terminate=True):
    """Open and modify the SIS file (delete some rows and
    columns and save it as a csv file
    Parameters:
    
      * filename - absolute path (or use ~ for userdir)

      * host - the host on which the UNO server is listening

      * port - the port on which the UNO server is listening

      * desktop - a connection to the running UNO desktop

      * terminate - if true, terminate the connection before returning
    """
    filename = os.path.expanduser(filename)
    delete_headings = ('USER ID',)
    ordered_field_map = (('ID', 'student_id'),
                         ('FIRST', 'first_name'),
                         ('LAST', 'last_name'),
                         ('ADDRESS','street_address'),
                         ('CITY', 'city'),
                         ('PROV', 'province'),
                         ('POSTAL', 'postal_code'),
                         ('EMAIL TYPE', 'email_type'),
                         ('EMAIL ADDRESS', 'email_address'),
                         ('PREFERRED_EMAIL', 'preferred_email'),
                         ('PHONE #', 'telephone1'),
                         ('TYPE', 'telephone_type'),)
                  
    field_map = tuple([(i[0],i[1][0],i[1][1]) \
                       for i in enumerate(ordered_field_map)])
                  
    last_col = len(field_map) - 1
    if desktop is None:
        desktop = uno_init(CONN_DFLT % (host, port))
    document = desktop.loadComponentFromURL('file://' + filename,'_blank',0,())
    logging.info('Loaded file %s' % (filename,))
    sheets = document.getSheets()
    sheet0 = sheets.getByIndex(0)
    # delete some columns
    for col in range(0,last_col):
        cell = sheet0.getCellByPosition(col,0)
        if cell.getString() in delete_headings:
            deleteColumn(document, col=col)
    for f in field_map:
        cell = sheet0.getCellByPosition(f[0],0)
        if cell.getString() == f[1]:
            cell.setString(f[2])
        else:
            raise ValueError, "Invalid value in field: %s" % cell.getString()

    # save current sheet as csv
    controller = document.getCurrentController()
    controller.setActiveSheet(sheet0)
    save_to_csv(document, filename)
    document.dispose()
    # ignore the DisposedException when terminating
    if terminate:
        try:
            desktop.terminate()
        except DisposedException:
            pass
    
if __name__ == '__main__':

    if len(sys.argv) < 3:
        print "Usage: %s TYPE FILENAME" % (sys.argv[0],)
        sys.exit(2)
        
    if not os.path.isfile(sys.argv[2]):
        print "File not found: %s" % (sys.argv[2],)
    else:
        if sys.argv[1] == 'sid':
            modify_sid(sys.argv[2])
        elif sys.argv[1] == 'sis':
            modify_sis(sys.argv[2])
        else:
            print "Unknown input file type: %s" % (sys.argv[1],)
            sys.exit(3)
