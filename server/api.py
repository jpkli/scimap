import tornado.ioloop
import tornado.web
import rasterio as rio
import tornado.websocket
import io
import numpy as np
import xarray as xr

file = '/store/data/scimap/Global_fire_atlas_day_of_burn_yearly_2015.tif'
# file = '../data/Global_fire_atlas_day_of_burn_yearly_2003.tif'
# file = '../data/out.npy'
nc_file = '/store/data/scimap/vs_2016.nc'

class DataHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "http://localhost:8080")
        self.set_header("Access-Control-Allow-Headers", "Origin, X-Requested-With, Content-Type, Accept")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')

    def options(self):
        # no body
        self.set_status(204)
        self.finish()

class GeoTiffDataHandler(DataHandler):
    data = []
    bound = []

    def get(self, param):
      if param == 'bound':
        bound = GeoTiffDataHandler.bound
        print(bound)
        self.write({
          'left': -124.60327134602406,
          'right': -114.1977643576058,
          'top': 42.10009746644571,
          'bottom': 31.99689783895414
        })
        # self.write({
        #   'left': bound.left,
        #   'right': bound.right,
        #   'top': bound.top,
        #   'bottom': bound.bottom
        # })
      else:
        with rio.open(file) as ff:
          band = ff.read(1, masked = True)
          GeoTiffDataHandler.bound = ff.bounds
          memfile = io.BytesIO()
          np.save(memfile, band)
          memfile.seek(0)
          self.write(memfile.read())

class NcDataHandler(DataHandler):
    data = []
    bound = []
    
    def get(self, param):
      if param == 'bound':
        self.write({
          'left': -124.7666666333333,
          'right': -67.058333300000015,
          'top': 49.400000000000000,
          'bottom': 25.066666666666666
        })
      elif param == 'lng':
        data = np.load('/store/data/scimap/test_lon.npy')
        memfile = io.BytesIO()
        np.save(memfile, data)
        memfile.seek(0)
        self.write(memfile.read())
      elif param == 'lat':
        data = np.load('/store/data/scimap/test_lat.npy')
        memfile = io.BytesIO()
        np.save(memfile, data)
        memfile.seek(0)
        self.write(memfile.read())
      else:
        data = np.load('/store/data/scimap/test.npy')
        memfile = io.BytesIO()
        np.save(memfile, data)
        memfile.seek(0)
        self.write(memfile.read())
      

def make_app():
    return tornado.web.Application([
        (r"/geotiff/([^/]+)", GeoTiffDataHandler),
        (r"/nc/([^/]+)", NcDataHandler),
    ])

if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()
