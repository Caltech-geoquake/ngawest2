#!/usr/bin/env Python

import numpy as np
import xlrd, xlwt

# =======================
# NGA flatfiles  (data)
# =======================
def ReadFlatFileNGA(xlsfile):
    """
    Generate NGA flatfile dictionary for generate usage
    """
    # read in excel flatfile
    book = xlrd.open_workbook(xlsfile)
    sh = book.sheet_by_index(0)    # 'Flatfile' sheet name
    keys = sh.row_values(0)
    for itmp in range( len(keys) ):
        keys[itmp] = keys[itmp].encode('ascii')

    # Column names needed ( add more depending on selection criterion )
    names_predictors = [ 'Record Sequence Number', 'EQID',     # IDs
          'Earthquake Magnitude', 'Dip (deg)','Rake Angle (deg)','Dept to Top Of Fault Rupture Model', 'Fault Rupture Width (km)',    # source related
          'Joyner-Boore Dist. (km)', 'ClstD (km)', 'FW/HW Indicator', 'Source to Site Azimuth (deg)',                                 # source-site pair related
          "GMX's C1", 'HP-H1 (Hz)', 'HP-H2 (Hz)', 'LP-H1 (Hz)', 'LP-H2 (Hz)','File Name (Horizontal 1)','File Name (Horizontal 2)',   # seismogram related
          'Preferred Vs30 (m/s)', 'Measured/Inferred Class', 'Z1 (m)', 'Z1.5 (m)', 'Z2.5 (m)'         # site related
          ]
    keys_predictors = ['RecordID', 'EQID',
                       'Mw', 'dip', 'rake', 'Ztor', 'W',
                       'Rjb', 'Rrup', 'Fhw', 'azimuth',
                       'GMX_C1', 'HP1', 'HP2', 'LP1', 'LP2', 'H1','H2',
                       'Vs30', 'VsFlag', 'Z1.0','Z1.5','Z2.5'
                       ]
    Fhwi = {'hw':1,'fw':0,'nu':0,'na':0,'':None}   # relate indicators to Fhw flag

    # IM related
    names_IMs = ['Record Sequence Number', 'PGA (g)', 'PGV (cm/sec)', 'PGD (cm)' ]
    keys_IMs = ['RecordID', 'PGA', 'PGV', 'PGD']

    periods = []
    for ikey, key in enumerate( keys ):
        if isinstance( key, str ):
            key.encode( 'ascii' )
        # key now is one of the column name
        if key[0] == 'T' and key[-1] == 'S':
            names_IMs.append( key )
            keys_IMs.append( 'SA'+key[1:-1] )
            periods.append( float(key[1:-1]) )

    # colname and colindex map
    icol_dictP = {}
    icol_dictI = {}
    for ikey, key in enumerate( keys ):
        if key in names_predictors:
            icol_dictP[key] = ikey
        if key in names_IMs:
            icol_dictI[key] = ikey

    nga_flats = {}; nga_IMs = {}
    for icol, key in enumerate( names_predictors ):
        col0 = sh.col_values(icol_dictP[key])
        col0[0] = col0[0].encode('ascii')
        if isinstance( col0[1], str ):
            if key == 'FW/HW Indicator':
                # Fhw string to flag (int)
                for irow in range(1, len(col0) ):
                    col0[irow] = col0[irow].encode('ascii')
                    col0[irow] = Fhwi[col0[irow]]
            else:
                for irow in range(1, len(col0) ):
                    col0[irow] = col0[irow].encode('ascii')

        keyP = keys_predictors[icol]
        nga_flats[keyP] = col0[1:]

    for icol, key in enumerate( names_IMs ):
        col0 = sh.col_values(icol_dictI[key])
        if isinstance( col0[1], str ):
            for irow in range(1, len(col0) ):
                col0[irow] = col0[irow].encode('ascii')
        keyI = keys_IMs[icol]
        nga_IMs[keyI] = col0[1:]

    return nga_flats, nga_IMs


