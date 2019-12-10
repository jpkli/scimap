<template>
  <v-app>
    <v-app-bar
      app
      color="#666"
      clipped-left
      dark
    >
      <v-app-bar-nav-icon @click="drawer=!drawer"></v-app-bar-nav-icon>
      <v-toolbar-title >Fire Map</v-toolbar-title>
    </v-app-bar>

    <v-content>
      <v-container fluid class="fill-height">
        <v-row class="fill-height" id="mapbox-container">
        </v-row>
      </v-container>
    </v-content>
    <v-navigation-drawer
      v-model="drawer"
        app
        flat
        clipped
        width="20%"
        class="pa-5"
    >
    <v-col>
      <p>Select Map Layer: </p>
      <v-overflow-btn
        class="my-2"
        :items="layerNames"
        item-value="text"
        v-model="selectedLayer"
      ></v-overflow-btn>
    </v-col>
    <v-col>
      <p>Select NetCDF Variable: </p>
      <v-overflow-btn
        class="my-2"
        :items="netCDFVariables"
        v-model="selectedNetCDFVar"
      ></v-overflow-btn>
    </v-col>
    </v-navigation-drawer>
    <v-dialog
      v-model="loadingData"
      hide-overlay
      persistent
      width="380"
      height="380"
    >
      <v-card
        dark
        class="text-center pa-3"
      >
        <h3 class="text-center ma-5">Please Wait</h3>
        <v-card-text>
          <v-progress-circular
          :size="60"
          :width="7"
          color="primary"
          indeterminate
        ></v-progress-circular>
        </v-card-text>
      </v-card>
    </v-dialog>
  </v-app>
  
</template>

<script>
import Mapbox from 'mapbox-gl';
import { GeoPrint, numpyDataLoader } from './GeoPrint';
import axios from 'axios';
import { config } from '../app.config';

