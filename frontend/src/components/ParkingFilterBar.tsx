// frontend/src/components/ParkingFilterBar.tsx
import React, { useState, useEffect } from "react";
import { View, Text, StyleSheet } from "react-native";
import type { ParkingFilters } from "../domain/models";
import { Picker } from "@react-native-picker/picker";

interface Props {
  onChange: (filters: ParkingFilters) => void;
}

export const ParkingFilterBar: React.FC<Props> = ({ onChange }) => {
  const [minSafetyScore, setMinSafetyScore] = useState<number>(60);
  const [maxWalkingDistanceM, setMaxWalkingDistanceM] = useState<number>(800);
  const [timeOfDay, setTimeOfDay] =
    useState<ParkingFilters["timeOfDay"]>("evening");
  const [tourismBias, setTourismBias] =
    useState<ParkingFilters["tourismBias"]>("medium");

  useEffect(() => {
    onChange({
      minSafetyScore,
      maxWalkingDistanceM,
      timeOfDay,
      tourismBias,
    });
  }, [minSafetyScore, maxWalkingDistanceM, timeOfDay, tourismBias, onChange]);

  return (
    <View style={styles.container}>
      <View style={styles.row}>
        <Text style={styles.label}>Min safety: {minSafetyScore}</Text>
      </View>

      <View style={styles.row}>
        <Text style={styles.label}>
          Max walk: {(maxWalkingDistanceM / 1000).toFixed(1)} km
        </Text>
      </View>

      <View style={styles.row}>
        <Picker
          style={styles.picker}
          selectedValue={timeOfDay}
          onValueChange={(value) =>
            setTimeOfDay(value as ParkingFilters["timeOfDay"])
          }
        >
          <Picker.Item label="Morning" value="morning" />
          <Picker.Item label="Afternoon" value="afternoon" />
          <Picker.Item label="Evening" value="evening" />
          <Picker.Item label="Night" value="night" />
        </Picker>

        <Picker
          style={styles.picker}
          selectedValue={tourismBias}
          onValueChange={(value) =>
            setTourismBias(value as ParkingFilters["tourismBias"])
          }
        >
          <Picker.Item label="Low tourism" value="low" />
          <Picker.Item label="Medium" value="medium" />
          <Picker.Item label="High tourism" value="high" />
        </Picker>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    backgroundColor: "white",
    elevation: 2,
    zIndex: 10,
  },
  row: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 4,
  },
  label: {
    fontSize: 12,
  },
  picker: {
    flex: 1,
    height: 32,
  },
});


