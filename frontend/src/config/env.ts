// frontend/src/config/env.ts
// For dev: adjust URL depending on simulator/emulator
// - iOS simulator: http://127.0.0.1:8000
// - Android emulator: http://10.0.2.2:8000

export const API_BASE_URL =
  process.env.EXPO_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";


