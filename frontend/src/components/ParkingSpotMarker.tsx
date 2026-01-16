// frontend/src/components/ParkingSpotMarker.tsx
import React from "react";
import { Marker, Callout } from "react-native-maps";
import { View, Text, StyleSheet } from "react-native";
import type { ParkingSpot } from "../domain/models";

interface Props {
  spot: ParkingSpot;
  onPressDetails?: (spotId: string) => void;
}

export const ParkingSpotMarker: React.FC<Props> = ({ spot, onPressDetails }) => {
  const color =
    spot.meterStatus === "broken"
      ? "#f97373"
      : spot.safetyScore >= 70
      ? "#22c55e"
      : "#facc15";

  return (
    <Marker
      coordinate={{ latitude: spot.latitude, longitude: spot.longitude }}
      pinColor={color}
    >
      <Callout onPress={() => onPressDetails?.(spot.id)}>
        <View style={styles.callout}>
          <Text style={styles.title}>{spot.streetName}</Text>
          <Text style={styles.subtitle}>
            Safety: {spot.safetyScore.toFixed(0)} · Tourism:{" "}
            {spot.tourismDensity.toFixed(0)}
          </Text>
          <Text style={styles.subtitle}>
            Meter: {spot.meterStatus} (
            {Math.round(spot.meterStatusConfidence * 100)}%)
          </Text>
          {spot.distanceToDestinationM != null && (
            <Text style={styles.subtitle}>
              Walk: {(spot.distanceToDestinationM / 1000).toFixed(2)} km
            </Text>
          )}
          <Text style={styles.cta}>Tap for details</Text>
        </View>
      </Callout>
    </Marker>
  );
};

const styles = StyleSheet.create({
  callout: {
    minWidth: 180,
    padding: 8,
  },
  title: { fontWeight: "600", marginBottom: 4 },
  subtitle: { fontSize: 12 },
  cta: { marginTop: 4, fontSize: 12, fontWeight: "500" },
});


