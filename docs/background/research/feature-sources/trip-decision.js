const { policy } = require("../data/itinerary");

/**
 * Picks the best alternate flight and checks it against policy.
 * Returns a decision object the Action Layer and UI both consume.
 */
function evaluate(scenario) {
  // Best alternate = lowest delay among options that don't require
  // a fare-class upgrade, if allowed; otherwise the only option we have.
  const sorted = [...scenario.alternates].sort(
    (a, b) => a.delayMinutes - b.delayMinutes
  );
  const best = sorted[0];

  const requiresUpgrade =
    best.fareClass !== undefined &&
    best.fareClass === "First" &&
    !policy.allowFareClassUpgrade;

  const withinDelay = best.delayMinutes <= policy.maxDelayMinutesAutoApprove;
  const withinCost = best.cost <= policy.maxAdditionalCostAutoApprove;

  const withinPolicy = withinDelay && withinCost && !requiresUpgrade;

  const reasons = [];
  if (!withinDelay) {
    reasons.push(
      `delay of ${best.delayMinutes} min exceeds the ${policy.maxDelayMinutesAutoApprove} min auto-approve limit`
    );
  }
  if (!withinCost) {
    reasons.push(
      `additional cost of $${best.cost} exceeds the $${policy.maxAdditionalCostAutoApprove} auto-approve limit`
    );
  }
  if (requiresUpgrade) {
    reasons.push("selected option requires a fare-class upgrade, which needs manual approval");
  }

  return {
    chosenAlternate: best,
    withinPolicy,
    escalationReasons: reasons
  };
}

/**
 * Builds the plain-language explanation shown to the card member.
 * Falls back to a template if no ANTHROPIC_API_KEY is configured —
 * so the demo works with zero setup. Swap in a real Claude call by
 * setting ANTHROPIC_API_KEY in the environment.
 */
async function explain({ decision, itinerary, disruption, hotelAdjustment }) {
  const key = process.env.ANTHROPIC_API_KEY;
  if (!key) {
    return templateExplanation({ decision, itinerary, disruption, hotelAdjustment });
  }

  try {
    const prompt = buildPrompt({ decision, itinerary, disruption, hotelAdjustment });
    const res = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-api-key": key,
        "anthropic-version": "2023-06-01"
      },
      body: JSON.stringify({
        model: "claude-sonnet-4-6",
        max_tokens: 300,
        messages: [{ role: "user", content: prompt }]
      })
    });
    const data = await res.json();
    const text = (data.content || [])
      .filter((b) => b.type === "text")
      .map((b) => b.text)
      .join(" ")
      .trim();
    return text || templateExplanation({ decision, itinerary, disruption, hotelAdjustment });
  } catch (err) {
    console.error("Claude explain() call failed, using template fallback:", err.message);
    return templateExplanation({ decision, itinerary, disruption, hotelAdjustment });
  }
}

function buildPrompt({ decision, itinerary, disruption, hotelAdjustment }) {
  return `You are the transparency layer of a travel-disruption assistant for a premium credit card member.
Write a short (2-3 sentence), warm, plain-language explanation of what happened and what was done.
No jargon, no bullet points, just a short paragraph.

Facts:
- Original flight ${disruption.flightNumber} was disrupted: ${disruption.reason}
- ${decision.withinPolicy ? "Rebooked" : "Proposed"} alternate: ${decision.chosenAlternate.flightNumber}, arriving about ${decision.chosenAlternate.delayMinutes} minutes later than originally planned
- Additional cost to the member: $${decision.chosenAlternate.cost}
- Hotel adjustment: ${hotelAdjustment ? hotelAdjustment.note : "none needed"}
- Decision outcome: ${decision.withinPolicy ? "resolved automatically within policy" : "escalated to a human agent because: " + decision.escalationReasons.join("; ")}`;
}

function templateExplanation({ decision, itinerary, disruption, hotelAdjustment }) {
  const delayText =
    decision.chosenAlternate.delayMinutes < 60
      ? `${decision.chosenAlternate.delayMinutes} minutes later than planned`
      : `about ${Math.round(decision.chosenAlternate.delayMinutes / 60)} hours later than planned`;

  if (decision.withinPolicy) {
    const costText =
      decision.chosenAlternate.cost > 0
        ? `for an additional $${decision.chosenAlternate.cost}`
        : "at no extra cost";
    const hotelText = hotelAdjustment
      ? ` ${hotelAdjustment.note}.`
      : "";
    return `Your flight ${disruption.flightNumber} was cancelled (${disruption.reason.toLowerCase()}). We rebooked you on ${decision.chosenAlternate.flightNumber}, arriving ${delayText}, ${costText}, in the same fare class you originally booked.${hotelText} This was resolved automatically within your card's travel protection policy.`;
  }

  return `Your flight ${disruption.flightNumber} was cancelled (${disruption.reason.toLowerCase()}). The best available option, ${decision.chosenAlternate.flightNumber}, would arrive ${delayText} and ${decision.escalationReasons.join(
    "; "
  )}. Because this falls outside your policy's auto-approve limits, we've handed this to a human agent with your full case history so they can confirm the best path forward with you.`;
}

module.exports = { evaluate, explain };
