# Real Estate Intelligence Platform — Hyderabad City-Wide Scaling
## Implementation Timeline & Execution Plan

**Company:** Relai  
**Document Type:** Project Scaling Timeline  
**Date:** February 15, 2026  
**Version:** 1.0  
**Author:** Development Team  
**Start Date:** February 19, 2026 (Thursday)  
**Target Completion:** March 28, 2026  

---

## 1. Executive Summary

This document outlines the execution plan for scaling the Real Estate Intelligence Platform from a **7-location Proof of Concept (West Hyderabad)** to a **production-grade system covering ~300 micro-market locations across all of Hyderabad**.

The current system has a fully validated pipeline — web scraping, FinBERT sentiment analysis, PostGIS aggregation, and interactive map visualization — operational for 7 locations. The objective is to extend this pipeline city-wide while maintaining data quality, system reliability, and platform performance.

### Current Baseline

| Metric | Status |
|--------|--------|
| Locations with full pipeline (Scrape → FinBERT → Scores) | 7 (West Hyderabad) |
| Locations with CSV-imported data only | ~293 |
| Total target locations | ~300 |
| Working infrastructure | PostgreSQL + PostGIS, FastAPI, MapLibre GL, Playwright Scrapers |
| Sentiment model | FinBERT (ProsusAI/finbert) — validated |
| Frontend | Interactive vector map with Intel Card, search, layers |

### Scaling Objective

| From | To |
|------|----|
| 7 locations with real sentiment | **~300 locations with real sentiment** |
| Manual scraping triggers | **Automated bi-weekly refresh cycle** |
| Single-area coverage | **City-wide coverage (all Hyderabad zones)** |
| Development environment | **Production-ready deployment** |

---

## 2. Development Approach

### Solo Developer + AI Agent Model
This project is executed by a **single developer augmented with an AI coding agent**, which significantly compresses traditional development timelines:

- **Code generation & boilerplate:** Handled by AI agent
- **Research & debugging:** AI-assisted, reducing resolution time by 60-70%
- **Documentation:** Auto-generated alongside development
- **Testing & validation:** Parallel execution with AI support

**Estimated acceleration factor:** 2.5x–3x compared to solo development without AI assistance.

---

## 3. Phase Breakdown

---

### Phase 1: Scraping Architecture Overhaul
**Duration:** 5 days (Feb 19 – Feb 25)  
**Objective:** Transform the scraping system from individual-location queries to a city-wide harvesting model capable of covering ~300 locations efficiently.

#### Why the Current Approach Won't Scale
The existing scraper (`scrape_playwright.py`) fires queries like *"Gachibowli Hyderabad real estate"* — one query per location. For 300 locations across 5 themes, that's **1,500 queries**, which will:
- Trigger Google's anti-bot defenses
- Take days to complete
- Miss cross-location articles

#### The Solution: Inverted Scraping + NER Tagging

| Day | Task | Deliverable |
|-----|------|-------------|
| **Day 1** (Thu, Feb 19) | Design the Inverted Scraping architecture | Architecture document + flow diagram |
| | — Define city-wide query templates (e.g., *"Hyderabad real estate 2026"*, *"Hyderabad metro infrastructure"*) | |
| | — Map out 8-10 broad query categories covering: Real Estate, Infrastructure, Transport, Lifestyle, Safety, Corporate, Education, Healthcare | |
| **Day 2** (Fri, Feb 20) | Build the Named Entity Recognition (NER) Tagger | Working NER module |
| | — Create a location registry of all ~300 location names + aliases (e.g., "Gachi" → "Gachibowli", "HITEC City" → "Hi-Tech City") | |
| | — Implement fuzzy matching logic for location detection in article text | |
| | — Test NER accuracy on sample articles (target: >90% precision) | |
| **Day 3** (Sat, Feb 22) | Re-architect the Playwright scraper for city-wide queries | Modified `scrape_playwright.py` |
| | — Implement proxy rotation system (to avoid IP blocking) | |
| | — Add rate limiting (2-3 second delays between requests) | |
| | — Build retry logic with exponential backoff | |
| **Day 4** (Mon, Feb 24) | Build a scraping queue & job management system | Queue system + logging |
| | — Track which queries have been executed & when | |
| | — Implement incremental scanning (only fetch articles newer than last run) | |
| | — Add deduplication logic (same article appearing in multiple queries) | |
| **Day 5** (Tue, Feb 25) | Execute the first full city-wide scrape (2024-2026 data) | Raw articles in database |
| | — Run all query templates across Google News RSS | |
| | — Tag articles to locations via NER | |
| | — Store in `raw_articles` table with metadata (source, date, location_id, raw_text) | |
| | — **Expected yield:** 3,000–6,000 articles | |

