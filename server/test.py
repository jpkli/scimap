import numpy as np
import rasterio as rio
import xarray as xr
from netCDF4 import Dataset
f_path = '/store/data/scimap/vs_2015.nc'

# file = '../data/Global_fire_atlas_direction_monthly_2015.tif'
file = '/store/data/Global_fire_atlas_day_of_burn_yearly_2015.tif'

if __name__ == "__main__":

    f = Dataset(f_path)
    ds = xr.open_dataset(xr.backends.NetCDF4DataStore(f))
    df = ds.to_dataframe()
    print(df)

    # with rio.open(file) as ff:
    #   # bound = ff.bounds
    #   band = ff.read(1)
    #   print(band.shape)
    #   np.save('../data/out.npy', band)