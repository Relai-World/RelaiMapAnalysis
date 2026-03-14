# 🧮 Growth & Investment Score Calculation Guide

## Overview

Your system calculates **Growth Score** and **Investment Score** from the `news_balanced_corpus` table using sentiment analysis and article volume.

---

## 📊 DATA FLOW

```
news_balanced_corpus (raw articles)
    ↓
Sentiment Analysis (FinBERT)
    ↓
compute_location_insights.py (aggregation)
    ↓
location_insights table (scores)
    ↓
API → Frontend display
```

---

## 🗂️ SOURCE TABLE: news_balanced_corpus

### Schema:
```sql
CREATE TABLE news_balanced_corpus (
    id SERIAL PRIMARY KEY,
    location_id INTEGER,          -- Which location
    category VARCHAR,              -- Theme (Real Estate, Infrastructure, etc.)
    source VARCHAR,                -- News source name
    url TEXT UNIQUE,               -- Article URL
    content TEXT,                  -- Full article text
    published_at TIMESTAMP,        -- When published
    scraped_at TIMESTAMP,          -- When scraped
    sentiment_label VARCHAR,       -- 'positive', 'negative', 'neutral'
    sentiment_score FLOAT,         -- -1.0 to 1.0 (FinBERT score)
    confidence FLOAT               -- 0.0 to 1.0 (confidence level)
);
```

### Sample Data:
```sql
id | location_id | category      | source      | sentiment_label | sentiment_score | confidence
---|-------------|---------------|-------------|-----------------|-----------------|------------
 1 |     1       | Real Estate   | The Hindu   | positive        |      0.85       |    0.92
 2 |     1       | Infrastructure| Times Now   | negative        |     -0.65       |    0.88
 3 |     2       | Corporate     | Economic T  | neutral         |      0.10       |    0.75
```

---

## 🔢 CALCULATION PROCESS

### File: `aggregation/compute_location_insights.py`

This script runs the aggregation and calculates all scores.

---

## 📈 STEP 1: Fetch Sentiment Data

For each location, it queries:

```python
cur.execute("""
    SELECT
        COUNT(id) AS article_count,
        AVG(sentiment_score) AS avg_sentiment,
        AVG(confidence) AS avg_confidence
    FROM news_balanced_corpus
    WHERE location_id = %s
      AND sentiment_score IS NOT NULL
""", (location_id,))

article_count, avg_sentiment, avg_confidence = cur.fetchone()
```

### What This Gets:
- **article_count**: Total number of articles for this location
- **avg_sentiment**: Average sentiment score (-1.0 to 1.0)
- **avg_confidence**: Average confidence of predictions

### Example:
For **Gachibowli** with 150 articles:
- article_count = 150
- avg_sentiment = 0.25 (slightly positive)
- avg_confidence = 0.87 (87% confident)

---

## 🚀 STEP 2: Calculate Growth Score

### Function: `compute_growth_score(avg_sentiment, article_count)`

**Logic:**
```python
def compute_growth_score(avg_sentiment, article_count):
    """
    Activity-Driven Growth Logic (V2):
    1. Volume is the primary driver of 'Growth'
    2. Sentiment acts as a slight modifier/bonus
    """
    if article_count == 0:
        return 0.0

    # 1. BUZZ SCORE (Logarithmic Scale)
    # 10 articles -> 1.0
    # 100 articles -> 2.0
    # 1000 articles -> 3.0 (Tier 1 Hub)
    buzz = math.log(article_count + 1, 10)
    
    # Normalize Buzz to 0-1 scale (Assuming max ~3000 articles => ~3.5)
    buzz_normalized = clamp(buzz / 3.5)

    # 2. SENTIMENT MODIFIER (Calibrated V3)
    # Map -0.5..0.5 to 0..1 (Matches Frontend Calibration)
    sentiment_normalized = clamp(avg_sentiment + 0.5)
    
    # 3. FINAL WEIGHTED SCORE
    # 80% Buzz (Activity), 20% Sentiment (Quality)
    growth_score = (0.8 * buzz_normalized) + (0.2 * sentiment_normalized)
    
    return clamp(growth_score)
```

### Breakdown:

