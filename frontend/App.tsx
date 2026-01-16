// frontend/App.tsx
import React from "react";
import { SafeAreaView, StyleSheet, StatusBar } from "react-native";
import { MapScreen } from "./src/screens/MapScreen/MapScreen";

export default function App() {
  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="dark-content" />
      <MapScreen />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
});


