// Mock for react-native-maps
import React from "react";

export const PROVIDER_GOOGLE = "google";

export const Marker = ({ children, ...props }: any) => {
  return React.createElement("Marker", props, children);
};

export const Callout = ({ children, ...props }: any) => {
  return React.createElement("Callout", props, children);
};

export default class MapView extends React.Component<any> {
  render() {
    return React.createElement("MapView", this.props, this.props.children);
  }
}

