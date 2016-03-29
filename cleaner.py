import sys
import re
import csv
import itertools
import numpy as np
import pandas as pd

qRE = re.compile(r'^[a-z][a-z]\d\d_')
tsLineRE = re.compile(r'form_.*_timestamp')

def rplcNA(s):
    if s == '2':
        return 'NA'
    elif s == '1':
        return 'YES'
    elif s == '0':
        return 'NO'
    else:
        return s

def readForm(pathToData, csv_filename):
    """
    Read in CSV file with denormalized data
    Clean and normalize
    Return obs in a DataFrame
    """

    obs = pd.DataFrame()

    week = 0
    mentor = 0
    
    # open and transpose data
    ogData = itertools.izip(*csv.reader(open(pathToData+csv_filename, "rU")))
    
    # drop the csv extension
    if re.search('.csv$', csv_filename) != None:
        fn = csv_filename[:re.search('.csv$', csv_filename).start()] 
    else:
        fn = csv_filename

    # iterate through records
    for i, entry in enumerate(ogData):

        # first entry in the row has branching information in it
        qt = entry[0]
        resp = entry[2:]

        # if there is an incomplete week stop reading the data
        if tsLineRE.search(qt) != None:
            if set(resp)=={''}: 
                break

        # this is the week beginning
        # increment and reset counters
        if tsLineRE.search(qt) != None:
            week = week + 1
            mentor = 0
            print 'Reading ' + fn + ' Week ' + str(week)
        
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
                
            # how many columns are there
            WID = len(resp)
            
            # append new data row
            newEvent = zip(
                itertools.repeat(str(fn),WID),
                itertools.repeat(int(week),WID),
                itertools.repeat(int(mentor),WID),
                itertools.repeat(str(qCode),WID),
                resp
                )
            header = ['fn','week', 'mentor', 'qCode', 'resp']
            obsDF = pd.DataFrame.from_records(newEvent, columns = header)
            obs = obs.append(obsDF)
    
    # filter out blank responses
    blank = obs['resp'].isin([''])
    obs = obs[np.logical_not(blank)]

    # replace 2 with NA, etc.
    obs['resp'] = map(rplcNA, obs['resp'])
    
    return obs

def main():
    """
    Loop read / clean function over all files
    Concatenate and print all observations
    """

    # can pass multiple files
    pathToData = sys.argv[1]
    filename = sys.argv[2:]

    # clean data files
    collect = []
    for fn in filename:
        print pathToData + fn
        this_study = readForm(pathToData, fn)
        collect.append(this_study)

    # concatenate dataframes
    obs = pd.concat(collect)

    # print normalized data
    obs.to_csv(pathToData+'obs.csv', index = False)

if __name__ == '__main__':
    main()

# python cleaner.py './' AG.csv AI.csv CI.csv CG.csv