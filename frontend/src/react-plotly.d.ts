declare module "react-plotly.js" {
  import { Component } from "react";
  import { Data, Layout, Config } from "plotly.js";

  interface PlotParams {
    data: Data[];
    layout?: Partial<Layout>;
    config?: Partial<Config>;
    style?: React.CSSProperties;
    className?: string;
    revision?: number;
    onInitialized?: (figure: { data: Data[]; layout: Partial<Layout> }, graphDiv: HTMLElement) => void;
    onUpdate?: (figure: { data: Data[]; layout: Partial<Layout> }, graphDiv: HTMLElement) => void;
    onPurge?: (graphDiv: HTMLElement) => void;
    onRedraw?: (graphDiv: HTMLElement) => void;
    divId?: string;
    debug?: boolean;
    useResizeHandler?: boolean;
  }

  export default class Plot extends Component<PlotParams> {}
}