#### A. Buzz Score (Article Volume)
```python
buzz = math.log(article_count + 1, 10)
buzz_normalized = buzz / 3.5  # Normalize to 0-1
```

**Examples:**
| Articles | Buzz Score | Normalized |
|----------|------------|------------|
| 0        | log(1) = 0  | 0.00       |
| 10       | log(11) ≈ 1.04 | 0.30    |
| 50       | log(51) ≈ 1.71 | 0.49    |
| 100      | log(101) ≈ 2.00 | 0.57    |
| 500      | log(501) ≈ 2.70 | 0.77    |
| 1000     | log(1001) ≈ 3.00 | 0.86    |
| 3000     | log(3001) ≈ 3.48 | 0.99    |

**Why Logarithmic?**
- Prevents locations with massive article counts from dominating
- Gives diminishing returns after certain point
- Rewards activity but caps out reasonably

#### B. Sentiment Modifier
```python
sentiment_normalized = clamp(avg_sentiment + 0.5)
```

**Maps sentiment from:**
- Range: -1.0 to 1.0
- To: 0.0 to 1.0

**Examples:**
| Avg Sentiment | Normalized (+0.5) | Clamped |
|---------------|-------------------|---------|
| -1.0          | -0.5              | 0.0     |
| -0.5          | 0.0               | 0.0     |
| 0.0           | 0.5               | 0.5     |
| 0.25          | 0.75              | 0.75    |
| 0.5           | 1.0               | 1.0     |
| 1.0           | 1.5               | 1.0     |

#### C. Final Growth Score
```python
growth_score = (0.8 * buzz_normalized) + (0.2 * sentiment_normalized)
```

**Weight Distribution:**
- **80%** Article Volume (Buzz)
- **20%** Sentiment Quality

### Complete Example:

**Gachibowli:**
- article_count = 150
- avg_sentiment = 0.25

**Calculations:**
1. Buzz = log(150 + 1, 10) = log(151) ≈ 2.18
2. Buzz Normalized = 2.18 / 3.5 ≈ **0.62**
3. Sentiment Normalized = 0.25 + 0.5 = **0.75**
4. Growth Score = (0.8 × 0.62) + (0.2 × 0.75)
                = 0.496 + 0.15
                = **0.646** (clamped to 0.65)

**Result:** Growth Score = **0.65** (65/100)

---

## 💰 STEP 3: Calculate Investment Score

### Function: `compute_investment_score(growth_score, avg_sentiment)`

**Logic:**
```python
def compute_investment_score(growth_score, avg_sentiment):
    """
    Investment Potential (V2):
    - Highly correlated with Growth (Booming area = Good Investment)
    - But heavily penalized by negative sentiment (Risk factor)
    """
    # Calibrated Sentiment Normalization (Matches Frontend)
    sentiment_normalized = clamp(avg_sentiment + 0.5)
    
    # Investment = 70% Growth Potential + 30% "Vibe Check" (Sentiment)
    # If it's growing but everyone hates it, it's a risky investment
    score = (0.7 * growth_score) + (0.3 * sentiment_normalized)
    
    return clamp(score)
```

### Formula:
```
Investment Score = (0.7 × Growth Score) + (0.3 × Sentiment Normalized)
```

**Weight Distribution:**
- **70%** Growth Potential (calculated above)
- **30%** Sentiment Quality ("Vibe Check")

### Complete Example (Continuing Gachibowli):

From before:
- growth_score = 0.65
- avg_sentiment = 0.25
- sentiment_normalized = 0.75

**Calculation:**
Investment Score = (0.7 × 0.65) + (0.3 × 0.75)
                 = 0.455 + 0.225
                 = **0.68** (68/100)

**Result:** Investment Score = **0.68**

---

## 📊 COMPLETE CALCULATION EXAMPLE

### Location: HITEC City

**Raw Data from news_balanced_corpus:**
```sql
SELECT COUNT(*), AVG(sentiment_score)
FROM news_balanced_corpus
WHERE location_id = 2;  -- HITEC City

Result: 
article_count = 200
avg_sentiment = 0.18
```

**Step-by-Step Calculation:**

1. **Buzz Score:**
   - buzz = log(200 + 1, 10) = log(201) ≈ 2.30
   - buzz_normalized = 2.30 / 3.5 = **0.66**

