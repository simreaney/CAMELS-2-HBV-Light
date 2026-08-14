# CAMELS-GB-2-HBV-Light
#
# Input projects for HBV-Light (Seibert and Vis 2012) for the 671 GB catchments in the CAMELS-GB2 dataset (Coxon et al 2020,
# CAMELS-GB v2 update). For each catchment, the dataset has been split into calibration and validation time periods on a 50:50 basis.
# In the src folder, there is the python script that was used for the processing.
#
# CAMELS-GB2 daily hydro-meteorological time series (1970-10-01 to 2022-09-30):
# https://catalogue.ceh.ac.uk/datastore/eidchub/9a46d428-958f-4ac1-86eb-94eee70c0955/Catchment_Timeseries/hydro-meteorological/daily/
#
# CAMELS-GB2 offers two products for precipitation/PET/temperature: CEH-GEAR/CHESS (matches CAMELS-GB v1, ends 2019-12-30)
# and HadUK-Grid/hydrope (covers the full 1970-2022 record). This script uses the HadUK-Grid precipitation & temperature and
# the "hydrope" PET, since only that combination spans the full record.
#
# Sim Reaney, Durham University
# simreaney.github.io
# November 2022, updated August 2026 for CAMELS-GB2

import pandas as pd
from pathlib import Path
import os

# Directory containing the raw CAMELS-GB2 CSVs (downloaded separately, not tracked in this repo).
RAW_DATA_DIR = Path(os.environ.get('CAMELS_GB2_RAW_DIR', 'raw_data'))

def main():

    list = open('gaugeList.csv')
    #Skip header
    list.readline()
    for line in list.readlines():

        line = line.split(',')
        print(line)
        gauge = line[0]
        fn = RAW_DATA_DIR / f'camels_gb_v2_hydromet_daily_timeseries_{gauge}_19701001-20220930.csv'
        df = pd.read_csv(fn)

        # Keep the HadUK-Grid precip/temperature and hydrope PET, which cover the full 1970-2022 record
        # (the CEH-GEAR/CHESS equivalents stop at 2019-12-30). Select before pad/dropna so the unused
        # columns' trailing NaNs don't wipe out otherwise-valid rows.
        df = df[['date', 'precipitation_haduk', 'temperature_haduk', 'pet_hydrope', 'peti_hydrope', 'discharge_spec', 'discharge_vol']]
        df = df.rename(columns={
            'precipitation_haduk': 'precipitation',
            'temperature_haduk': 'temperature',
            'pet_hydrope': 'pet',
            'peti_hydrope': 'peti',
        })

        #fill in missing values with padding. Not great but makes things work
        df = df.ffill()
        #if there are values at the start of the series that are 'na', drop these rows
        df = df.dropna()

        midpoint = len(df) // 2
        df0, df1 = df.iloc[:midpoint], df.iloc[midpoint:]

        createHBVLightDataSet(df0, gauge, 'cali', line[1])
        createHBVLightDataSet(df1, gauge, 'vali', line[1])


def createHBVLightDataSet(df, gauge, type, name):
    print(gauge)
    name = name.replace(" ", "_")
    name = name.replace("\n", "")
    name = name.replace("/", "-")

    filepath = Path(gauge + '-' + name + '-' + type + '/data/')
    filepath.parent.mkdir(parents=True, exist_ok=True)
    os.makedirs(filepath, exist_ok=True)

    df["date"] = pd.to_datetime(df['date'], format='%Y-%m-%d')

    #make the daily mean pet and precip files
    df['DOY'] = df['date'].dt.dayofyear
    DOY = df.groupby(['DOY']).mean()
    DOY = DOY.drop(366)
    DOY['pet'].to_csv(str(filepath) + '/evap.txt', index=False)
    DOY['temperature'].to_csv(str(filepath) + '/temp.txt', index=False)

    # Create the PTQ.txt file
    ptq = df.drop(columns=['discharge_vol', 'pet', 'peti', 'DOY'])
    ptq["date"] = pd.to_datetime(ptq["date"]).dt.strftime('%Y%m%d')
    ptq.to_csv(str(filepath) + '/ptq.txt', index=False, sep="\t")

main()
