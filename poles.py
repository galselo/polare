import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import pygrib as pg
import pickle
import os
from tqdm import tqdm
import matplotlib

# configure backend
matplotlib.use('Agg')

# https://jswhit.github.io/pygrib/docs/

datafile = "data.grib"
lat_max = 66.  # max absolute latitude, map from +/-90 to +/-lat_max
vmin = -12.  # min temperature range, C
vmax = 12.  # max temperature range, C
ncols = 12  # number of columns in the plot
colormap = 'coolwarm'  # define colormap
year_min = 1981  # min year for average (included)
year_max = 2010  # max year for average (included)
hemisphere = "N"  # N/S

# month names array, 1-based
months = "# Gen Feb Mar Apr Mag Giu Lug Ago Set Ott Nov Dic".split(" ")

# load data
a = pg.open(datafile)

# get time series size
ntot = a.messages
print("Number of time-series points: %d" % ntot)


# check if pickle for average is present, if so load from pickle
# NOTE: remove pickles if lat_max changed, or if year_min, year_max changed
if os.path.isfile("avg_N.pickle"):
    print("loading averages from pickle")
    avg_N = pickle.load(open("avg_N.pickle","rb"))
    avg_S = pickle.load(open("avg_S.pickle","rb"))
else:

    # loop on time series to compute average
    for i in tqdm(range(ntot)):

        # read next descriptor
        b = a.read(1)[0]

        # load data both hemispheres
        data_N, lats_N, lons_N = b.data(lat1=lat_max, lat2=90., lon1=0., lon2=359.9)
        data_S, lats_S, lons_S = b.data(lat1=-90., lat2=-lat_max, lon1=0., lon2=359.9)

        # get month and year from current dataset info
        msg = "%s" % b
        date = msg.split(" ")[-1]
        year = int(date[:4])
        month = int(date[4:6])

        # init average array to zero, one per month
        if i == 0:
            xx_N, yy_N = data_N.shape
            xx_S, yy_S = data_S.shape
            avg_count = 0
            avg_N = np.zeros((12, xx_N, yy_N))
            avg_S = np.zeros((12, xx_S, yy_S))

        # sum for the average only if in year range
        if year_min <= year <= year_max:
            avg_N[month-1, :, :] += data_N
            avg_S[month-1, :, :] += data_S


    # compute average
    avg_count = year_max - year_min + 1
    avg_N /= avg_count
    avg_S /= avg_count

    # save to pickles, TODO: single function
    pickle_out = open("avg_N.pickle", "wb")
    pickle.dump(avg_N, pickle_out)
    pickle_out.close()

    # same as above
    pickle_out = open("avg_S.pickle", "wb")
    pickle.dump(avg_S, pickle_out)
    pickle_out.close()

print("Number of rows: %d" % (ntot // ncols))

# init
min_anomaly = 999.
max_anomaly = -999.

# define plotting grid
fig = plt.figure(figsize=(ncols, ntot // ncols))
gs = gridspec.GridSpec(ntot // ncols, ncols, # width_ratios=np.ones(ncols),
         wspace=0.0, hspace=0.0)

# rewind data
a.seek(0)

# loop to plot
for i in tqdm(range(ntot)):

    # select grid
    ax = plt.subplot(gs[i // ncols, i % ncols], projection="polar")

    # move to next descriptor
    b = a.read(1)[0]

    # find year, month for labelling
    msg = "%s" % b
    date = msg.split(" ")[-1]
    year = int(date[:4])
    month = int(date[4:6])

    # load data, TODO: use data already loaded
    if hemisphere == "N":
        data_N, lats_N, lons_N = b.data(lat1=lat_max, lat2=90., lon1=0., lon2=359.9)
        anomaly = data_N - avg_N[month-1, :, :]
        lons_range = lons_N / 180.*np.pi
        lat_range = (90. - lats_N) / 180. * np.pi
    else:
        data_S, lats_S, lons_S = b.data(lat1=-90., lat2=-lat_max, lon1=0., lon2=359.9)
        anomaly = data_S - avg_S[month-1, :, :]
        lons_range = lons_S / 180.*np.pi
        lat_range = (90. + lats_S) / 180. * np.pi

    # store min/max anomaly
    min_anomaly = min(min_anomaly, np.amin(anomaly))
    max_anomaly = max(max_anomaly, np.amax(anomaly))

    # do plot
    plt.pcolormesh(lons_range,
                   lat_range,
                   anomaly,
                   vmin=vmin,
                   vmax=vmax,
                   cmap=colormap)

    # remove tick labels
    ax.set_xticklabels([])
    ax.set_yticklabels([])

    # remove black circle
    ax.spines['polar'].set_visible(False)

print("Anomaly range:", min_anomaly, max_anomaly)
print("Current range:", vmin, vmax)

# save figure
plt.tight_layout()
plt.savefig("grid_%s.png" % hemisphere)