#### Phase 1 Exit Criteria
- [ ] City-wide scraper operational and tested
- [ ] NER tagger achieving >90% location-matching accuracy
- [ ] 3,000+ raw articles harvested and stored in database
- [ ] Articles tagged to their respective locations
- [ ] Proxy rotation and rate limiting active

---

### Phase 2: FinBERT Sentiment Processing at Scale
**Duration:** 4 days (Feb 26 – Mar 1)  
**Objective:** Process all harvested articles through FinBERT and generate real sentiment scores for ~300 locations.

| Day | Task | Deliverable |
|-----|------|-------------|
| **Day 6** (Wed, Feb 26) | Set up GPU processing environment | GPU pipeline ready |
| | — Configure Google Colab Pro (or local GPU if available) | |
| | — Create batch processing script (process 200-500 articles per batch) | |
| | — Implement progress tracking & checkpointing (resume if interrupted) | |
| **Day 7** (Thu, Feb 27) | Run FinBERT inference — Batch 1 | ~50% articles processed |
| | — Process first half of articles (~1,500–3,000) | |
| | — Store per-article sentiment scores in `processed_sentiment_data` table | |
| | — Monitor for quality: spot-check 20 articles manually | |
| **Day 8** (Fri, Feb 28) | Run FinBERT inference — Batch 2 | All articles processed |
| | — Process remaining articles | |
| | — Validate: ensure every article has a sentiment score | |
| | — Generate processing report (articles per location distribution) | |
| **Day 9** (Sat, Mar 1) | Score Aggregation & Database Update | Updated `location_insights` |
| | — Run aggregation logic: calculate weighted average sentiment per location | |
| | — Compute derived scores: `growth_score`, `investment_score` from sentiment + infrastructure data | |
| | — Update `location_insights` table: replace CSV-based scores with real FinBERT-derived scores | |
| | — **Validation:** Compare old (CSV) vs new (FinBERT) scores for 20 sample locations | |

#### Phase 2 Exit Criteria
- [ ] All harvested articles processed through FinBERT
- [ ] Sentiment scores stored in `processed_sentiment_data`
- [ ] Aggregated scores computed for all ~300 locations
- [ ] `location_insights` table updated with real sentiment-derived scores
- [ ] Quality validation passed on sample locations

---

### Phase 3: Price Trends & Analytics Enhancement
**Duration:** 3 days (Mar 3 – Mar 5)  
**Objective:** Ensure price trend data and analytics features are complete and accurate for all ~300 locations.

| Day | Task | Deliverable |
|-----|------|-------------|
| **Day 10** (Mon, Mar 3) | Price data validation & gap-filling | Complete `price_trends` table |
| | — Audit existing price data for all 300 locations | |
| | — Identify locations with missing or incomplete price history | |
| | — Backfill missing data using interpolation + scraped price signals | |
| | — Validate price trends against known market benchmarks | |
| **Day 11** (Tue, Mar 4) | Build enhanced analytics APIs | New API endpoints |
| | — Location comparison endpoint (compare 2-5 locations side-by-side) | |
| | — "Trending" detection (identify locations with sharp score changes) | |
| | — City-wide statistics endpoint (avg price, top performers, declining areas) | |
| **Day 12** (Wed, Mar 5) | Frontend integration for new analytics | Updated UI |
| | — Wire new API endpoints to Price Trends page | |
| | — Add comparison charts (Chart.js multi-location overlay) | |
| | — Display city-wide market summary stats | |

#### Phase 3 Exit Criteria
- [ ] Price trends available for all ~300 locations
- [ ] Comparison and trending APIs functional
- [ ] Price Trends page displays real, accurate data
- [ ] City-wide statistics rendering correctly

---

### Phase 4: Frontend Polish & Production Readiness
**Duration:** 4 days (Mar 6 – Mar 11)  
**Objective:** Ensure the platform is polished, performant, and ready for corporate-level demonstration.

