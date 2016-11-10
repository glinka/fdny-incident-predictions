import urllib
import os.path
import zipfile
import pandas as pd
import numpy as np
from sklearn import linear_model
from scipy.stats import ks_2samp
import matplotlib.pyplot as plt

def analyze_data():
    """Download JSON using SODA API"""
    
    # download and save data if we haven't already done so
    filename = './data/fdny-data.csv'
    if not os.path.exists(filename):
        # build query
        soda_endpoint = 'https://data.cityofnewyork.us/resource/ibte-hq4u.json'
        data_columns_to_dl = ("im_incident_key,"
                                  "fire_box,"
                                  "incident_type_desc,"
                                  "incident_date_time,"
                                  "arrival_date_time,"
                                  "units_onscene,"
                                  "last_unit_cleared_date_time,"
                                  "highest_level_desc,"
                                  "total_incident_duration,"
                                  "action_taken1_desc,"
                                  "zip_code,"
                                  "borough_desc")

        soda_query = soda_endpoint + '?$select=' + data_columns_to_dl + '&$where=units_onscene>"1"' + '&$limit=1000'

        # download and read json
        data = pd.read_json(soda_query)
        # save by csv
        data.to_csv(filename, index=False)

    else:
        data = pd.read_csv(filename) # , parse_dates=[4,5,7], infer_datetime_format=True)
        for column in data.columns:
            if 'time' in column:
                data[column] = pd.to_datetime(data[column])

    np.set_printoptions(precision=4)

    # # # look at response times by borough
    data['response_times'] = (data['arrival_date_time'] - data['incident_date_time']).astype('timedelta64[s]')

    data_by_borough = data.groupby('borough_desc')
    nboroughs = data_by_borough.ngroups

    ks_statistics = np.empty((nboroughs, nboroughs))
    p_vals = np.empty((nboroughs, nboroughs))

    for i, (borough_name, borough) in enumerate(data_by_borough):
        for j, (borough_name2, borough2) in enumerate(data_by_borough):
            ks_statistic = ks_2samp(borough['response_times'], borough2['response_times'])
            ks_statistics[i,j] = ks_statistic[0]
            p_vals[i,j] = ks_statistic[1]
    print 'Pairwise Kolmogorov-Smirnov test statistics:\n', ks_statistics
    print 'Pairwise Kolmogorov-Smirnov p-values:\n', p_vals
    print 'Group names:\n', data_by_borough.groups.keys()
    
    

    # # generate exploratory plots
    fig = plt.figure()
    ax = fig.add_subplot(111)
    fs = 36
    data.boxplot(column='response_times', by='borough_desc', ax=ax, rot=45)
    ax.set_ylim((0,1000))
    ax.set_title('')
    ax.set_ylabel('Response time (s)', fontsize=1.5*fs)
    fig.subplots_adjust(bottom=0.35, left=0.12)

    # # group by zip/borough and look at number of incidents over time
    # by borough:
    data_by_borough = data.groupby('borough_desc')
    nboroughs = data_by_borough.ngroups
    incident_freq_by_borough = np.zeros((nboroughs, 24))

    fig = plt.figure()
    ax = fig.add_subplot(111)
    for i, (borough_name, borough) in enumerate(data_by_borough):
        nincidents_in_borough = borough.shape[0]
        hourly_incidents = borough.groupby(borough['incident_date_time'].map(lambda t: t.hour))
        his = hourly_incidents.size()
        incident_freq_by_borough[i,his.index]  = his.values.astype(float)/nincidents_in_borough
        ax.plot(np.arange(1,25), incident_freq_by_borough[i], label=borough_name)

    ax.legend(fontsize=fs, loc='upper left')
    ax.set_xlabel('Hour of day (24 -> midnight)', fontsize=1.5*fs)
    ax.set_ylabel('Incident frequency', fontsize=1.5*fs)
    ax.set_xlim((1,24))

    # by zip
    data_by_zip = data.groupby('zip_code')
    nzips = data_by_zip.ngroups
    incident_freq_by_zip = np.zeros((nzips, 24))

    fig = plt.figure()
    ax = fig.add_subplot(111)
    for i, (zip_name, zipcode) in enumerate(data_by_zip):
        nincidents_in_zip = zipcode.shape[0]
        hourly_incidents = zipcode.groupby(zipcode['incident_date_time'].map(lambda t: t.hour))
        his = hourly_incidents.size()
        incident_freq_by_zip[i,his.index]  = his.values.astype(float)/nincidents_in_zip
        ax.plot(np.arange(1,25), incident_freq_by_zip[i])

    ax.legend(fontsize=fs, loc='upper left')
    ax.set_xlabel('Hour of day (24 -> midnight)', fontsize=1.5*fs)
    ax.set_ylabel('Incident frequency', fontsize=1.5*fs)
    ax.set_xlim((1,24))
    ax.set_title('Incident frequency by zip code')

    plt.show()


    
if __name__=='__main__':
    analyze_data()
