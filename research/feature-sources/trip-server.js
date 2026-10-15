const express = require("express");
const path = require("path");
const { state, scenarios, resetState } = require("./data/itinerary");
const { evaluate, explain } = require("./services/decisionEngine");

const app = express();
app.use(express.json());
app.use(express.static(path.join(__dirname, "..", "public")));

// --- Read current trip state ---
app.get("/api/trip", (req, res) => {
  res.json(state);
});

// --- Reset the demo back to a clean "monitoring" state ---
app.post("/api/reset", (req, res) => {
  res.json(resetState());
});

// --- Trigger a simulated disruption event ---
// body: { scenario: "in_policy" | "out_of_policy" }
app.post("/api/disrupt", async (req, res) => {
  const scenarioKey = req.body.scenario === "out_of_policy" ? "out_of_policy" : "in_policy";
  const scenario = scenarios[scenarioKey];

  const disruption = { ...scenario.disruption, reportedAt: new Date().toISOString() };
  state.status = "DISRUPTED";

  // 1) Decision Engine: evaluate alternates against policy
  const decision = evaluate(scenario);

  // 2) Action Layer: execute or hold for escalation
  if (decision.withinPolicy) {
    state.itinerary.trip.flight = {
      ...state.itinerary.trip.flight,
      number: decision.chosenAlternate.flightNumber,
      status: "REBOOKED",
      departure: decision.chosenAlternate.departure,
      arrival: decision.chosenAlternate.arrival
    };
    if (scenario.hotelAdjustment) {
      state.itinerary.trip.hotel.checkIn = scenario.hotelAdjustment.newCheckIn;
    }
    state.status = "RESOLVED";
  } else {
    state.status = "ESCALATED";
  }

  // 3) Transparency layer: plain-language explanation (LLM or template)
  const reasoning = await explain({
    decision,
    itinerary: state.itinerary,
    disruption,
    hotelAdjustment: scenario.hotelAdjustment
  });

  state.lastDecision = {
    disruption,
    decision,
    reasoning,
    resolvedAt: new Date().toISOString()
  };

  res.json(state);
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`TripGuard AI backend running at http://localhost:${PORT}`);
});