| Day | Task | Deliverable |
|-----|------|-------------|
| **Day 13** (Thu, Mar 6) | Map performance optimization for 300 pins | Optimized map rendering |
| | — Implement marker clustering for dense areas | |
| | — Optimize GeoJSON payload size (compression, field trimming) | |
| | — Add lazy loading for Intel Card data (fetch on click, not on load) | |
| **Day 14** (Fri, Mar 7) | Intel Card refinement with real data | Enhanced Intel Card |
| | — Ensure all 300 locations show real FinBERT-based smart copy | |
| | — Verify dynamic facts are data-driven (not placeholder text) | |
| | — Test edge cases: locations with very few articles, extreme scores | |
| **Day 15** (Mon, Mar 10) | Mobile responsiveness & cross-browser testing | Responsive UI |
| | — Test and fix layout on mobile (phones, tablets) | |
| | — Verify map interactions work on touch devices | |
| | — Cross-browser testing: Chrome, Firefox, Edge, Safari | |
| **Day 16** (Tue, Mar 11) | UI/UX final polish | Production-quality interface |
| | — Smooth all animations and transitions | |
| | — Add loading states, error handling, empty states | |
| | — Final visual QA pass | |

#### Phase 4 Exit Criteria
- [ ] Map renders 300 pins smoothly (<3 second load time)
- [ ] All Intel Cards display real, FinBERT-derived insights
- [ ] Responsive design verified on mobile/tablet
- [ ] No visual bugs or broken interactions

---

### Phase 5: Automation & Continuous Intelligence Loop
**Duration:** 3 days (Mar 12 – Mar 14)  
**Objective:** Set up the automated refresh cycle so the platform stays current without manual intervention.

| Day | Task | Deliverable |
|-----|------|-------------|
| **Day 17** (Wed, Mar 12) | Build incremental scraping script | Auto-refresh scraper |
| | — Modify scraper to only fetch articles from the last 2 weeks | |
| | — Implement "last_scraped" timestamp tracking per query category | |
| | — Add NER tagging to incremental pipeline | |
| **Day 18** (Thu, Mar 13) | Implement automated scheduling & moving average updates | Scheduled automation |
| | — Set up Windows Task Scheduler (or cloud-based cron) | |
| | — Schedule: Run every 2 weeks (Sunday 2:00 AM) | |
| | — Implement moving average score update: fold new data into existing scores | |
| | — Build error notification system (email/log alert if scraper fails) | |
| **Day 19** (Fri, Mar 14) | End-to-end automation test | Validated automation pipeline |
| | — Trigger a manual run of the full loop: Scrape → FinBERT → Aggregate → Update DB | |
| | — Verify scores update correctly in the database | |
| | — Verify frontend reflects the new scores | |
| | — Document the automation setup (runbook) | |

#### Phase 5 Exit Criteria
- [ ] Incremental scraper fetches only recent articles
- [ ] Automation schedule configured and tested
- [ ] Moving average update logic validated
- [ ] Full loop executes without manual intervention
- [ ] Runbook documentation complete

---

### Phase 6: Deployment & Launch
**Duration:** 4 days (Mar 17 – Mar 20)  
**Objective:** Deploy the platform to production infrastructure accessible for corporate use.

| Day | Task | Deliverable |
|-----|------|-------------|
| **Day 20** (Mon, Mar 17) | Backend deployment | Live backend API |
| | — Deploy FastAPI + Uvicorn to cloud server (Render / AWS / DigitalOcean) | |
| | — Migrate PostgreSQL + PostGIS to managed cloud database | |
| | — Configure environment variables, connection pooling, CORS | |
| **Day 21** (Tue, Mar 18) | Frontend deployment | Live frontend |
| | — Deploy frontend to static hosting (Vercel / GitHub Pages / Netlify) | |
| | — Configure custom domain (if applicable) | |
| | — Set up SSL/HTTPS | |
| **Day 22** (Wed, Mar 19) | Security & hardening | Hardened production environment |
| | — Configure firewall rules (restrict DB access) | |
| | — Set up API rate limiting (prevent abuse) | |
| | — Database backup strategy (daily automated backups) | |
| | — Health check endpoint + uptime monitoring | |
| **Day 23** (Thu, Mar 20) | Final testing & documentation | Production-ready system |
| | — End-to-end smoke test on production | |
| | — API documentation (Swagger/OpenAPI) | |
| | — User guide / demo walkthrough | |
| | — **🚀 LAUNCH** | |

#### Phase 6 Exit Criteria
- [ ] Backend API live and responding (<500ms latency)
- [ ] Frontend accessible via public URL
- [ ] SSL/HTTPS configured
- [ ] Database backups operational
- [ ] Documentation complete

---

## 4. Master Timeline (Gantt View)

