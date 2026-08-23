import json

with open("../outputs/recommendations.json") as f:
    data = json.load(f)

print("Budget:", data["budget"])
print("Total recommended customers:", data["total_recommended_customers"])
print("Total expected profit:", data["total_expected_profit"])
print("Total expected cost:", data["total_expected_cost"])

recs = data["recommendations"]
print("\nTotal records in recommendations list:", len(recs))
print("\nFirst 3 recommendations:")
for r in recs[:3]:
    print(json.dumps(r, indent=2))