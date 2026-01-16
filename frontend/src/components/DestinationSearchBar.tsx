// frontend/src/components/DestinationSearchBar.tsx
import React, { useState } from "react";
import { View, TextInput, StyleSheet, Button } from "react-native";

interface Props {
  onDestinationSelected: (coords: { latitude: number; longitude: number }) => void;
}

export const DestinationSearchBar: React.FC<Props> = ({
  onDestinationSelected,
}) => {
  const [query, setQuery] = useState("");

  const handleSearch = () => {
    // TODO: integrate a real geocoding service
    // For now, just a placeholder that centers somewhere fixed.
    onDestinationSelected({ latitude: 40.7128, longitude: -74.006 });
  };

  return (
    <View style={styles.container}>
      <TextInput
        placeholder="Search destination (e.g. restaurant)"
        value={query}
        onChangeText={setQuery}
        style={styles.input}
      />
      <Button title="Go" onPress={handleSearch} />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    backgroundColor: "white",
    flexDirection: "row",
    alignItems: "center",
    zIndex: 20,
  },
  input: {
    flex: 1,
    marginRight: 8,
    borderWidth: 1,
    borderColor: "#ddd",
    borderRadius: 6,
    paddingHorizontal: 8,
    paddingVertical: 4,
    fontSize: 14,
  },
});