```
Week 1 (Feb 19-25)  ████████████████████  Phase 1: Scraping Architecture
Week 2 (Feb 26-Mar 1) ██████████████████  Phase 2: FinBERT at Scale
Week 3 (Mar 3-5)     ████████████         Phase 3: Price Trends & Analytics
Week 3-4 (Mar 6-11)  ████████████████     Phase 4: Frontend Polish
Week 4 (Mar 12-14)   ████████████         Phase 5: Automation
Week 5 (Mar 17-20)   ████████████████     Phase 6: Deployment & Launch
```

| Week | Dates | Phase | Key Milestone |
|------|-------|-------|---------------|
| **Week 1** | Feb 19 – Feb 25 | Scraping Architecture | 3,000+ articles harvested, NER tagger operational |
| **Week 2** | Feb 26 – Mar 1 | FinBERT Processing | All ~300 locations have real sentiment scores |
| **Week 3** | Mar 3 – Mar 5 | Price Trends | Complete price analytics for all locations |
| **Week 3-4** | Mar 6 – Mar 11 | Frontend Polish | Production-quality, mobile-ready interface |
| **Week 4** | Mar 12 – Mar 14 | Automation | Self-updating bi-weekly intelligence loop |
| **Week 5** | Mar 17 – Mar 20 | Deployment | **🚀 Production Launch** |

---

## 5. Risk Register

| # | Risk | Probability | Impact | Mitigation Strategy |
|---|------|-------------|--------|---------------------|
| R1 | Google blocks scraper IPs during city-wide harvest | High | Critical | Proxy rotation, rate limiting (2-3s delays), residential proxy fallback |
| R2 | FinBERT processing exceeds GPU time estimates | Medium | High | Use Google Colab Pro ($10/mo), implement checkpointing to resume |
| R3 | NER tagger misidentifies locations (<90% accuracy) | Medium | High | Maintain comprehensive alias dictionary, implement fuzzy matching, manual QA on sample |
| R4 | Insufficient articles for some locations | Medium | Medium | Retain CSV-based scores as fallback for locations with <5 articles; flag for manual review |
| R5 | Database performance degrades at 300 locations | Low | Medium | Add PostgreSQL indexing, implement API response caching |
| R6 | Deployment environment configuration issues | Low | Medium | Use containerization (Docker), document all env variables |

---

## 6. Resource Requirements

### Infrastructure

| Resource | Provider | Cost | Duration |
|----------|----------|------|----------|
| GPU for FinBERT processing | Google Colab Pro | $10 | 1 month |
| Cloud server (Backend) | Render / DigitalOcean | $12-15/month | Ongoing |
| Managed PostgreSQL | Render / AWS RDS | $15-20/month | Ongoing |
| Proxy service (scraping) | Rotating proxy provider | $20-30 | One-time |
| Domain name (optional) | Namecheap | $10/year | Ongoing |
| **Total (Month 1)** | | **~$70-85** | |
| **Total (Ongoing/month)** | | **~$30-40/month** | |

### Tools & Stack

| Layer | Technology |
|-------|-----------|
| Scraping | Playwright (Async), BeautifulSoup, Google News RSS |
| NLP/AI | FinBERT (ProsusAI/finbert), Hugging Face Transformers |
| Database | PostgreSQL 15 + PostGIS |
| Backend | FastAPI, Uvicorn (ASGI) |
| Frontend | MapLibre GL JS, PMTiles, Chart.js, Vanilla JS/CSS |
| Deployment | Render / Vercel / GitHub Pages |

---

## 7. Success Criteria

### Technical KPIs
| Metric | Target |
|--------|--------|
| Locations with real FinBERT sentiment | ~300 |
| Sentiment accuracy (manual validation) | >85% agreement |
| API response time | <500ms (p95) |
| Map load time | <3 seconds |
| Automated refresh cycle | Bi-weekly (every 14 days) |
| System uptime | >99% |

### Business KPIs
| Metric | Target |
|--------|--------|
| Hyderabad coverage | All major micro-markets |
| Data freshness | Scores updated within 14 days of new data |
| User experience | Mobile-responsive, professional-grade UI |
| Documentation | Complete API docs + user guide |

---

## 8. Delivery Summary

| Item | Date |
|------|------|
| **Project Start** | Thursday, February 19, 2026 |
| **Data Pipeline Complete** | Saturday, March 1, 2026 |
| **Analytics & UI Complete** | Tuesday, March 11, 2026 |
| **Automation Operational** | Friday, March 14, 2026 |
| **🚀 Production Launch** | **Thursday, March 20, 2026** |
| **Total Duration** | **~5 weeks (23 working days)** |

---

*This document is a living plan and will be updated as phases are completed.*  
*Last updated: February 15, 2026*
