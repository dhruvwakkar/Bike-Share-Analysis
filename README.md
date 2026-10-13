# Cyclistic Bike-Share Analysis 🚲

## Project Overview

This project analyzes 2025 Cyclistic bike-share data to understand how annual members and casual riders use Cyclistic bikes differently.

The analysis follows the Google Data Analytics Capstone case study approach, using data cleaning, exploratory analysis, summary statistics, and Power BI dashboards to identify differences in riding behavior.

**Business Question:** How do annual members and casual riders use Cyclistic bikes differently?

## Tools & Technologies

- **Python:** Data cleaning, preparation, and exploratory data analysis
- **Pandas:** Data manipulation and aggregation
- **Excel:** Summary tables and data preparation
- **Power BI:** Interactive dashboards and data visualization

## Project Workflow

1. **Data Collection:** Obtained the 2025 bike-share trip data.
2. **Data Cleaning:** Processed the monthly datasets using Python, checked timestamps, calculated ride durations, and handled invalid records.
3. **Data Validation:** Checked the cleaned dataset and validated the summary ride counts.
4. **Data Analysis:** Compared ride frequency, ride duration, weekday and weekend patterns, monthly trends, and bike-type preferences.
5. **Dashboard Development:** Created a two-page Power BI report to communicate the findings.

## Key Findings

- **Total rides:** 5,552,941
- **Annual member rides:** 3,553,481 (approximately 64%).
- **Casual rider rides:** 1,999,460 (approximately 36%).
- **Average ride duration:** Casual riders averaged 19.13 minutes, compared with 11.95 minutes for annual members.
- **Weekday and weekend behavior:** Annual members accounted for more rides on weekdays, while casual riders had a larger share of their rides on weekends.
- **Bike preferences:** Classic and electric bikes were used by both rider groups, with differences in their usage patterns.

## Power BI Dashboard

### Page 1 — Rider Usage Overview

This page presents the overall ride volume, annual member and casual rider comparisons, monthly ride trends, bike-type preferences, and average ride duration.

![Cyclistic Rider Usage Overview](images/cyclistic_2025_powerbi_dashboard_report_1.jpeg)

### Page 2 — Rider Behavior Patterns

This page compares riding behavior across days of the week, weekday versus weekend usage, and average ride duration by rider type.

![Cyclistic Rider Behavior Patterns](images/cyclistic_2025_powerbi_dashboard_report_2.jpeg)

## Project Files

- `python/` — Python scripts used for data cleaning and analysis.
- `data/` — Summary CSV files used in the analysis and dashboard.
- `powerbi/` — Power BI report file (`.pbix`).
- `images/` — Dashboard screenshots.
- `README.md` — Project documentation.

## Business Objective

The objective is to understand the different usage patterns of annual members and casual riders. These findings can help Cyclistic develop data-informed strategies to encourage casual riders to become annual members.

## Data Source

The analysis uses 2025 Divvy bike-share trip data.

Source: [Divvy Trip Data](https://divvy-tripdata.s3.amazonaws.com/index.html)

## Conclusion

The analysis shows that annual members account for the majority of rides, while casual riders have longer average ride durations and a stronger relative presence on weekends. These differences provide a basis for exploring membership-conversion strategies.

---

*This project was completed as a portfolio case study inspired by the Google Data Analytics Professional Certificate.*
