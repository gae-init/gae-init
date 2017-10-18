var path = require('path');

var ExtractTextPlugin = require('extract-text-webpack-plugin');
var ManifestRevisionPlugin = require('manifest-revision-webpack-plugin');

var rootAssetPath = './main/static/assets';

module.exports = {
  entry: {
    app_js: [
      rootAssetPath + '/scripts/app.js'
    ],
    app_css: [
      rootAssetPath + '/styles/main.css'
    ]
  },
  output: {
    path: './main/static/dist',
    publicPath: 'http://localhost:2992/assets/',
    filename: '[name].[chunkhash].js',
    chunkFilename: '[id].[chunkhash].js'
  },
  resolve: {
    extensions: ['', '.js', '.css']
  },
  module: {
    loaders: [
      {
        test: /\.js?$/,
        loader: 'babel-loader',
        query: {
          presets: ['es2015', 'react']
        },
        exclude: /node_modules/
      },
      {
        test: /\.css$/i,
        loader: ExtractTextPlugin.extract('style-loader', 'css-loader')
      },
      {
        test: /\.(jpe?g|png|gif|svg([\?]?.*))$/i,
        loaders: [
          'file?context=' + rootAssetPath + '&name=[path][name].[hash].[ext]',
          'image?bypassOnDebug&optimizationLevel=7&interlaced=false'
        ]
      }
    ]
  },
  plugins: [
    new ExtractTextPlugin('[name].[chunkhash].css'),
    new ManifestRevisionPlugin(path.join('main/static', 'manifest.json'), {
      rootAssetPath: rootAssetPath,
      ignorePaths: ['/styles', '/scripts']
    })
  ]
};
