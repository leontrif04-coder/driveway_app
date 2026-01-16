// MSW request handlers for API mocking
import { http, HttpResponse } from "msw";

const API_BASE_URL = "http://127.0.0.1:8000";

export const handlers = [
  // GET /api/v1/spots
  http.get(`${API_BASE_URL}/api/v1/spots`, ({ request }) => {
    const url = new URL(request.url);
    const lat = parseFloat(url.searchParams.get("lat") || "0");
    const lng = parseFloat(url.searchParams.get("lng") || "0");
    const radius_m = parseFloat(url.searchParams.get("radius_m") || "1000");

    // Mock spots near the requested location
    const spots = [
      {
        id: "spot-1",
        latitude: lat + 0.001,
        longitude: lng + 0.001,
        street_name: "Test Street",
        max_duration_minutes: 120,
        price_per_hour_usd: 4.0,
        safety_score: 80.0,
        tourism_density: 70.0,
        meter_status: "working",
        meter_status_confidence: 0.9,
        distance_to_user_m: 141.0,
        review_count: 5,
        last_updated_at: new Date().toISOString(),
        score: 85.0,
      },
      {
        id: "spot-2",
        latitude: lat + 0.002,
        longitude: lng + 0.002,
        street_name: "Test Avenue",
        max_duration_minutes: 60,
        price_per_hour_usd: 3.0,
        safety_score: 60.0,
        tourism_density: 50.0,
        meter_status: "broken",
        meter_status_confidence: 0.8,
        distance_to_user_m: 283.0,
        review_count: 3,
        last_updated_at: new Date().toISOString(),
        score: 70.0,
      },
    ];

    return HttpResponse.json(spots);
  }),

  // GET /api/v1/spots/:id
  http.get(`${API_BASE_URL}/api/v1/spots/:id`, ({ params }) => {
    const { id } = params;
    if (id === "non-existent") {
      return HttpResponse.json({ detail: "Spot not found" }, { status: 404 });
    }

    return HttpResponse.json({
      id,
      latitude: 40.7128,
      longitude: -74.006,
      street_name: "Test Street",
      safety_score: 80.0,
      tourism_density: 70.0,
      meter_status: "working",
      meter_status_confidence: 0.9,
      review_count: 5,
      last_updated_at: new Date().toISOString(),
      score: 85.0,
    });
  }),

  // GET /api/v1/spots/:id/reviews
  http.get(`${API_BASE_URL}/api/v1/spots/:id/reviews`, ({ params }) => {
    const { id } = params;
    if (id === "non-existent") {
      return HttpResponse.json({ detail: "Spot not found" }, { status: 404 });
    }

    return HttpResponse.json([
      {
        id: "rev-1",
        spot_id: id,
        rating: 5,
        text: "Great parking spot!",
        created_at: new Date().toISOString(),
      },
      {
        id: "rev-2",
        spot_id: id,
        rating: 4,
        text: "Good location",
        created_at: new Date().toISOString(),
      },
    ]);
  }),

  // POST /api/v1/spots/:id/reviews
  http.post(`${API_BASE_URL}/api/v1/spots/:id/reviews`, async ({ params, request }) => {
    const { id } = params;
    if (id === "non-existent") {
      return HttpResponse.json({ detail: "Spot not found" }, { status: 404 });
    }

    const body = await request.json();
    return HttpResponse.json({
      id: "rev-new",
      spot_id: id,
      rating: (body as any).rating,
      text: (body as any).text,
      created_at: new Date().toISOString(),
    });
  }),
];