export default {
  components: {
  },
  data() {
    return {
      dataServerUrl: config.dataServer.url,
      accessToken: config.mapbox.accessToken,
      map: null,
      numpy: null,
      isMapLayerReady: false,
      drawer: true,
      selectedLayer: 'All',
      mapLayers: {},
      layerNames: [
        'All',
        'Shapefile',
        // 'GeoTiff',
        'NetCDF'
      ],
      selectedNetCDFVar: 'fm100',
      netCDFVariables: ['fm100', 'vpd', 'sph', 'vs'],
      loadingData: true
    };
  },
  watch: {
    selectedLayer () {
      if (this.selectedLayer === 'All') {
        this.layerNames.slice(1)
        .forEach(layer => {
          this.map.setLayoutProperty(layer, 'visibility', 'visible');
        })
      } else {
        this.layerNames.slice(1).filter(layer => layer !== this.selectedLayer).forEach(layer => {
          this.map.setLayoutProperty(layer, 'visibility', 'none');
        })
        this.map.setLayoutProperty(this.selectedLayer, 'visibility', 'visible');
        let bound = this.mapLayers[this.selectedLayer].bound
        this.map.fitBounds([
          [bound.left, bound.top],
          [bound.right, bound.bottom]
        ]);
      }
    },
    async selectedNetCDFVar () {
      this.map.removeLayer('NetCDF');
      let netCDFLayer = await this.netCDF();
      this.map.addLayer(netCDFLayer, 'Shapefile');
    }
  },
  created() {
    this.numpy = numpyDataLoader();
  },
  mounted () {
    Mapbox.accessToken = this.accessToken;
    this.map = new Mapbox.Map({
      container: 'mapbox-container',
      style: "mapbox://styles/mapbox/light-v10",
      center: [-95.7129, 37.0902],
      zoom: 3
    })
    this.map.on('load', evt => {
      this.visualizeMapLayers(evt);
    })
  },
  methods: {
    async visualizeMapLayers () {

      this.mapLayers.Shapefile = await this.shapefile();
      this.mapLayers.NetCDF = await this.netCDF();
      // let geoTiff = await this.geoTiff();

      this.map.addLayer(this.mapLayers.Shapefile, 'building');
      this.map.addLayer(this.mapLayers.NetCDF, this.mapLayers.Shapefile.id);
      // this.map.addLayer(geoTiff, 'building');

      // /* Initialize the bounding based on map layers */
      // let bound = netCDFLayer.bound
      // this.map.fitBounds([
      //   [bound.left, bound.top],
      //   [bound.right, bound.bottom]
      // ]);

      // /* if fitting bound, use the moveend callback */
      // this.map.on("moveend", () => {
      //   if (!this.isMapLayerReady) {
      //     this.map.addLayer(shapefileLayer, 'building');
      //     // this.map.addLayer(geoTiff, 'building');
      //     this.map.addLayer(netCDFLayer, shapefileLayer.id);
      //     this.isMapLayerReady = true;
      //   }
      // });
    },

    async geoTiff() {
      let url = this.dataServerUrl;
      let year = 2011;
      let variable = "day_of_burn";
      let geotiff = await this.numpy.get(
        `${url}/fire/geotiff/${year}/${variable}/data`
      );
      let bound = await axios.get(
        `${url}/fire/geotiff/${year}/${variable}/bound`
      );

      let geotiffLayer = new GeoPrint({
        bound,
        width: geotiff.shape[1],
        height: geotiff.shape[0],
        data: geotiff.data,
        dataDomain: [bound.min, bound.max],
        // colorMap: 'RdYlBu', //'RdBu',
        coordinateMap: Mapbox.MercatorCoordinate.fromLngLat
      });

      return {
        id: "GeoTiff",
        type: "custom",
        onAdd(map, gl) {
          geotiffLayer.init(gl);
        },
        render(gl, matrix) {
          geotiffLayer.render(matrix);
        },
        bound: bound.data
      }
    },

    async netCDF() {
      let url = this.dataServerUrl;
      let year = 2010;
      let day = 1;
      let variable = this.selectedNetCDFVar; 
      this.loadingData = true;
      let ncBound = await axios.get(
        `${url}/gridmet/${year}/${day}/${variable}/bound`
      );
      let nc = await this.numpy.get(
        `${url}/gridmet/${year}/${day}/${variable}/data`
      );
      let ncLat = await this.numpy.get(
        `${url}/gridmet/${year}/${day}/${variable}/lat`
      );
      let ncLng = await this.numpy.get(
        `${url}/gridmet/${year}/${day}/${variable}/lon`
      );

      let bound = ncBound.data;
  
      let data = {
        lat: ncLat.data,
        lng: ncLng.data,
        values: nc.data
      };

      let topLeft = this.map.project({ lng: bound.left, lat: bound.top });
      let bottomRight = this.map.project({
        lng: bound.right,
        lat: bound.bottom
      });
      let width = Math.ceil(bottomRight.x - topLeft.x);
      let height = Math.ceil(bottomRight.y - topLeft.y);
      let mapData = new Float32Array(width * height);
      for (let x = 0; x < width; x++) {
        for (let y = 0; y < height; y++) {
          let coord = this.map.unproject({
            x: x + topLeft.x,
            y: y + topLeft.y
          });
          let lngIdx = data.lng.findIndex(d => d > coord.lng);
          let latIdx = data.lat.findIndex(d => d < coord.lat);
          let value = data.values[latIdx * nc.shape[1] + lngIdx];
          value +=
            lngIdx < data.lng.length
              ? data.values[latIdx * nc.shape[1] + lngIdx + 1]
              : value;
          value +=
            latIdx < data.lat.length
              ? data.values[(latIdx + 1) * nc.shape[1] + lngIdx]
              : value;
          if (lngIdx < data.lng.length && latIdx < data.lat.length) {
            value += data.values[(latIdx + 1) * nc.shape[1] + lngIdx + 1];
          }
          //TODO: use bilinear interpolation instead of averging the closest 4 locations
          value *= 0.25;

          if (Number.isNaN(value)) {
            value = -9999;
          }
          mapData[y * width + x] = value;
        }
      }

      let ncLayer = new GeoPrint({
        bound,
        width,
        height,
        data: mapData,
        dataDomain: [bound.min, bound.max],
        // colorMap: 'RdBu', //'RdBu',
        coordinateMap: Mapbox.MercatorCoordinate.fromLngLat
      });

      this.loadingData = false;

      return {
        id: "NetCDF",
        type: "custom",
        onAdd(map, gl) {
          ncLayer.init(gl);
        },
        render(gl, matrix) {
          ncLayer.render(matrix);
        },
        bound
      };
    },
  
    async shapefile() {
      let url = this.dataServerUrl;
      let geojs = await axios.get(`${url}/fire/shapefile`);
      let bound = {
        left: geojs.data.bbox[0],
        right: geojs.data.bbox[2],
        bottom: geojs.data.bbox[1],
        top: geojs.data.bbox[3]
      }

      this.map.addSource("Shapefile", {
        type: "geojson",
        data: geojs.data
      });

      return  {
        id: "Shapefile",
        type: "fill",
        source: "Shapefile",
        paint: {
          "fill-color": "rgba(200, 100, 240, 0.4)"
        },
        filter: ["==", "$type", "Polygon"],
        bound
      }
    }
  }
};
</script>
