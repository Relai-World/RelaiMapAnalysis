# Helpful AI Review Guidelines

## 🎯 Goal: Reviews That Help Users Make Decisions

Users comparing properties need **actionable insights**, not generic descriptions. Reviews should answer:
- **Why should I consider this property?**
- **What are the location advantages?**
- **What should I be aware of?**
- **Who is this property best for?**

## ❌ Bad Review Example (Current)

```
Yoosufguda (near Sanjeevareddy Nagar, Secunderabad) is an under-
construction 3BHK project with 10 units on 0.113 acres, set for
possession in September 2025, featuring a gated community
setup. Residents appreciate the location, proximity to bus stops,
two-side roads, borewell water supply, quick access to ORR/RRR,
local markets, malls, hospitals, and schools within 2-3 km, minimal
power cuts, doorstep cabs, and a safe, low-traffic residential
zone. Construction quality is anticipated to meet promises,
though limited feedback exists due t
```

**Problems:**
- ❌ Cut off mid-sentence ("due t")
- ❌ Too technical and robotic
- ❌ Just lists features without context
- ❌ Doesn't help user decide
- ❌ No structure or flow

## ✅ Good Review Example (Target)

```
IRIS by Aparna Constructions stands out for its prime Somajiguda 
location with excellent connectivity to Hyderabad's business districts 
and entertainment hubs. The property offers premium amenities including 
a clubhouse, swimming pool, and 24/7 security, backed by Aparna's 
strong reputation for quality construction. 

Residents appreciate the well-maintained facilities and responsive 
management. The location provides easy access to schools, hospitals, 
and shopping centers within 2-3 km. Ideal for professionals and 
families seeking a well-connected, upscale living experience in 
central Hyderabad.
```

**Why This Works:**
- ✅ Complete sentences (no cutoff)
- ✅ Highlights what makes it special
- ✅ Mentions location benefits clearly
- ✅ Includes builder reputation
- ✅ States who it's best for
- ✅ Conversational and helpful tone

## 📋 Review Structure

### 1. Opening (What Makes It Special)
Start with the property's standout features or unique selling points.

**Examples:**
- "IRIS by Aparna Constructions stands out for its prime Somajiguda location..."
- "This project offers exceptional value with spacious 3BHK units..."
- "Known for its modern architecture and green spaces..."

### 2. Location & Connectivity
Explain why the location matters to buyers.

**Examples:**
- "Excellent connectivity to business districts and IT hubs"
- "Close to schools, hospitals, and shopping within 2-3 km"
- "Easy access to metro stations and major highways"

### 3. Key Features & Amenities
Mention what residents will enjoy.

**Examples:**
- "Premium amenities including clubhouse, pool, and gym"
- "24/7 security with CCTV surveillance"
- "Power backup and water supply ensured"

### 4. Builder Reputation (if known)
Add credibility with builder track record.

**Examples:**
- "Backed by Aparna's strong reputation for quality"
- "Builder known for timely delivery and good construction"
- "Established developer with multiple successful projects"

### 5. Considerations (if any)
Be honest about any concerns or things to note.

**Examples:**
- "Construction is ongoing, expected completion in 2025"
- "Limited parking may be a concern for multiple car owners"
- "Prices are on the higher side but justified by location"

### 6. Best Suited For
Help users self-identify if this property fits them.

**Examples:**
- "Ideal for professionals seeking central location"
- "Perfect for families with school-age children"
- "Great for investors looking for appreciation potential"

## 🎨 Tone & Style

### Do:
- ✅ Write conversationally (like talking to a friend)
- ✅ Be specific with details (distances, amenities)
- ✅ Be balanced (mention both positives and considerations)
- ✅ Use active voice ("offers", "provides", "features")
- ✅ End with complete sentences

### Don't:
- ❌ Use technical jargon unnecessarily
- ❌ Include citation numbers [1][2][3]
- ❌ Use markdown formatting **bold**
- ❌ Cut off mid-sentence
- ❌ Be overly promotional or negative

## 📏 Length Guidelines

- **Target**: 80-100 words
- **Minimum**: 60 words (too short = not helpful)
- **Maximum**: 120 words (too long = hard to read)
- **Sentences**: 4-6 complete sentences

