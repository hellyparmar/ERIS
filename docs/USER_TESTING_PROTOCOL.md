# R-DIOS User Testing Protocol

**Goal:** Evaluate usability, utility, and accuracy perception of the R-DIOS system with Petpooja users.
**Target Audience:** Restaurant owners/managers using Petpooja (3-5 participants).
**Duration:** 45-60 minutes per session.
**Format:** Moderated remote (Zoom/Meet) or in-person.

---

## 1. Pre-Test Preparation

### Equipment

- [ ] Computer with R-DIOS running (staging/prod)
- [ ] Recording software (OBS or Zoom recording)
- [ ] Note-taking spreadsheet
- [ ] Consent form (digital or printed)

### Participant Briefing (5 mins)
>
> "Hi, thank you for joining us. We are testing a new Retail Intelligence System called R-DIOS designed for Petpooja. We want to see how intuitive and useful it is for restaurant owners like you.
>
> Please remember: **We are testing the system, not you.** If you get stuck or confused, that's a problem with the design, not your ability. Please 'think aloud' as you navigate – tell me what you're looking for and what you expect to happen.
>
> Do you have any questions before we begin?"

---

## 2. Pre-Test Interview (5 mins)

- **Q1:** What is your current role and how long have you been managing restaurant operations?
- **Q2:** What tools do you currently use for inventory management and sales forecasting?
- **Q3:** What is your biggest pain point with your current reporting system?
- **Q4:** On a scale of 1-5, how comfortable are you with using data analytics tools?

---

## 3. Structured Tasks (25 mins)

### Task 1: Check Current Health & Waste (5 mins)

**Scenario:** "You've just logged in on a Monday morning. You want to quickly check how your stores performed yesterday and if there are any urgent waste issues."
**Goal:** Navigate Dashboard, identify Total Revenue, Waste percentage, and top alerts.
**Success Criteria:**

- [ ] Identifies Total Revenue correctly.
- [ ] Locates Waste % card.
- [ ] Notices at least one critical alert (e.g., "High Waste").
**Metric:** Time on Task (Target: < 30s)

### Task 2: Generate a Forecast for Next Week (5 mins)

**Scenario:** "You need to order ingredients for next week. You want to know the predicted sales for 'Butter Chicken' to avoid overstocking."
**Goal:** Navigate to Forecasts page, select a product/category, generate forecast.
**Success Criteria:**

- [ ] Finds 'Forecasts' in sidebar.
- [ ] Selects a specific item/category.
- [ ] Clicks 'Generate Forecast'.
- [ ] Interprets the result (e.g., "It says sales will go up on Friday").
**Metric:** Completion Rate (Pass/Fail)

### Task 3: Ask AI Assistant a Complex Query (5 mins)

**Scenario:** "You want to know which items are your least profitable but high volume. Instead of digging through reports, ask the AI Assistant."
**Goal:** Open AI Assistant, type a query (e.g., "Show me low margin high volume items"), and understand the response.
**Success Criteria:**

- [ ] Opens AI Assistant (sidebar or floating button).
- [ ] Types a relevant natural language query.
- [ ] Reviews the SQL/Table output.
- [ ] Expresses trust/distrust in the answer.
**Metric:** Satisfaction Rating (1-5)

### Task 4: Export a Monthly Report (5 mins)

**Scenario:** "Your accountant needs a sales and inventory report for last month. Create one and download it as a PDF."
**Goal:** Navigate to Reports, select Sales/Inventory, choose date range, Export PDF.
**Success Criteria:**

- [ ] Navigates to Reports section.
- [ ] Selects correct report type.
- [ ] Filters for 'Last Month'.
- [ ] Successfully clicks 'Export PDF'.
**Metric:** Number of Errors/Misclicks

### Task 5: Check Alert Settings (5 mins)

**Scenario:** "You are getting too many notifications about 'Low Stock'. You want to change the threshold so you are only notified when stock is critical."
**Goal:** Go to Settings/Integrations, find Alert configuration, adjust threshold.
**Success Criteria:**

- [ ] Navigates to Settings.
- [ ] Finds Alert/Notification settings.
- [ ] Adjusts a slider or input field.
- [ ] Saves changes.
**Metric:** Ease of Use Rating (1-5)

---

## 4. Post-Test Questionnaire (10 mins)

### System Usability Scale (SUS)

*Rate each from 1 (Strongly Disagree) to 5 (Strongly Agree)*

1. I think that I would use this system frequently.
2. I found the system unnecessarily complex.
3. I thought the system was easy to use.
4. I think that I would need the support of a technical person to be able to use this system.
5. I found the various functions in this system were well integrated.
6. I thought there was too much inconsistency in this system.
7. I would imagine that most people would learn to use this system very quickly.
8. I found the system very cumbersome to use.
9. I felt very confident using the system.
10. I needed to learn a lot of things before I could get going with this system.

### Debrief Questions

* **Q1:** What was the most useful feature you saw today?
- **Q2:** Was anything confusing or hard to find?
- **Q3:** If you could add one magic feature to this, what would it be?
- **Q4:** Would you pay for this tool? If so, how much (approx)?
- **Q5:** Any other feedback?

---

## 5. Observer Notes Template

| Participant ID | Task 1 Time | Task 2 Success | Task 3 Rating | Task 4 Errors | Task 5 Rating | Key Quotes / Bugs |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| P1 | | | | | | |
| P2 | | | | | | |
| P3 | | | | | | |

---

## Success Benchmarks

* **SUS Score:** Target > 80 (Excellent), Acceptable > 68.
- **Task Completion:** 100% for Tasks 1 & 2 (Core features).
- **Time on Task:** Dashboard check < 30s.