2. **Sentiment Normalized:**
   - sentiment_normalized = 0.18 + 0.5 = **0.68**

3. **Growth Score:**
   - growth = (0.8 × 0.66) + (0.2 × 0.68)
   - growth = 0.528 + 0.136
   - growth = **0.66** (66/100)

4. **Investment Score:**
   - investment = (0.7 × 0.66) + (0.3 × 0.68)
   - investment = 0.462 + 0.204
   - investment = **0.67** (67/100)

**Final Scores:**
- Growth Score: **0.66** ⭐⭐⭐ (Moderate)
- Investment Score: **0.67** ⭐⭐⭐ (Good)

---

## 🎯 SCORE INTERPRETATION

### Growth Score Ranges:

| Score | Label | Meaning | Typical Profile |
|-------|-------|---------|-----------------|
| 0.8-1.0 | 🚀 Strong | High growth area | Many articles, positive sentiment |
| 0.6-0.8 | 📈 Moderate | Steady growth | Good article count, mixed sentiment |
| 0.4-0.6 | 📊 Developing | Emerging area | Moderate activity |
| 0.2-0.4 | 🐌 Slow | Limited growth | Few articles |
| 0.0-0.2 | ⚠️ Stagnant | Very low activity | Almost no news coverage |

### Investment Score Ranges:

| Score | Label | Meaning | Recommendation |
|-------|-------|---------|----------------|
| 0.7-1.0 | 💎 Excellent | Prime investment | Strong buy signal |
| 0.5-0.7 | ✅ Good | Solid choice | Worth considering |
| 0.3-0.5 | 😐 Average | Mixed signals | Research more |
| 0.1-0.3 | ⚠️ Risky | Uncertain | Proceed with caution |
| 0.0-0.1 | ❌ Poor | High risk | Avoid |

---

## 🔄 HOW TO UPDATE SCORES

### Run the Aggregation Script:

```bash
cd "c:\Users\gudde\OneDrive\Desktop\Final"
python aggregation/compute_location_insights.py
```

This will:
1. ✅ Fetch all locations
2. ✅ Query `news_balanced_corpus` for each
3. ✅ Calculate new scores
4. ✅ Update `location_insights` table
5. ✅ Ready for API to serve

### After Running New Scraper:

If you scrape new articles (e.g., Future Development theme):

1. **Run scraper** → adds articles to `news_balanced_corpus`
2. **Run sentiment analysis** → updates `sentiment_score` column
3. **Run aggregation** → recalculates all scores
4. **Scores updated** → frontend shows new values

---

## 📝 SMART FACTS GENERATION

### File: `aggregation/generate_smart_facts.py`

This creates human-readable summaries from the scores.

### For Growth Score:

```python
def generate_growth_summary(location_id, cur):
    # Fetch infrastructure data
    cur.execute("""
        SELECT hospitals, schools, metro, airports 
        FROM location_infrastructure 
        WHERE location_id = %s
    """, (location_id,))
    
    h, s, m, a = row
    
    features = []
    if m > 0: features.append("Metro connectivity")
    if h > 2: features.append("major healthcare")
    if s > 3: features.append("schooling hubs")
    if a > 0: features.append("airport access")
    
    if not features:
        return "Developing area with emerging infrastructure."
    
    joined = ", ".join(features)
    return f"Well-connected zone featuring {joined}."
```

**Output Examples:**
- "Well-connected zone featuring Metro connectivity, major healthcare, schooling hubs."
- "Developing area with emerging infrastructure."

### For Investment Score:

```python
def generate_invest_summary(location_id, cur):
    # Fetch price trends
    cur.execute("SELECT year, avg_price_sqft FROM price_trends WHERE location_id = %s ORDER BY year ASC")
    
    # Calculate CAGR
    cagr = (pow(end_price / start_price, 1/years) - 1) * 100
    
    if cagr > 10:
        return f"High Appreciation: +{cagr:.1f}% Annual Growth. Strong capital gains potential."
    elif cagr > 5:
        return f"Steady Yield: {cagr:.1f}% CAGR offers a balanced risk-reward profile."
    else:
        return f"Stable Market: {cagr:.1f}% CAGR indicates value preservation over speculation."
```

