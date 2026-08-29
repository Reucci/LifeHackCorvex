# Ecolings Weather Analysis Features

This document describes the weather-analysis and weather-to-quest functionality currently implemented in Ecolings.

## 1. Official Singapore weather sources

The backend retrieves official National Environment Agency (NEA) data through data.gov.sg.

Implemented feeds:

- Air temperature
- Relative humidity
- Five-minute rainfall totals
- Mean wind speed
- Two-hour area forecast
- 70 km weather-radar imagery (beta)

Weather calls are made by the FastAPI backend rather than directly by the browser. This provides one consistent source of truth and keeps network handling, caching, validation, and future API credentials on the server.

## 2. Manual Singapore area selection

- The user selects one of the 47 official NEA two-hour forecast areas.
- Browser geolocation is not used.
- The selected area is stored locally for the logged-in account.
- The area choice happens in the frontend; the backend does not infer or select the user's area.
- The frontend sends the selected area's official label coordinates to the backend.
- The backend uses those coordinates for observation-station matching, radar analysis, and retrieval of the corresponding forecast record.
- Changing area refreshes weather and choices for an uncompleted slot.
- Completed slots remain locked to their original weather evidence.

## 3. Nearest-station observation matching

Temperature, humidity, rainfall, and wind do not always share the same reporting stations. The backend therefore selects the nearest available reporting station independently for each measurement.

Selection uses Haversine distance between:

- The selected forecast area's coordinates
- Each station's latitude and longitude

Every observation records:

- Value and unit
- Observation timestamp
- Age in minutes
- Station ID and name
- Station coordinates
- Distance from the selected area
- Whether the observation is stale

## 4. Unit and data normalization

- Temperature is represented in degrees Celsius.
- Humidity is represented as a percentage.
- Rainfall is represented in millimetres.
- NEA wind readings are converted from knots to kilometres per hour.
- Forecast and station data are combined into one normalized weather snapshot.

## 5. Reliability and freshness handling

- Standard observation feeds are cached for four minutes.
- Failed or empty observation requests are retried once.
- A last-known successful cached reading can be used during a short official-feed gap.
- Cached values still retain their original timestamps and can be marked stale.
- Observations older than 30 minutes generate a visible warning.
- Missing non-critical measurements generate warnings without crashing the whole request.
- Temperature is treated as required for quest generation.
- Radar failures do not stop ordinary weather quests; the system falls back to non-radar analysis.

## 6. Two-hour forecast matching

- The backend does not choose the user's forecast area. It matches the coordinates supplied by the user's manual frontend selection to the corresponding official NEA forecast record.
- The nearest-label calculation is a forecast-data lookup using official area coordinates, not automatic user geolocation or area selection.
- The forecast condition and valid period are stored with the weather snapshot.
- Rain-related forecast terms include rain, showers, and thunder.
- The forecast is used alongside observations rather than being treated as a current measurement.

## 7. Weather-radar frame retrieval

The radar system uses NEA's beta 70 km radar product.

- Retrieves the latest frame plus frames from approximately 10 and 20 minutes earlier.
- Deduplicates frames when the official feed returns the same timestamp.
- Downloads temporary official PNG image URLs.
- Processes up to three recent frames for each analysis.
- Caches radar analysis for the selected area's coordinates for four minutes.
- Retries radar integration when the beta feed has a transient failure.

No external image-processing dependency is required. The backend contains a lightweight standard-library decoder for NEA's non-interlaced, 8-bit indexed PNG format.

## 8. Radar rainfall-intensity decoding

The decoder uses NEA's published radar colour legend.

Implemented intensity classes:

- None
- Light
- Light to moderate
- Moderate
- Moderate to heavy
- Heavy

For the selected area, each frame measures:

- Rain intensity within approximately 3 km
- Distance to the nearest rain echo within 35 km
- Intensity of the nearest rain echo
- Approximate coordinates of that echo

## 9. Radar movement analysis

The system compares how the distance to the nearest rain echo changes across recent frames.

Movement classifications:

- `approaching`
- `moving_away`
- `stationary`
- `overhead`
- `no_nearby_rain`
- `insufficient_data`

When rain is approaching, the system estimates minutes to arrival using the observed closure rate. Estimates are limited to a useful 5–120 minute range.

Radar output includes:

- Movement classification
- Estimated arrival time when applicable
- Low, medium, or high confidence
- Local and nearest-echo intensity
- Nearest-echo distance
- Radar observation age
- Number of frames analyzed
- Per-frame evidence
- Analysis method and beta status

## 10. Derived weather features

The quest engine derives deterministic features from normalized observations and radar evidence.

Current thresholds:

