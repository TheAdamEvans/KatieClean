import numpy as np
import pandas as pd
import sys

def readForm(pathToData, csv_filename):
    import re
    import csv
    import itertools
    
    obs = pd.DataFrame()

    weekIndex = 0
    mentor = 0
    
    # open and transpose data
    ogData = itertools.izip(*csv.reader(open(pathToData+csv_filename, "rU")))
    
    # drop the extension
    if re.search('.csv$', csv_filename) != None:
        fn = csv_filename[:re.search('.csv$', csv_filename).start()] 
    else:
        fn = csv_filename
        
    # pattern matching with regular expressions
    qRE = re.compile('^[a-z][a-z]\d\d_')
    tsLineRE = re.compile('form_.*_timestamp')



    for i, entry in enumerate(ogData):

        # first entry in the row has branching information in it
        qt = entry[0]

        # if there is an incomplete week stop reading the data
        if tsLineRE.search(qt) != None:
            if set(entry[1:])=={''}: 
                break 

        # survey level information
        if re.match('.*survey_identifier.*',qt) != None:
            surveyIdentifier = entry[1:]
        elif re.match('.*record_id.*',qt) != None or re.match('.*staffid.*',qt) != None:
            staffID = entry[1:]
            
        # this is the week beginning
        # increment and reset counters
        elif tsLineRE.search(qt) != None:
            weekIndex = weekIndex + 1
            mentor = 0
            ts = entry[1:]
            print 'Reading ' + fn + ' Week ' + str(weekIndex)
        
        # matching a question
        elif qRE.match(qt) != None:
            
            # get the question code
            qCode = qt.split('_')[1]
            
            # guess mentor number when applicable
            if re.search('isfm',qCode) != None:                
                fmNum = int(re.search('(\d+)',qCode).group(0))
                if fmNum <= 57:
                    mentor = (fmNum+1)/7 + 1
                else:
                    mentor = 0
            else:
                mentor = 0
                
            # record responses
            resp = entry[1:]
            
            # how many columns are there
            WID = len(staffID)
            

            # append new data row
            newEvent = zip(
                itertools.repeat(str(fn),WID),
                ts,
                staffID,
                itertools.repeat(int(weekIndex),WID),
                itertools.repeat(int(mentor),WID),
                itertools.repeat(str(qCode),WID),
                resp
                )
            obsDF = pd.DataFrame.from_records(newEvent, columns = ['fn', 'ts','staffID','weekIndex', 'mentor', 'qCode', 'resp'])
            obs = obs.append(obsDF)
    
    # filter out blank responses
    blank = obs['resp'].isin([''])
    obs = obs[np.logical_not(blank)]
    
    return obs


pathToData = sys.argv[1] # TODO check this path
filename = sys.argv[2:]

# normalize data
obs = pd.DataFrame()
for fn in filename:
    print pathToData + fn
    this_study = readForm(pathToData, fn)
    obs = this_study.append(obs)

# print all data
obs.to_csv(pathToData+'obs.csv', index = False)

# python cleaner.py './' AG.csv AI.csv CI.csv CG.csv
