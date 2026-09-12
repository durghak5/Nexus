export const BASE_URL = "http://localhost:8000/api/v1";

/**
 * Search for drugs by query string.
 * GET /drugs/search?query=...
 * @param {string} query
 * @returns {Promise<Object>} parsed JSON response
 */
export async function searchDrugs(query) {
  const url = `${BASE_URL}/drugs/search?query=${encodeURIComponent(query)}`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Search failed: ${response.status} ${response.statusText}`);
  }
  return response.json();
}

/**
 * Get alternative recommendations for a brand name.
 * GET /drugs/recommendations?brand_name=...
 * @param {string} brandName
 * @returns {Promise<Object>} parsed JSON response
 */
export async function getRecommendations(brandName) {
  const url = `${BASE_URL}/drugs/recommendations?brand_name=${encodeURIComponent(brandName)}`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Recommendations failed: ${response.status} ${response.statusText}`);
  }
  return response.json();
}

/**
 * Get composition details for a brand name.
 * GET /drugs/composition?brand_name=...
 * @param {string} brandName
 * @returns {Promise<Object>} parsed JSON response
 */
export async function getComposition(brandName) {
  const url = `${BASE_URL}/drugs/composition?brand_name=${encodeURIComponent(brandName)}`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Composition failed: ${response.status} ${response.statusText}`);
  }
  return response.json();
}
