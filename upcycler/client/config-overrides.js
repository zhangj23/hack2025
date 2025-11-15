const webpack = require("webpack");
const path = require("path");

module.exports = function override(config) {
  const fallback = config.resolve.fallback || {};
  Object.assign(fallback, {
    buffer: require.resolve("buffer"),
    stream: require.resolve("stream-browserify"),
    crypto: require.resolve("crypto-browserify"),
    util: require.resolve("util"),
    assert: require.resolve("assert"),
    http: require.resolve("stream-http"),
    https: require.resolve("https-browserify"),
    os: require.resolve("os-browserify/browser"),
    url: require.resolve("url"),
    zlib: require.resolve("browserify-zlib"),
    process: require.resolve("process/browser.js"),
    vm: require.resolve("vm-browserify"),
  });
  config.resolve.fallback = fallback;

  // Fix for process/browser resolution
  config.resolve.alias = {
    ...config.resolve.alias,
    "process/browser": require.resolve("process/browser.js"),
  };

  config.plugins = (config.plugins || []).concat([
    new webpack.ProvidePlugin({
      process: "process/browser.js",
      Buffer: ["buffer", "Buffer"],
    }),
  ]);
  config.ignoreWarnings = [/Failed to parse source map/];
  return config;
};