def test_ReadFlatFileNGA(xlsfile):
    nga_flats, nga_IMs = ReadFlatFileNGA(xlsfile)
    print(list(nga_flats.keys()))
    print(list(nga_IMs.keys()))
    print(nga_flats['Fhw'])


#  Other Utilities
def GetSubset( nga_flats0, nga_IMs0, index ):
    nga_flats1 = {}; nga_IMs1 = {}
    for ikey0, key0 in enumerate( nga_flats0.keys() ):
        row_value1 = list(nga_flats0[key0])
        row_value1 = [element for i,element in enumerate( row_value1 ) if i not in index]  # Use this instead of using pop (dangerous)
        nga_flats1[key0] = tuple(row_value1)

    for ikey1, key1 in enumerate( nga_IMs0.keys() ):
        row_value1 = list(nga_IMs0[key1])
        row_value1 = [element for i,element in enumerate( row_value1 ) if i not in index]
        nga_IMs1[key1] = tuple(row_value1)

    return nga_flats1, nga_IMs1


# Save by rules
def SubsetExtractNGA0(nga_flats, nga_IMs, RecordID):
    print(RecordID[0])

    nga_flats0 = {}; nga_IMs0 = {}
    for ikey0, key0 in enumerate( nga_flats.keys() ):
        nga_flats0[key0] = []
        for ir,rid in enumerate( RecordID ):
            try:
                nga_flats0[key0].append( nga_flats[key0][rid-1] )
            except:
                print(key0, rid)

    for ikey0, key0 in enumerate( nga_IMs.keys() ):
        nga_IMs0[key0] = []
        for ir,rid in enumerate( RecordID ):
            try:
                nga_IMs0[key0].append( nga_IMs[key0][rid-1] )
            except:
                print(key0, rid)

    return nga_flats0, nga_IMs0