- Hot: at least 30°C
- Very hot: at least 33°C
- Very humid: at least 80% relative humidity
- Breezy: at least 10 km/h
- Daylight: 7:00 AM–7:00 PM Singapore time
- Raining: nearest rainfall station reports more than 0 mm
- Rain expected: forecast contains a rain term or radar predicts arrival within two hours
- Sunny: forecast contains fair, sunny, or clear

The current apparent-temperature heuristic adds 0.04°C for each humidity percentage point above 60% when air temperature is at least 27°C. It is used for game comfort decisions and is not presented as an official heat-index or WBGT measurement.

## 11. Weather-safe quest eligibility

Every quest has explicit requirements. Ineligible quests are removed before randomization.

Examples:

- Line drying requires daylight, no observed rain, and no forecast or radar-indicated incoming rain.
- Closing blinds requires daylight and hot conditions.
- Fan-first requires conditions that are not excessively hot according to the comfort heuristic.
- Indoor standby-power quests become eligible during observed or expected rain.
- Outdoor or drying suggestions are withheld when conditions make them unsuitable.

## 12. Predictive quest windows

Every newly generated quest includes an action window with:

- Recommended start time
- Recommended end time
- Human-readable timing guidance
- Confidence level
- Evidence explaining the timing

Implemented predictive cases:

- Approaching radar rain: act before the estimated arrival, with a 10-minute safety buffer.
- Hot daylight conditions: close blinds or delay heat-producing appliances within the next 30 minutes.
- Receding rain: the quest explains that nearby rain is moving away and remains suitable during the slot.
- Stable/general conditions: complete before the current two-hour slot ends.

## 13. Urgent radar opportunity quest

When high-quality radar evidence indicates approaching rain during daylight, one choice is reserved for:

> Bring drying laundry in before the rain.

This protects the energy already saved through natural drying and avoids needing to run the dryer again. The second choice remains randomized from other eligible actions.

## 14. Randomized two-choice recommendations

- Two distinct quests are offered per two-hour slot.
- Only weather-eligible quests enter selection.
- Selection is weighted toward the five strongest weather matches.
- Weather-urgent radar quests are guaranteed one position when applicable.
- The second option preserves user autonomy.
- There is no penalty for repeating a useful habit.
- Random choices are seeded and persisted, so refreshing cannot reroll them.

## 15. Weather-adjusted reward scaling

Quest score starts with base impact and receives bonuses for relevant conditions such as:

- Very hot weather
- Very high humidity
- Sunshine
- Wind
- High-confidence approaching rain

The final slot reward is scaled to 4–15 gold.

Difficulty labels:

- Easy: 4–7 gold
- Medium: 8–11 gold
- Hard: 12–15 gold

The recent-quest penalty was removed to support habit formation.

## 16. Two-hour persistence and completion protection

- Quest slots are aligned to even two-hour boundaries in Singapore time.
- Each user receives one persisted pair of choices per slot.
- Weather evidence, radar analysis, choices, and timing windows are stored together.
- Refreshing returns the same choices.
- Only one of the two options can be completed in each slot.
- The completion request must reference both the slot and an offered quest key.
- Invalid or expired-slot submissions are rejected.
- Gold can be earned in multiple slots, while the daily streak changes at most once per day.

## 17. Frontend weather evidence

The dashboard displays:

- Manually selected area
- Current temperature and forecast condition
- Nearest station name and distance
- Observation age
- Humidity
- Forecast area
- Stale or missing-feed warnings
- Radar movement
- Nearest rain distance
- Estimated rain arrival when available
- Radar confidence
- Quest timing window and its evidence
- Quest difficulty and reward

## 18. Current limitations

- The radar API is officially beta and may change or become temporarily unavailable.
- Radar coordinates are mapped through the published geographic bounding box. This is an approximation of the source's azimuthal-equidistant projection, though the error is small around Singapore.
- Nearest-echo movement is a lightweight nowcasting heuristic, not an official NEA rain-arrival forecast.
- Multiple separate rain cells can make nearest-echo movement less stable.
- Station readings represent outdoor conditions near the station, not conditions inside a building.
- The system estimates action suitability and potential impact; it does not measure actual household electricity use.
- No LLM generates or overrides weather facts.
- Lightning, official WBGT heat stress, notifications, smart-meter integration, and learned per-user completion models are not currently implemented.

## 19. Main implementation files

- `backend/weather_service.py` — official observation and forecast normalization
- `backend/radar_service.py` — radar PNG decoding and movement analysis
- `backend/rules.py` — eligibility, scoring, randomization, and predictive windows
- `backend/main.py` — authenticated weather and quest endpoints
- `backend/models.py` — persisted users, sessions, and quest slots
- `frontend/src/App.jsx` — manual area selection and weather/quest presentation
- `frontend/src/App.css` — weather, radar, and predictive-window interface styling
