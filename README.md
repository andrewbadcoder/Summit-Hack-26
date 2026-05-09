# Summit-Hack-26
Summit hack 26 for sustanability

[Phone camera / web upload]
        ↓
[Frontend: React or React Native]
        ↓
   [ClaudeAPI or Cursor]
        ↓
   ┌────┴────┐
   ↓         ↓
[Vision     [LLM reasoning
 model]      layer]
   ↓         ↑
[Classification → structured prompt → recommendation]
        ↓
[Knowledge base: recycling rules, materials DB, dropoff locations]
        ↓
[JSON response → rendered UI card]

What the app actually does
User points phone camera at an item → app returns:

Identification — what it is (e.g., "Lithium-ion 18650 battery")
Recyclability verdict — recycle / e-waste dropoff / hazardous / repair-first / trash, with reasoning
Shelf life or condition — visible damage, swelling (batteries), corrosion, wear indicators
Action steps — nearest dropoff location, manufacturer take-back program, repair guide link
Hazard Concerns — What will happen if the user does not dispose of the device properly, notes any safety concerns
