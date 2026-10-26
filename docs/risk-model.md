# Weather risk and route recommendation model

The domain model is implemented as pure Python so it can be tested without the
database or external providers.

## Boundary policy

The assessment table contains touching ranges. To keep classification deterministic,
each boundary belongs to the higher risk band. The stated strict No Travel boundaries
for rain and snow remain strict:

- Rain at exactly `1.00 in/hr` is Severe; values above `1.00` are No Travel.
- Snow at exactly `3.00 in/hr` is Severe; values above `3.00` are No Travel.
- Wind at `55 mph` or higher is No Travel.

## Load adjustments

- Wind of at least `55 mph` is No Travel for every load.
- Wind from `45` through `54 mph` becomes No Travel above `30,000 lb`.
- Wind from `35` through `44 mph` becomes Severe above `40,000 lb`.

The checkpoint risk is the highest risk produced by wind, rain, snow, and applicable
load adjustments.

## Route recommendation

Routes containing No Travel mileage are ranked behind travelable routes as a safety
gate. Remaining comparison follows the assessment brief exactly:

1. Fewest Severe miles
2. Fewest High-risk miles
3. Lowest distance-weighted average risk score
4. Shortest travel time

Route ID is used only as a deterministic technical tie-breaker when all business
criteria are equal.
