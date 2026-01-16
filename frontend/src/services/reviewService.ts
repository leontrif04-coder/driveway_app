// frontend/src/services/reviewService.ts
import { API_BASE_URL } from "../config/env";

export interface RawReview {
  id: string;
  text: string;
  rating: number;
  createdAt: string;
}

export const reviewService = {
  async getReviewsForSpot(spotId: string): Promise<RawReview[]> {
    const res = await fetch(`${API_BASE_URL}/api/v1/spots/${spotId}/reviews`);
    if (!res.ok) {
      throw new Error(`Failed to fetch reviews: ${res.status}`);
    }
    const json = await res.json();
    return json.map((r: any) => ({
      id: r.id,
      text: r.text,
      rating: r.rating,
      createdAt: r.created_at,
    }));
  },

  async submitReview(spotId: string, rating: number, text: string): Promise<void> {
    const res = await fetch(`${API_BASE_URL}/api/v1/spots/${spotId}/reviews`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ rating, text }),
    });
    if (!res.ok) {
      throw new Error(`Failed to submit review: ${res.status}`);
    }
  },
};


