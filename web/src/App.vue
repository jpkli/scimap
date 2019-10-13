<template>
  <div>
  <MglMap 
    style="height: 800px; width: 1200px;"
    :accessToken="accessToken"
    :mapStyle="mapStyle"
    :antialias="true"
    @load="testGeoTiff"
  />
  </div>
</template>

<script>
import Mapbox from "mapbox-gl";
import { MglMap } from "vue-mapbox";
import {GeoPrint, numpyDataLoader} from './GeoPrint';
import axios from 'axios';

export default {
  components: {
    MglMap
  },
  data() {
    return {
      accessToken: 'pk.eyJ1IjoianBrbGkiLCJhIjoiY2sxMGFxMzgyMDN2dzNicXcydDkxOHl3ZCJ9.Drr4XXqFPmp5gfdjZ0sQ0Q',
      mapStyle: 'mapbox://styles/mapbox/light-v10',
      numpy: null,
      bound: {},
      setData: false
    };
  },
  created () {
    this.numpy = numpyDataLoader()
  },
  methods: {

    async testGeoTiff (event) {
      this.map = event.map;
      let geotiff = await this.numpy.get('http://localhost:8888/geotiff/data');
      let bound = await axios.get('http://localhost:8888/geotiff/bound');
      // console.log(geotiff)
      bound = bound.data;
      this.map.fitBounds([
        [bound.left, bound.top],
        [bound.right, bound.bottom]
      ]);

      this.map.on('moveend', () => {
        if(!this.setData) {
          let geotiffLayer = new GeoPrint({
            bound,
            width: geotiff.shape[1],
            height: geotiff.shape[0],
            data: geotiff.data,
            dataDomain: [0, 365.0],
            // colorMap: 'RdYlBu', //'RdBu',
            coordinateMap: Mapbox.MercatorCoordinate.fromLngLat
          });

          this.map.addLayer({
            id: 'NetCDF4',
            type: 'custom',
            onAdd (map, gl) {
              geotiffLayer.init(gl);
            },
            render (gl, matrix) {
              geotiffLayer.render(matrix)
            }
          }, 'building');
          this.setData = true;
        }
      });
    },

    async testNetCDF4 (event) {
      this.map = event.map;
      let ncBound = await axios.get('http://localhost:8888/nc/bound');
      let nc = await this.numpy.get('http://localhost:8888/nc/data');
      let ncLat = await this.numpy.get('http://localhost:8888/nc/lat');
      let ncLng = await this.numpy.get('http://localhost:8888/nc/lng');
      
      let bound = ncBound.data;
      let data = {
        lat: ncLat.data,
        lng: ncLng.data,
        values: nc.data
      }

      this.map.fitBounds([
        [bound.left, bound.top],
        [bound.right, bound.bottom]
      ]);

      this.map.on('moveend', () => {
        if(!this.setData) {
          let topLeft = this.map.project({lng: bound.left, lat: bound.top});
          let bottomRight = this.map.project({lng: bound.right, lat: bound.bottom});
          let width = Math.ceil(bottomRight.x - topLeft.x);
          let height = Math.ceil(bottomRight.y - topLeft.y);
          let mapData = new Float32Array(width * height);          
          for (let x = 0; x < width; x++) {
            for (let y = 0; y < height; y++) {
              let coord = this.map.unproject({x: x + topLeft.x, y: y + topLeft.y});
              let lngIdx = data.lng.findIndex(d => d > coord.lng);
              let latIdx = data.lat.findIndex(d => d < coord.lat);
              let value = data.values[latIdx * nc.shape[1] + lngIdx];
              value += (lngIdx < data.lng.length) ? data.values[latIdx * nc.shape[1] + lngIdx + 1] : value;
              value += (latIdx < data.lat.length) ? data.values[(latIdx + 1) * nc.shape[1] + lngIdx] : value;
              if (lngIdx < data.lng.length && latIdx < data.lat.length) {
                value += data.values[(latIdx + 1) * nc.shape[1] + lngIdx + 1];
              }
              //TODO: use bilinear interpolation instead of averging the closest 4 locations
              value *= 0.25;

              if (Number.isNaN(value)) {
                value = -9999;
              }
              mapData[y * width + x] = value
            }
          }
          let ncLayer = new GeoPrint({
            bound,
            width,
            height,
            data: mapData,
            dataDomain: [0, 36.0],
            // colorMap: 'RdBu', //'RdBu',
            coordinateMap: Mapbox.MercatorCoordinate.fromLngLat
          });

          this.map.addLayer({
            id: 'NetCDF4',
            type: 'custom',
            onAdd (map, gl) {
              ncLayer.init(gl);
            },
            render (gl, matrix) {
              ncLayer.render(matrix)
            }
          }, 'building');
          this.setData = true;
        }
      })
    }
  }
};
</script>