# Remove by rules
def SubsetExtractNGA(nga_flats, nga_IMs, rules=None):
    """
    Extract Subset from NGA FlatFiles Given rules ('parameter_name':conditions)
    conditions could be:
    case 1: [('<',0.5),]
    in this case, the rule will be: when parameter_name equals to a list (could be a number or string), then remove that whole record (a row)
    case 2: [('>', 0.5),  ('<', 1.0)]
    in this case, the rule will be: when 0.5 < parameter < 1.0, keep the whole rule, here the two limit could only be number
    case 3: [('>',0.5),]
    in this case, the rule will be: when 0.5 < parameter, remove the whole row
    the operation include: remove and keep, the condition could be : ==, >, <, >=, <=
    """
    nga_flats0 = {}; nga_IMs0 = {}
    for ikey, key in enumerate( nga_flats.keys() ):
        nga_flats0[key] = tuple( nga_flats[key] )
    for ikey, key in enumerate( nga_IMs.keys() ):
        nga_IMs0[key] = tuple( nga_IMs[key] )
    if rules == None:
        return nga_flats, nga_IMs
    else:

        for ikey, key in enumerate( rules.keys() ):
            # conditional selection for given column
            # get the index, and then remove the same row for all columns
            row_value = nga_flats0[key]
            condition = rules[key]

            # Special Cases for the selection
            if key == 'H1' or key == 'H2':
                # one special case where the seismogram name with *XXX.at2 or *XXX-(W,N,S,E).at2
                row_value0 = []; row_value_tmp0 = []
                for irow in range( len(row_value) ):
                    char0 = row_value[irow].strip().split('.')[0]
                    char1 = char0[-1]
                    if char1 in ['W','E','N','S']:
                        char2 = char0.strip().split('-')[0][-3:]
                    else:
                        char2 = char0[-3:]
                    row_value0.append(char2)
                row_value = tuple( row_value0 )

            # find the index and do the selection
            try:
                Nc = len(condition)
                if Nc == 1:
                    con = condition[0][0]
                    values = condition[0][1]
                    if con == '==':
                        try:
                            N = len(values)
                            if isinstance( values, str ):
                                # for 'A','AB', 'XXX'
                                index = eval("(np.array(row_value)%s'%s').nonzero()"%(con,values))[0]
                                nga_flats0, nga_IMs0 = GetSubset(nga_flats0,nga_IMs0, index)
                            else:
                                print(N)
                                # for [1,2,3,],['A','B',] (string list or number list)
                                for ic in range( N ):
                                    print('id %s'%value[ic])
                                    row_value = nga_flats0[key]
                                    if isinstance( values[ic], str ):
                                        index = eval("(np.array(row_value)%s'%s').nonzero()"%(con,values[ic]))[0]
                                    else:
                                        index = eval('(np.array(row_value)%s%s).nonzero()'%(con,values[ic]))[0]
                                    print(index)
                                    nga_flats0, nga_IMs0 = GetSubset(nga_flats0,nga_IMs0, index)
                                    print('test GetSubset')
                                    row_input()

                        except:
                            if isintance( values, str ):
                                # for ''( empty)
                                print('test')
                                index = eval("(np.array(row_value)%s'%s').nonzero()"%(con,values))[0]
                                nga_flats0, nga_IMs0 = GetSubset(nga_flats0,nga_IMs0, index)
                            else:
                                # for single number as value
                                index = eval('(np.array(row_value)%s%s).nonzero()'%(con,values))[0]
                                nga_flats0, nga_IMs0 = GetSubset(nga_flats0,nga_IMs0, index)

                    elif con == '>' or con == '<' or con=='>=' or con=='<=':
                        try:
                            Nv = len(values)
                            print('>,<,>=,<= could not work for multiple values or strings')
                            raise ValueError
                        except:
                            index = eval('(np.array(row_value)%s%s).nonzero()'%(con,values))[0]
                            nga_flats0, nga_IMs0 = GetSubset(nga_flats0,nga_IMs0, index)
                else:
                    # multiple conditions (2)
                    for ic in range( Nc ):
                        row_value = nga_flats0[key]
                        con = condition[ic][0]
                        value = conditions[ic][1]
                        if con == '>' or con == '<' or con=='>=' or con=='<=':
                            try:
                                Nv = len(value)
                                print('>,<,>=,<= could not work for multiple values or string')
                                raise ValueError
                            except:
                                index = eval('(np.array(row_value)%s%s).nonzero()'%(con,value))[0]
                                nga_flats0, nga_IMs0 = GetSubset(nga_flats0,nga_IMs0, index)
            except:
                # no condition for key
                pass

        for ikey, key in enumerate( nga_flats0.keys() ):
            nga_flats0[key] = list( nga_flats0[key] )
        for ikey, key in enumerate( nga_IMs0.keys() ):
            nga_IMs0[key] = list( nga_IMs0[key] )

        return nga_flats0, nga_IMs0


def WriteSubsetNGA(flats, IMs, xlsfile):
    """
    Write subset dataset to xls files
    """
    wbk = xlwt.Workbook()
    sheet1 = wbk.add_sheet('FlatFile_Subset')
    for ikey, key in enumerate( flats.keys() ):
        for irow in range( len( flats[key] )+1 ):
            if irow == 0:
                sheet1.write( irow, ikey, key )
            else:
                sheet1.write( irow, ikey, flats[key][irow-1] )
    sheet2 = wbk.add_sheet('FlatFile_Subset_IM')
    for ikey, key in enumerate( IMs.keys() ):
        for irow in range( len( IMs[key] )+1 ):
            if irow == 0:
                sheet2.write( irow, ikey, key )
            else:
                sheet2.write( irow, ikey, IMs[key][irow-1] )
    wbk.save(xlsfile)


