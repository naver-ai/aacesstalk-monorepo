const { withNxMetro } = require('@nx/react-native');
const { getDefaultConfig, mergeConfig } = require('@react-native/metro-config');
const { withNativeWind } = require("nativewind/metro");
const { wrapWithReanimatedMetroConfig } = require('react-native-reanimated/metro-config')

const defaultConfig = getDefaultConfig(__dirname);
const { assetExts, sourceExts } = defaultConfig.resolver;

async function createConfig() {
    /**
   * Metro configuration
   * https://reactnative.dev/docs/metro
   *
   * @type {import('metro-config').MetroConfig}
   */
  const customConfig = {
    transformer: {
      babelTransformerPath: require.resolve('react-native-svg-transformer'),
    },
    resolver: {
      assetExts: assetExts.filter((ext) => ext !== 'svg'),
      sourceExts: [...sourceExts, 'cjs', 'mjs', 'svg'],
    },
  };

  const reanimConfig = wrapWithReanimatedMetroConfig(customConfig)

  const nxConfig = await withNxMetro(mergeConfig(defaultConfig, reanimConfig), {
    // Change this to true to see debugging info.
    // Useful if you have issues resolving modules
    debug: false,
    // all the file extensions used for imports other than 'ts', 'tsx', 'js', 'jsx', 'json'
    extensions: [],
    // Specify folders to watch, in addition to Nx defaults (workspace libraries and node_modules)
    watchFolders: [],
  })

  return withNativeWind(nxConfig, {input: './src/global.css'})
}

module.exports = createConfig()