**Output Examples:**
- "High Appreciation: +12.5% Annual Growth. Strong capital gains potential."
- "Steady Yield: 7.2% CAGR offers a balanced risk-reward profile."

---

## 🔍 VERIFY CURRENT SCORES

### Check Specific Location:

```sql
SELECT 
    l.name as location,
    li.avg_sentiment_score,
    li.growth_score,
    li.investment_score,
    (SELECT COUNT(*) FROM news_balanced_corpus WHERE location_id = l.id) as article_count
FROM location_insights li
JOIN locations l ON li.location_id = l.id
WHERE l.name = 'Gachibowli';
```

### See All Locations Ranked:

```sql
SELECT 
    l.name as location,
    ROUND(li.growth_score::numeric, 2) as growth,
    ROUND(li.investment_score::numeric, 2) as investment,
    ROUND(li.avg_sentiment_score::numeric, 2) as sentiment,
    (SELECT COUNT(*) FROM news_balanced_corpus WHERE location_id = l.id) as articles
FROM location_insights li
JOIN locations l ON li.location_id = l.id
ORDER BY li.investment_score DESC;
```

---

## 🎨 FRONTEND DISPLAY

### In `frontend/app.js`:

The scores are displayed as percentages:

```javascript
// Convert to percentage
const growthVal = (p.growth_score * 10).toFixed(0);  // 0.65 → 65%
const investVal = (p.investment_score * 10).toFixed(0);  // 0.68 → 68%
const sentimentScore = ((p.avg_sentiment + 1) * 50).toFixed(0);  // Maps -1..1 to 0..100
```

### Color Coding:

**Growth:**
- ≥70% → 🟢 Positive (Green)
- 45-70% → 🟡 Neutral (Yellow)
- <45% → 🔴 Negative (Red)

**Investment:**
- ≥70% → 🟢 Positive (Green)
- 40-70% → 🟡 Neutral (Yellow)
- <40% → 🔴 Negative (Red)

**Sentiment:**
- ≥60% → 🟢 Positive
- 35-60% → 🟡 Neutral
- <35% → 🔴 Negative

---

## 📊 IMPACT OF NEW THEMES

When you add the **Future Development** scraper:

### Current Themes (6 themes):
1. Real Estate
2. Infrastructure
3. Safety
4. Lifestyle
5. Corporate
6. Transport

### Adding Future Development (6 more themes):
7. Future Infrastructure
8. Upcoming Projects
9. Government Plans
10. Real Estate Future
11. Transportation Future
12. Smart City

### Impact on Scores:

**More articles → Higher Buzz Score → Higher Growth Score**

Example:
- Before: 150 articles → buzz = 0.62
- After: 300 articles → buzz = 0.70
- Growth increases: 0.65 → 0.72

**Expected Impact:**
- Locations with lots of future development news will see **significant score increases**
- Areas with few articles won't change much
- Overall scores become more accurate with more data

---

## ✅ SUMMARY

### Key Formulas:

1. **Buzz Score** = log(article_count + 1) / 3.5
2. **Sentiment Normalized** = avg_sentiment + 0.5
3. **Growth Score** = (0.8 × Buzz) + (0.2 × Sentiment)
4. **Investment Score** = (0.7 × Growth) + (0.3 × Sentiment)

### Data Sources:

| Score | Primary Source | Secondary Source |
|-------|----------------|------------------|
| Growth | Article Count (80%) | Sentiment (20%) |
| Investment | Growth Score (70%) | Sentiment (30%) |

### Files Involved:

1. **Scraper**: Adds articles to `news_balanced_corpus`
2. **Sentiment Analysis**: Calculates `sentiment_score`
3. **Aggregation** (`compute_location_insights.py`): Computes final scores
4. **Smart Facts** (`generate_smart_facts.py`): Generates summaries
5. **API** (`api.py`): Serves to frontend
6. **Frontend** (`app.js`): Displays scores

---

**Ready to run your Future Development scraper!** 🚀

After scraping completes, just run:
```bash
python aggregation/compute_location_insights.py
```

And all scores will be automatically updated with the new data! 📈