def ReadSubsetNGA(xlsfile, ftype='xls'):
    """
    Read Subset xls file or txt file
    """
    nga_flats = {}; nga_IMs = {}
    if ftype == 'xls':
        # read in excel flatfile
        book = xlrd.open_workbook(xlsfile)
        sh1 = book.sheet_by_index(0)    # Flatinfo
        sh2 = book.sheet_by_index(1)    # IMinfo

        # flatinfo
        keys = sh1.row_values(0)     # column name
        for icol, key in enumerate( keys ):
            if isinstance( key, str ):
                key = key.encode( 'ascii' )
            col0 = sh1.col_values(icol)
            for irow in range(1, len(col0) ):
                if isinstance( col0[irow] , str ):
                    col0[irow] = col0[irow].encode('ascii')
            nga_flats[key] = col0[1:]

        # IMinfo
        keys = sh2.row_values(0)
        for icol, key in enumerate( keys ):
            if isinstance( key, str ):
                key = key.encode( 'ascii' )
            col0 = sh2.col_values(icol)
            for irow in range(1, len(col0) ):
                if isinstance( col0[1], str ):
                    col0[irow] = col0[irow].encode('ascii')
            nga_IMs[key] = col0[1:]
    else:
        # ftype = 'txt':
        # ...
        pass

    return nga_flats, nga_IMs


def info_pre(flatinfo, IMinfo):
    # pre-processing the flatinfo
    keys_flat = [
               'Mw', 'dip', 'rake', 'Ztor', 'W',
               'Rjb', 'Rrup', 'Fhw', 'azimuth',
               'Vs30', 'VsFlag', 'Z1.0','Z1.5','Z2.5'
               ]
    flatinfo0 = {}; IMinfo0 = {}
    for ikey, key in enumerate( keys_flat ):
        row_value = flatinfo[key]
        for irow in range( len(row_value) ):
            if isinstance(row_value[irow], str):
                if row_value[irow] == '':
                    row_value[irow] = None
                else:
                    if key == 'VsFlag':
                        tmp = int(row_value[irow])
                        row_value[irow] = (tmp+1)*(tmp==0) + (1-1)*(tmp!=0)
                    elif key == 'Fhw':
                        row_value[irow] = int( row_value[irow] )
                    elif key == 'Z2.5':
                        row_value[irow] = float( row_value[irow] ) / 1000. # from m to km for Python NGA calc
                    else:
                        row_value[irow] = float( row_value[irow] )
            else:
                if key == 'VsFlag':
                    tmp = row_value[irow]
                    if tmp == None:
                        row_value[irow] = 0   # inferred Vs30
                    else:
                        tmp = int(tmp)
                        row_value[irow] = (tmp+1)*(tmp==0) + (1-1)*(tmp!=0)
                elif key == 'Z2.5':
                    row_value[irow] = float( row_value[irow] ) / 1000. # from m to km for Python NGA calc
                else:
                    pass
        flatinfo0[key] = row_value

    # pre-processing the IMinfo
    IMinfo.pop('RecordID')
    IMinfo.pop('PGV')
    IMinfo.pop('PGD')
    for ikey, key in enumerate( IMinfo.keys() ):
        row_value = IMinfo[key]
        for irow in range( len(row_value) ):
            rv = row_value[irow]
            if isinstance( rv, str ):
                row_value[irow] = float( rv )
            else:
                pass
        IMinfo0[key] = row_value

    return flatinfo0, IMinfo0


def IMs_nga_Py( flatinfo, periods, NGA_models = ['BA',], NGAs=None ):

    # flatinfo now is based on record id for nga flatfiles
    try :
        Np = len(periods)
    except:
        periods = [periods]
        Np = len(periods)

    IMs = {}
    IMs_std = {}
    for inga, nga in enumerate( NGA_models ):
        IMs[nga] = []
        IMs_std[nga] = []

        print('Compute %s model...'%nga)

        # Compute NGAs
        for ip in range( Np ):
            median, std, tau, sigma = NGA08( nga, flatinfo['Mw'], flatinfo['Rjb'], flatinfo['Vs30'], periods[ip], flatinfo['rake'], NGAs=NGAs,\
                                 Rrup = flatinfo['Rrup'], Rx=None, dip = flatinfo['dip'], W = flatinfo['W'], Ztor = flatinfo['Ztor'], \
                                 Z25 = flatinfo['Z2.5'], Z10 = flatinfo['Z1.0'], azimuth=flatinfo['azimuth'],Fhw=flatinfo['Fhw'], \
                                 Fas=0, AB11= None, VsFlag=flatinfo['VsFlag'] )
            # append with the order of the periods ! (not by key)
            IMs[nga].append( median )
            IMs_std[nga].append( std )
        IMs[nga] = np.array( IMs[nga] )
        IMs_std[nga] = np.array( IMs_std[nga] )

    return IMs, IMs_std, IMs_tau, IMs_sigma



