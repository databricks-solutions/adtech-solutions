# Genie Configuration

The genie space used in this series was configued using the following settings:

## Data

* `segments.megacorp_segment_definitions`
* `segments.megacorp_campaigns`
* `profiles.megacorp_audience_census_profile`

## Instructions

- We have 3 age groups: ‘Child’ for age<18, ‘Adult’ for age <65 and ‘Senior’ for age >=65
- The table achu_demos.profiles.megacorp_audience_census_profile may contain multiple records for the same individual if they belong to more than one campaign. Ensure the results include only distinct individuals.
- QSR stands for Quick Service Restaurant

## Description

This Genie space is designed for marketing analysis, enabling detailed exploration and reporting on audience segments, and individual demographic profiles. The space integrates campaign data, segment definitions, and audience census profiles. 

The space allows to:
- Understand audience segment definitions and membership
- Profiling the campaign audience on demographic dimensions such as age and gender
- Developing custom ad-hoc queries for marketing analysts