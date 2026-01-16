// frontend/src/screens/MapScreen/MapScreen.tsx
import React, { useEffect, useState, useCallback } from "react";
import { View, StyleSheet, ActivityIndicator } from "react-native";
import MapView, { PROVIDER_GOOGLE, Region } from "react-native-maps";
import { useUserLocation } from "../../hooks/useUserLocation";
import { useParkingSpots } from "../../hooks/useParkingSpots";
import { ParkingSpotMarker } from "../../components/ParkingSpotMarker";
import { ParkingFilterBar } from "../../components/ParkingFilterBar";
import { DestinationSearchBar } from "../../components/DestinationSearchBar";

const INITIAL_REGION: Region = {
  latitude: 40.7128,
  longitude: -74.006,
  latitudeDelta: 0.05,
  longitudeDelta: 0.05,
};

export const MapScreen: React.FC = () => {
  const { location, isLoading: locationLoading } = useUserLocation();
  const {
    spots,
    isLoading: spotsLoading,
    fetchSpotsForRegion,
    applyFilters,
  } = useParkingSpots();

  const [region, setRegion] = useState<Region>(INITIAL_REGION);

  useEffect(() => {
    if (location) {
      const newRegion: Region = {
        latitude: location.latitude,
        longitude: location.longitude,
        latitudeDelta: 0.02,
        longitudeDelta: 0.02,
      };
      setRegion(newRegion);
      fetchSpotsForRegion(newRegion, {
        userLat: location.latitude,
        userLng: location.longitude,
      });
    }
  }, [location, fetchSpotsForRegion]);

  const handleRegionChangeComplete = useCallback(
    (nextRegion: Region) => {
      setRegion(nextRegion);
      fetchSpotsForRegion(nextRegion);
    },
    [fetchSpotsForRegion]
  );

  const handleFiltersChange = useCallback(
    (filters) => {
      applyFilters(filters);
    },
    [applyFilters]
  );

  const handleDestinationSelected = useCallback(
    (destinationCoords: { latitude: number; longitude: number }) => {
      const destRegion: Region = {
        latitude: destinationCoords.latitude,
        longitude: destinationCoords.longitude,
        latitudeDelta: 0.02,
        longitudeDelta: 0.02,
      };
      setRegion(destRegion);
      fetchSpotsForRegion(destRegion, {
        destLat: destinationCoords.latitude,
        destLng: destinationCoords.longitude,
      });
    },
    [fetchSpotsForRegion]
  );

  const isBusy = locationLoading || spotsLoading;

  return (
    <View style={styles.container}>
      <DestinationSearchBar onDestinationSelected={handleDestinationSelected} />
      <ParkingFilterBar onChange={handleFiltersChange} />

      <View style={styles.mapContainer}>
        {isBusy && (
          <View style={styles.loadingOverlay}>
            <ActivityIndicator />
          </View>
        )}

        <MapView
          style={StyleSheet.absoluteFill}
          provider={PROVIDER_GOOGLE}
          region={region}
          onRegionChangeComplete={handleRegionChangeComplete}
          showsUserLocation
          showsMyLocationButton
        >
          {spots.map((spot) => (
            <ParkingSpotMarker key={spot.id} spot={spot} />
          ))}
        </MapView>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1 },
  mapContainer: { flex: 1 },
  loadingOverlay: {
    position: "absolute",
    top: 16,
    right: 16,
    zIndex: 10,
    padding: 8,
    borderRadius: 8,
    backgroundColor: "rgba(0,0,0,0.15)",
  },
});