def HypocenterDistribution(xlsfile):

    # Read in all xls content
    book = xlrd.open_workbook(xlsfile)
    sh = book.sheet_by_index(0)    # 'Flatfile' sheet name
    keys = sh.row_values(0)
    for itmp in range( len(keys) ):
        keys[itmp] = keys[itmp].encode('ascii')

    # select corresponding fields
    select_keys = ['EQID', 'Dip (deg)', 'Rake Angle (deg)', 'Source to Site Azimuth (deg)','X',\
            'Fault Rupture Width (km)', 'Hypocenter Depth (km)', 'Dept to Top Of Fault Rupture Model']
    icol_dict = {}
    for ikey, key in enumerate( keys ):
        if key in select_keys:
            icol_dict[key] = ikey

    # first select to get subset (all fault models)
    subset = {}
    FFlag = 'Finite Rupture Model: 1=Yes;  0=No'
    for ikey, key in enumerate( keys ):
        if FFlag == key:
            iflag = ikey
            break
    Fcol0 = sh.col_values(iflag)[1:]    # finite fault flag

    for icol, key in enumerate( select_keys ):
        col0 = sh.col_values(icol_dict[key])
        col0[0] = col0[0].encode('ascii')
        irow0 = 0; col_values = []
        for irow in range(1, len(col0) ):
            if Fcol0[irow-1] == 1:
                if isinstance( col0[irow], str ):
                    col00 = col0[irow].strip()
                else:
                    col00 = col0[irow]
                    if isinstance( col00, str ):
                        col00 = col00.encode('ascii')
                col_values.append( col00 )
            else:
                continue
        keyP = select_keys[icol]
        subset[keyP] = col_values

    # second: manage the data by EQID (group by each source)
    key = 'EQID'
    eqid0s = subset[key]
    eqids = []   # not repeated
    SrcGroupX = {}   # site-dependent
    SrcGroupRD = {}   # source-dependent rake and dip
    irow = 0
    while irow < len(eqid0s):
        eqid0 = eqid0s[irow]
        key1 = str(eqid0)
        if eqid0 not in eqids:
            eqids.append( eqid0 )
            SrcGroupX[key1] = []
            SrcGroupX[key1].append([subset[select_keys[3]][irow],\
                                    subset[select_keys[4]][irow],\
                                    ])
            SrcGroupRD[key1] = [ subset[select_keys[1]][irow],\
                                 subset[select_keys[2]][irow],
                                 subset[select_keys[5]][irow],\
                                 subset[select_keys[6]][irow],\
                                 subset[select_keys[7]][irow],]
        else:
            SrcGroupX[key1].append([subset[select_keys[3]][irow],\
                                     subset[select_keys[4]][irow],\
                                    ])
        irow += 1

    SrcAveRD_XY = []
    EQkeys = list(SrcGroupRD.keys())

    for isrc in range( len(EQkeys) ):
        key1 = EQkeys[isrc]
        dip = SrcGroupRD[key1][0] * np.pi/ 180.
        W = SrcGroupRD[key1][2]
        HypoDepth = SrcGroupRD[key1][3]
        Ztor = SrcGroupRD[key1][4]

        # Compute HypoY (based on W, dip, HypoDepth, and Ztor)
        Y = 1-(HypoDepth-Ztor)/(W*np.sin(dip))
        if Y < 0:
            continue
            #print 'EQID', 'HypoDepth', 'Ztor','W','Dip'
            #print key1, HypoDepth, Ztor, W, dip*180./np.pi
        if Y < 0.1:
            print('EQID', 'HypoDepth', 'Ztor','W','Dip')
            print(key1, HypoDepth, Ztor, W, dip*180./np.pi)

        # first find the correct sites to do the average:
        Xs = []; Ys = []
        for isite in range( len(SrcGroupX[key1]) ):
            az = SrcGroupX[key1][isite][0]
            X = SrcGroupX[key1][isite][1]

            # set the starting point of strike vector
            # and starting point of the up-dip vector
            # as the origin:
            if az in [90,-90]:
                continue
            elif 0 <= az < 90 or -90 < az < 0:
                Xs.append( 1-X )
                Ys.append( Y )
            elif 90 < az <= 180 or -180 <= az < 90:
                Xs.append( X )
                Ys.append( Y )

        # second, find the largest
        try:
            AbsX = max(Xs)
            AbsY = max(Ys)
            rake = SrcGroupRD[key1][1]
            if -180<=rake<-150 or -30<rake<30 or 150<rake<=180:
                # strike-slip events
                Fss = 1
            else:
                # dip-slip events
                Fss = 0
            SrcAveRD_XY.append([Fss, AbsX, AbsY])
        except:
            continue

    SrcAveRD_XY = np.array( SrcAveRD_XY )

    # plot historgram X,Y scatter with histogram
    import matplotlib.pyplot as plt
    plt.rc('font',family='Arial')
    nbar = 10
    clr = 'b'
    pfmt = 'eps'

    # all events
    Xs = SrcAveRD_XY[:,1]
    Ys = SrcAveRD_XY[:,2]

    fig = plt.figure(1,(8,6))
    ax1 = fig.add_axes([0.45,0.35,0.5,0.5])
    ax2 = fig.add_axes([0.45,0.05,0.5,0.2])
    ax3 = fig.add_axes([0.05,0.35,0.3,0.5])
    ax1.plot( Xs,Ys, 'ro', mfc='none')
    ax1.set_xlabel('AlongStrikeHypoX')
    ax1.set_ylabel('UpDipHypoY')
    ax1.set_title('AllEvents (%s)'%(len(Xs)) )

    ax2.hist( Xs, nbar, normed=0, color=clr )
    ax2.xaxis.set_label_position('top')
    ax2.invert_yaxis()
    ax2.xaxis.set_ticks([])
    ax3.hist( Ys, nbar, normed=0, color=clr, orientation='horizontal' )
    ax3.yaxis.set_ticks([])
    ax3.invert_xaxis()
    fig.savefig('./plots/AllEventsHypoDistribution.%s'%pfmt,format=pfmt)

    # strike-slip events
    index = (SrcAveRD_XY[:,0] == 1).nonzero()[0]
    Xs = SrcAveRD_XY[index,1]
    Ys = SrcAveRD_XY[index,2]

    fig.clf()
    ax1 = fig.add_axes([0.45,0.35,0.5,0.6])
    ax2 = fig.add_axes([0.45,0.05,0.5,0.2])
    ax3 = fig.add_axes([0.05,0.35,0.3,0.6])
    ax1.plot( Xs,Ys, 'ro', mfc='none')
    ax1.set_xlabel('AlongStrikeHypoX')
    ax1.set_ylabel('UpDipHypoY')
    ax1.set_title('Strike-Slip Events (%s)'%(len(Xs)) )

    ax2.hist( Xs, nbar, normed=0, color=clr )
    ax2.xaxis.set_label_position('top')
    ax2.invert_yaxis()
    ax2.xaxis.set_ticks([])
    ax3.hist( Ys, nbar, normed=0, color=clr,orientation='horizontal' )
    ax3.yaxis.set_ticks([])
    ax3.invert_xaxis()
    fig.savefig('./plots/SSEventsHypoDistribution.%s'%pfmt,format=pfmt)

    # non-strike-slip
    index = (SrcAveRD_XY[:,0] == 0).nonzero()[0]
    Xs = SrcAveRD_XY[index,1]
    Ys = SrcAveRD_XY[index,2]

    fig.clf()
    ax1 = fig.add_axes([0.45,0.35,0.5,0.6])
    ax2 = fig.add_axes([0.45,0.05,0.5,0.2])
    ax3 = fig.add_axes([0.05,0.35,0.3,0.6])
    ax1.plot( Xs,Ys, 'ro', mfc='none')
    ax1.set_xlabel('AlongStrikeHypoX')
    ax1.set_ylabel('UpDipHypoY')
    ax1.set_title('Non Strike-Slip Events (%s)'%(len(Xs)) )

    ax2.hist( Xs, nbar, normed=0, color=clr)
    ax2.xaxis.set_label_position('top')
    ax2.invert_yaxis()
    ax2.xaxis.set_ticks([])
    ax3.hist( Ys, nbar, normed=0, color=clr, orientation='horizontal' )
    ax3.yaxis.set_ticks([])
    ax3.invert_xaxis()
    fig.savefig('./plots/NonSSEventsHypoDistribution.%s'%pfmt,format=pfmt)
    #plt.show()