## 🔍 Quality Checklist

A helpful review should:

- [ ] Start with what makes the property attractive
- [ ] Mention specific location benefits
- [ ] Include key amenities or features
- [ ] Reference builder reputation (if known)
- [ ] Note any important considerations
- [ ] State who the property is best for
- [ ] Be 80-100 words
- [ ] Have complete sentences (no cutoff)
- [ ] No citation numbers [1][2]
- [ ] No markdown **bold**
- [ ] Conversational and friendly tone
- [ ] Help users make a decision

## 💡 Example Reviews for Different Scenarios

### Scenario 1: Premium Property in Prime Location
```
RAMKY ONE GALAXIA PHASE-II by Ramky Estates offers luxury living in 
Gachibowli's IT corridor with excellent connectivity to major tech parks 
and business hubs. The property features premium amenities including a 
state-of-the-art clubhouse, swimming pool, gym, and landscaped gardens. 
Residents praise the quality construction and professional maintenance. 
The location provides easy access to schools, hospitals, and shopping 
centers. Ideal for IT professionals and executives seeking upscale living 
with modern conveniences in Hyderabad's prime tech hub.
```

### Scenario 2: Value-for-Money Property
```
This project offers excellent value with spacious 3BHK units in a 
well-connected neighborhood. The builder has a good track record of 
timely delivery and quality construction. Amenities include power backup, 
security, and children's play area. The location provides good connectivity 
to schools and hospitals within 2-3 km, with bus stops nearby. While not 
ultra-premium, it's a solid choice for families seeking affordable, 
comfortable living with essential amenities and good location.
```

### Scenario 3: Under-Construction Property
```
This upcoming project by an established builder promises modern amenities 
and good connectivity to the business district. Construction is progressing 
well with expected completion in late 2025. The location offers proximity 
to schools, hospitals, and shopping areas. Early buyers may benefit from 
attractive pricing and appreciation potential. However, as with any 
under-construction property, buyers should verify completion timelines 
and builder credentials. Best suited for investors or buyers planning 
for future occupancy.
```

## 🚀 Implementation Changes

### Updated System Prompt:
```
You are a helpful real estate advisor. Write property reviews that help 
buyers make informed decisions.

Structure your reviews like this:
- Start with what makes the property attractive
- Mention location benefits and connectivity
- Include any important considerations or concerns
- End with who this property is best suited for

Write in a friendly, conversational tone. Be honest and balanced. 
Keep it under 100 words. Do NOT include citation numbers.
```

### Updated Search Query:
```
Analyze {project_name} by {builder_name} in {area_name}, India as a 
property investment.

Provide a helpful review covering:
1. What makes this property stand out (unique features, quality)
2. Location advantages (connectivity, nearby facilities)
3. What buyers should know (construction status, pricing, any concerns)

Write in a friendly, informative tone that helps buyers make decisions. 
Keep it under 100 words.
```

### Key Changes:
1. **Increased max_tokens**: 150 → 200 (prevents cutoff)
2. **Better temperature**: 0.2 → 0.3 (more natural language)
3. **Sentence completion check**: Removes incomplete sentences
4. **Fallback text**: If review too short, provides basic info
5. **Improved cleanup**: Removes citations and markdown

## 📊 Before vs After

| Aspect | Before | After |
|--------|--------|-------|
| **Tone** | Technical, robotic | Conversational, helpful |
| **Structure** | Random facts | Logical flow |
| **Completeness** | Cut off mid-sentence | Complete sentences |
| **Helpfulness** | Lists features | Explains benefits |
| **Decision Support** | None | "Best suited for..." |
| **Length** | 98+ words | 80-100 words |
| **Readability** | Poor | Good |

## ✅ Success Criteria

Reviews are successful when users can answer:
1. ✅ "What makes this property special?"
2. ✅ "Is the location good for me?"
3. ✅ "What amenities will I get?"
4. ✅ "Are there any concerns?"
5. ✅ "Is this property right for me?"

---

**Next Steps:**
1. Restart backend server
2. Clear old reviews from database
3. Test with `python test_helpful_review.py`
4. Verify reviews are helpful and complete
