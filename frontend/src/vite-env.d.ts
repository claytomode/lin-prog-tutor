/// <reference types="svelte" />
/// <reference types="vite/client" />

declare module "plotly.js-dist-min" {
  const Plotly: {
    react: (
      el: HTMLElement,
      data: object[],
      layout?: object,
      config?: Record<string, unknown>,
    ) => Promise<void>;
    newPlot: (el: HTMLElement, data: object[], layout?: object, config?: object) => Promise<void>;
  };
  export default Plotly;
}