# ====================
# self_application
# ====================
if __name__ == '__main__':

    import sys
    opt = sys.argv[1]
    xlsfile = './NGAdata/NGA_Flatfile.xls'

    if opt == 'HypoL':
        HypocenterDistribution(xlsfile)

    if opt == 'GetSubset':

        rules_type = sys.argv[2]   # read from file or defined by user in the process

        # Read the original NGA flatfile
        nga_flats, nga_IMs = ReadFlatFileNGA(xlsfile)    # for all nga_flats

        # =======================================
        # Subset database generation
        if rules_type == 'file':

            # read record id you want to remove from file
            RecordID_save = list(np.loadtxt( './NGAdata/RecordID_save.txt', dtype='i4' ))
            nga_flats0, nga_IMs0 = SubsetExtractNGA0(nga_flats, nga_IMs, RecordID_save)

            # write into xls file for test for further usage
            subfile = './NGAdata/FlatFile_Subset_%s.xls'%rules_type

        else:
            # sepecify the rule of selection by user
            # set selection conditions follow Chiou and Youngs
            EQID_remove = [3,5,7,8,11,13,17,22,26,35,67,71,84,86,93,95,109,129,142,153,154,155,156]
            # Kobe event 128 doesn't have SA values
            for ieq in range( len( EQID_remove) ):
                EQID_remove[ieq] = '%4.4i'%EQID_remove[ieq]
            GMXC1_remove = ['','C','D','E','F','G','H',]   # put '' condition first

            # set up rule dictionary for selecting the subset of the original dataset
            # Remove records that match the following conditions from the original dataset
            rules = {
                     'EQID':[('==',EQID_remove),],
                     'GMX_C1':[('==',GMXC1_remove),],
                     'H1':[('==','XXX'),],    # check record index
                     'H2':[('==','XXX'),],
                     'Mw':[('==',''),],
                     'Vs30':[('==',''),],
                     'Rjb': [('==',''),],
                     'rake':[('==',''),],
                     'Ztor':[('<',0),],
                     }
            nga_flats0, nga_IMs0 = SubsetExtractNGA(nga_flats, nga_IMs,rules)

            if 1:
                # Aftershock selection
                lines = open( './NGAdata/event_class_AS' ).readlines()
                AS_event_ID = []   # get all eq that are not mainshock and use rule to remove
                for il in range( 1, len(lines) ):
                    spl = lines[il].strip().split(' ')
                    eqid = '%4.4i'%int(spl[0])
                    flag = spl[-2]
                    if flag == 'AS' or flag == 'Swarm':
                        AS_event_ID.append( eqid )
                rules = {'EQID': [('==',AS_event_ID),]}
                nga_flats0, nga_IMs0 = SubsetExtractNGA(nga_flats0, nga_IMs0, rules )

            subfile = './NGAdata/FlatFile_Subset_%s.xls'%rules_type

        # write into xls file for test for further usage
        WriteSubsetNGA(nga_flats0, nga_IMs0, subfile )

        # print the subset dimensions (as test)
        print('# of Records:')
        print('%s:   %s   %s'%('InfoEntry', 'Subset', 'Original'))
        for key in list(nga_flats.keys()):
            print('%s:   %s   %s'%(key,len(nga_flats0[key]),len(nga_flats[key]) ))
        for key in list(nga_IMs.keys()):
            print('%s:   %s   %s'%(key,len(nga_IMs0[key]),len(nga_IMs[key]) ))
