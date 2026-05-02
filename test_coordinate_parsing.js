// Test the coordinate parsing logic

function extractCoordinates(google_place_location) {
  let lat = null, lng = null;
  
  if (google_place_location) {
    try {
      // Try parsing as JSON first
      const locData = JSON.parse(google_place_location);
      lat = locData.lat || locData.latitude;
      lng = locData.lng || locData.longitude;
    } catch (e) {
      // If JSON parsing fails, try comma-separated format: "lat,lng"
      if (typeof google_place_location === 'string' && google_place_location.includes(',')) {
        const parts = google_place_location.split(',');
        if (parts.length === 2) {
          lat = parseFloat(parts[0].trim());
          lng = parseFloat(parts[1].trim());
        }
      }
    }
  }
  
  return { lat, lng };
}

// Test cases from the screenshot
const testCases = [
  '{"lat":12.9638673,"lng":77.5942386}',
  '{"lat":12.8550228,"lng":77.5420548}',
  '{"lat":12.9325666,"lng":77.5307467}',
  '12.7932376,77.7412678',
  '{"lat":13.025872,"lng":77.662627}',
  null,
  ''
];

console.log('Testing coordinate extraction:\n');
testCases.forEach((testCase, i) => {
  const result = extractCoordinates(testCase);
  console.log(`Test ${i + 1}: ${testCase}`);
  console.log(`  Result: lat=${result.lat}, lng=${result.lng}`);
  console.log(`  Status: ${result.lat && result.lng ? '✅ SUCCESS' : '❌ FAILED'}\n`);
});
