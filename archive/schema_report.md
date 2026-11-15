# CSV Schema Inspection Report
Inspection only: files were read with pandas and not cleaned, transformed, or modeled.
## ball_by_ball.csv
- Path: `data_pack/ball_by_ball.csv`
- File size: 39.169 MB
- Rows: 200,999
- Columns: 33
### Columns
| Column | Dtype | Null count | Null % | Unique | 3 examples |
| --- | --- | --- | --- | --- | --- |
| match_id | int64 | 0 | 0.00% | 867 | 13511, 13511, 13511 |
| innings | int64 | 0 | 0.00% | 4 | 1, 1, 1 |
| overid | int64 | 0 | 0.00% | 20 | 1, 1, 1 |
| over_ball_num | int64 | 0 | 0.00% | 13 | 1, 2, 3 |
| innings_ball_num | int64 | 0 | 0.00% | 136 | 1, 2, 3 |
| batting_team_id | int64 | 0 | 0.00% | 38 | 22, 22, 22 |
| bowling_team_id | int64 | 0 | 0.00% | 38 | 28, 28, 28 |
| striker_id | int64 | 0 | 0.00% | 888 | 1187, 1187, 1187 |
| striker_name | str | 0 | 0.00% | 885 | Jason Roy, Jason Roy, Jason Roy |
| non_striker_id | int64 | 0 | 0.00% | 867 | 6273, 6273, 6273 |
| non_striker_name | str | 0 | 0.00% | 864 | Tom Banton, Tom Banton, Tom Banton |
| bowler_id | int64 | 0 | 0.00% | 647 | 1772, 1772, 1772 |
| bowler_name | str | 0 | 0.00% | 646 | Sheldon Cottrell, Sheldon Cottrell, Sheldon Cottrell |
| batting_type | str | 0 | 0.00% | 2 | RHB, RHB, RHB |
| bowling_type | str | 0 | 0.00% | 12 | Left-arm fast-medium, Left-arm fast-medium, Left-arm fast-medium |
| batting_order | int64 | 0 | 0.00% | 13 | 1, 1, 1 |
| runs | int64 | 0 | 0.00% | 7 | 0, 0, 0 |
| is_four | bool | 0 | 0.00% | 2 | False, False, False |
| is_six | bool | 0 | 0.00% | 2 | False, False, False |
| is_wicket | bool | 0 | 0.00% | 2 | False, False, False |
| dismissal_type_id | float64 | 190118 | 94.59% | 8 | 1.0, 2.0, 2.0 |
| dismissal_type | str | 190118 | 94.59% | 9 | Bowled, Caught, Caught |
| dismissed_player_id | float64 | 190107 | 94.58% | 814 | 1187.0, 6273.0, 1596.0 |
| extras_type | str | 189167 | 94.11% | 6 | wide, wide, wide |
| extras1_runs | int64 | 0 | 0.00% | 7 | 6, 6, 6 |
| extras_2_runs | int64 | 0 | 0.00% | 3 | 0, 0, 0 |
| pace_or_spin | str | 0 | 0.00% | 2 | Pace, Pace, Pace |
| bowl_speed | float64 | 0 | 0.00% | 1033 | 0.0, 0.0, 0.0 |
| stroke | str | 6158 | 3.06% | 30 | Cover Drive, Flick, Square Cut |
| delivery_style | str | 391 | 0.19% | 34 | Inswing, Inswing, Inswing |
| over_or_around | str | 407 | 0.20% | 2 | Over, Over, Over |
| on_or_off | str | 0 | 0.00% | 2 | Off-side, On-side, Off-side |
| delivery_ist_time | str | 0 | 0.00% | 200826 | 2022-01-23 00:00:00 UTC, 2022-01-23 00:00:00 UTC, 2022-01-23 00:00:00 UTC |
### First 5 rows
| match_id | innings | overid | over_ball_num | innings_ball_num | batting_team_id | bowling_team_id | striker_id | striker_name | non_striker_id | non_striker_name | bowler_id | bowler_name | batting_type | bowling_type | batting_order | runs | is_four | is_six | is_wicket | dismissal_type_id | dismissal_type | dismissed_player_id | extras_type | extras1_runs | extras_2_runs | pace_or_spin | bowl_speed | stroke | delivery_style | over_or_around | on_or_off | delivery_ist_time |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 13511 | 1 | 1 | 1 | 1 | 22 | 28 | 1187 | Jason Roy | 6273 | Tom Banton | 1772 | Sheldon Cottrell | RHB | Left-arm fast-medium | 1 | 0 | False | False | False |  |  |  |  | 6 | 0 | Pace | 0.0 | Cover Drive | Inswing | Over | Off-side | 2022-01-23 00:00:00 UTC |
| 13511 | 1 | 1 | 2 | 2 | 22 | 28 | 1187 | Jason Roy | 6273 | Tom Banton | 1772 | Sheldon Cottrell | RHB | Left-arm fast-medium | 1 | 0 | False | False | False |  |  |  |  | 6 | 0 | Pace | 0.0 | Flick | Inswing | Over | On-side | 2022-01-23 00:00:00 UTC |
| 13511 | 1 | 1 | 3 | 3 | 22 | 28 | 1187 | Jason Roy | 6273 | Tom Banton | 1772 | Sheldon Cottrell | RHB | Left-arm fast-medium | 1 | 0 | False | False | False |  |  |  |  | 6 | 0 | Pace | 0.0 | Square Cut | Inswing | Over | Off-side | 2022-01-23 00:00:00 UTC |
| 13511 | 1 | 1 | 4 | 4 | 22 | 28 | 1187 | Jason Roy | 6273 | Tom Banton | 1772 | Sheldon Cottrell | RHB | Left-arm fast-medium | 1 | 0 | False | False | False |  |  |  |  | 6 | 0 | Pace | 0.0 | Backfoot defensive | Inswing | Over | On-side | 2022-01-23 00:00:00 UTC |
| 13511 | 1 | 1 | 5 | 5 | 22 | 28 | 1187 | Jason Roy | 6273 | Tom Banton | 1772 | Sheldon Cottrell | RHB | Left-arm fast-medium | 1 | 6 | False | True | False |  |  |  |  | 6 | 0 | Pace | 0.0 | Pull shot | Seamed In | Over | On-side | 2022-01-23 00:00:00 UTC |
### Numeric and date-like summaries
| Column | Summary |
| --- | --- |
| match_id | min=13511; max=55561; mean=3.273e+04 |
| innings | min=1; max=4; mean=1.474 |
| overid | min=1; max=20; mean=10.1 |
| over_ball_num | min=1; max=13; mean=3.648 |
| innings_ball_num | min=1; max=136; mean=60.46 |
| batting_team_id | min=1; max=4444; mean=412.8 |
| bowling_team_id | min=1; max=4444; mean=405.6 |
| striker_id | min=8; max=71727; mean=6745 |
| non_striker_id | min=8; max=68410; mean=6671 |
| bowler_id | min=23; max=71727; mean=8270 |
| batting_order | min=1; max=13; mean=3.869 |
| runs | min=0; max=6; mean=1.341 |
| is_four | min=False; max=True; mean=0.1158 |
| is_six | min=False; max=True; mean=0.06374 |
| is_wicket | min=False; max=True; mean=0.05413 |
| dismissal_type_id | min=1.0; max=10.0; mean=2.084 |
| dismissed_player_id | min=8.0; max=71727.0; mean=7228 |
| extras1_runs | min=1; max=7; mean=5.785 |
| extras_2_runs | min=0; max=4; mean=0.0004179 |
| bowl_speed | min=-1.0; max=1456.1; mean=71.41 |
### Low-cardinality value counts
| Column | Value counts |
| --- | --- |
| innings | 1 (105727); 2 (95234); 3 (25); 4 (13) |
| overid | 1 (10818); 2 (10788); 3 (10645); 4 (10638); 5 (10615); 6 (10542); 8 (10476); 7 (10441); 9 (10415); 10 (10396); 11 (10319); 12 (10254); 13 (10195); 14 (10088); 15 (9915); 16 (9824); 17 (9566); 18 (9160); 19 (8594); 20 (7310) |
| over_ball_num | 1 (32350); 2 (32257); 3 (32169); 4 (32066); 5 (31937); 6 (31791); 7 (6710); 8 (1364); 9 (279); 10 (57); 11 (15); 12 (2); 13 (2) |
| batting_type | RHB (131006); LHB (69993) |
| bowling_type | Right-arm Leg-Break (28027); Right-arm medium-fast (27014); Right-arm Fast (26637); Right-arm medium (23919); Slow left-arm orthodox (23582); Right-arm offbreak (20948); Right-arm fast-medium (15380); Left-arm medium-fast (12492); Left-arm fast-medium (7780); Left-arm medium (6082); Left-arm Chinaman (4685); Left-arm Fast (4453) |
| batting_order | 2 (34488); 1 (34126); 3 (31065); 4 (30068); 5 (24125); 6 (18297); 7 (13091); 8 (7578); 9 (4448); 10 (2554); 11 (1133); 12 (17); 13 (9) |
| runs | 0 (79387); 1 (72267); 4 (23303); 6 (12814); 2 (12547); 3 (656); 5 (25) |
| is_four | False (177716); True (23283) |
| is_six | False (188188); True (12811) |
| is_wicket | False (190118); True (10881) |
| dismissal_type_id | 2.0 (7557); 1.0 (1775); 3.0 (709); 4.0 (600); 5.0 (214); 6.0 (17); 9.0 (6); 10.0 (3); <NA> (190118) |
| dismissal_type | Caught (7557); Bowled (1775); LBW (709); RunOut (600); Stump (214); Hit Wicket (17); Retire Out (6); Obstracting the field (2); Obstructing the field (1); <NA> (190118) |
| extras_type | wide (7714); legbyes (2748); Overstep (576); byes (529); other (264); Penalty (1); <NA> (189167) |
| extras1_runs | 6 (189167); 2 (7714); 3 (2748); 1 (576); 4 (529); 5 (264); 7 (1) |
| extras_2_runs | 0 (200963); 1 (20); 4 (16) |
| pace_or_spin | Pace (123886); Spin (77113) |
| over_or_around | Over (154670); Around (45922); <NA> (407) |
| on_or_off | Off-side (104875); On-side (96124) |
### Candidate key check
| Column | Unique among non-null values | Basis |
| --- | --- | --- |
| match_id | no | 200,999 non-null values |
| overid | no | 200,999 non-null values |
| batting_team_id | no | 200,999 non-null values |
| bowling_team_id | no | 200,999 non-null values |
| striker_id | no | 200,999 non-null values |
| non_striker_id | no | 200,999 non-null values |
| bowler_id | no | 200,999 non-null values |
| dismissal_type_id | no | 10,881 non-null values |
| dismissed_player_id | no | 10,892 non-null values |
## matches.csv
- Path: `data_pack/matches.csv`
- File size: 0.118 MB
- Rows: 883
- Columns: 22
### Columns
| Column | Dtype | Null count | Null % | Unique | 3 examples |
| --- | --- | --- | --- | --- | --- |
| match_id | int64 | 0 | 0.00% | 883 | 13511, 13512, 13513 |
| comp_id | int64 | 0 | 0.00% | 138 | 1331, 1331, 1331 |
| match_number | int64 | 0 | 0.00% | 75 | 1, 2, 3 |
| match_date | str | 0 | 0.00% | 686 | 2022-01-22, 2022-01-23, 2022-01-26 |
| stage | str | 0 | 0.00% | 7 | League, League, League |
| venue_id | int64 | 0 | 0.00% | 98 | 54, 54, 54 |
| venue_country | str | 0 | 0.00% | 17 | West Indies, West Indies, West Indies |
| home_team_id | int64 | 0 | 0.00% | 36 | 28, 28, 28 |
| home_team | str | 0 | 0.00% | 36 | West Indies, West Indies, West Indies |
| away_team_id | int64 | 0 | 0.00% | 36 | 22, 22, 22 |
| away_team | str | 0 | 0.00% | 36 | England, England, England |
| home_team_captain_id | float64 | 44 | 4.98% | 89 | 494.0, 494.0, 494.0 |
| away_team_captain_id | float64 | 45 | 5.10% | 98 | 478.0, 1596.0, 1596.0 |
| toss_win_team_id | float64 | 15 | 1.70% | 37 | 28.0, 28.0, 22.0 |
| toss_opted | str | 15 | 1.70% | 2 | Fielding, Fielding, Fielding |
| man_of_the_match | int64 | 0 | 0.00% | 293 | 0, 0, 4986 |
| first_inn_revised_overs | float64 | 858 | 97.17% | 13 | 114.0, 84.0, 66.0 |
| second_inn_revised_overs | float64 | 858 | 97.17% | 12 | 114.0, 42.0, 48.0 |
| revised_target | float64 | 860 | 97.40% | 23 | 143.0, 56.0, 91.0 |
| knock_out | int64 | 0 | 0.00% | 2 | 0, 0, 0 |
| win_team_id | float64 | 41 | 4.64% | 36 | 28.0, 22.0, 28.0 |
| result | str | 0 | 0.00% | 670 | West Indies Won by 9 Wickets, England Won by 1 Run, West Indies Won by 20 runs |
### First 5 rows
| match_id | comp_id | match_number | match_date | stage | venue_id | venue_country | home_team_id | home_team | away_team_id | away_team | home_team_captain_id | away_team_captain_id | toss_win_team_id | toss_opted | man_of_the_match | first_inn_revised_overs | second_inn_revised_overs | revised_target | knock_out | win_team_id | result |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 13511 | 1331 | 1 | 2022-01-22 | League | 54 | West Indies | 28 | West Indies | 22 | England |  |  | 28.0 | Fielding | 0 |  |  |  | 0 | 28.0 | West Indies Won by 9 Wickets |
| 13512 | 1331 | 2 | 2022-01-23 | League | 54 | West Indies | 28 | West Indies | 22 | England | 494.0 | 478.0 | 28.0 | Fielding | 0 |  |  |  | 0 | 22.0 | England Won by 1 Run |
| 13513 | 1331 | 3 | 2022-01-26 | League | 54 | West Indies | 28 | West Indies | 22 | England | 494.0 | 1596.0 | 22.0 | Fielding | 4986 |  |  |  | 0 | 28.0 | West Indies Won by 20 runs |
| 13514 | 1331 | 4 | 2022-01-29 | League | 54 | West Indies | 28 | West Indies | 22 | England | 494.0 | 1596.0 | 28.0 | Fielding | 0 |  |  |  | 0 | 22.0 | England Won by 34 runs |
| 13515 | 1331 | 5 | 2022-01-30 | League | 54 | West Indies | 28 | West Indies | 22 | England | 494.0 |  | 28.0 | Batting | 0 |  |  |  | 0 | 28.0 | West Indies Won by 17 runs |
### Numeric and date-like summaries
| Column | Summary |
| --- | --- |
| match_id | min=13511; max=55561; mean=3.304e+04 |
| comp_id | min=1331; max=3787; mean=2395 |
| match_number | min=1; max=75; mean=17.64 |
| match_date | min=2022-01-22; max=2026-11-01 |
| venue_id | min=1; max=3692; mean=444.2 |
| home_team_id | min=1; max=4444; mean=416.5 |
| away_team_id | min=1; max=4444; mean=371.6 |
| home_team_captain_id | min=8.0; max=39444.0; mean=3550 |
| away_team_captain_id | min=8.0; max=39444.0; mean=3362 |
| toss_win_team_id | min=1.0; max=4444.0; mean=363.7 |
| man_of_the_match | min=0; max=67864; mean=5896 |
| first_inn_revised_overs | min=30.0; max=114.0; mean=74.16 |
| second_inn_revised_overs | min=30.0; max=114.0; mean=72.48 |
| revised_target | min=33.0; max=213.0; mean=122.6 |
| knock_out | min=0; max=1; mean=0.03511 |
| win_team_id | min=1.0; max=4444.0; mean=440.2 |
### Low-cardinality value counts
| Column | Value counts |
| --- | --- |
| stage | League (620); Others (226); Final (12); Qualifier (10); Super 4 (6); Eliminator (5); Semi Final (4) |
| venue_country | India (425); United Arab Emirates (69); New Zealand (52); United Kingdom (49); West Indies (44); Zimbabwe (38); Pakistan (36); Bangladesh (34); Sri Lanka (26); Australia (24); Oman (21); South Africa (18); Qatar (15); Netherlands (14); Ireland (10); United States (7); Japan (1) |
| toss_opted | Fielding (639); Batting (229); <NA> (15) |
| first_inn_revised_overs | 54.0 (4); 84.0 (3); 66.0 (3); 114.0 (2); 102.0 (2); 30.0 (2); 90.0 (2); 108.0 (2); 48.0 (1); 72.0 (1); 42.0 (1); 78.0 (1); 60.0 (1); <NA> (858) |
| second_inn_revised_overs | 90.0 (5); 114.0 (3); 48.0 (3); 42.0 (2); 102.0 (2); 60.0 (2); 30.0 (2); 54.0 (2); 72.0 (1); 78.0 (1); 84.0 (1); 66.0 (1); <NA> (858) |
| revised_target | 143.0 (1); 56.0 (1); 91.0 (1); 130.0 (1); 171.0 (1); 104.0 (1); 203.0 (1); 152.0 (1); 126.0 (1); 94.0 (1); 116.0 (1); 78.0 (1); 69.0 (1); 96.0 (1); 147.0 (1); 136.0 (1); 125.0 (1); 151.0 (1); 213.0 (1); 115.0 (1); 168.0 (1); 103.0 (1); 33.0 (1); <NA> (860) |
| knock_out | 0 (852); 1 (31) |
### Candidate key check
| Column | Unique among non-null values | Basis |
| --- | --- | --- |
| match_id | yes | 883 non-null values |
| comp_id | no | 883 non-null values |
| venue_id | no | 883 non-null values |
| home_team_id | no | 883 non-null values |
| away_team_id | no | 883 non-null values |
| home_team_captain_id | no | 839 non-null values |
| away_team_captain_id | no | 838 non-null values |
| toss_win_team_id | no | 868 non-null values |
| win_team_id | no | 842 non-null values |
## playing_eleven.csv
- Path: `data_pack/playing_eleven.csv`
- File size: 0.922 MB
- Rows: 28,381
- Columns: 9
### Columns
| Column | Dtype | Null count | Null % | Unique | 3 examples |
| --- | --- | --- | --- | --- | --- |
| match_id | int64 | 0 | 0.00% | 880 | 13511, 13511, 13511 |
| team_id | int64 | 0 | 0.00% | 38 | 22, 22, 22 |
| player_id | int64 | 0 | 0.00% | 1082 | 1187, 6273, 1210 |
| batting_order | float64 | 8678 | 30.58% | 13 | 1.0, 2.0, 3.0 |
| is_played | bool | 0 | 0.00% | 2 | True, True, True |
| is_captain | object | 8667 | 30.54% | 2 | False, False, False |
| is_wk | object | 8667 | 30.54% | 2 | False, False, False |
| is_impact | int64 | 0 | 0.00% | 2 | 0, 0, 0 |
| is_impact_off | int64 | 0 | 0.00% | 2 | 0, 0, 0 |
### First 5 rows
| match_id | team_id | player_id | batting_order | is_played | is_captain | is_wk | is_impact | is_impact_off |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 13511 | 22 | 1187 | 1.0 | True | False | False | 0 | 0 |
| 13511 | 22 | 6273 | 2.0 | True | False | False | 0 | 0 |
| 13511 | 22 | 1210 | 3.0 | True | False | False | 0 | 0 |
| 13511 | 22 | 1596 | 4.0 | True | False | False | 0 | 0 |
| 13511 | 22 | 478 | 5.0 | True | False | False | 0 | 0 |
### Numeric and date-like summaries
| Column | Summary |
| --- | --- |
| match_id | min=13511; max=55561; mean=3.561e+04 |
| team_id | min=1; max=4444; mean=453.4 |
| player_id | min=8; max=71727; mean=9764 |
| batting_order | min=1.0; max=13.0; mean=6.169 |
| is_played | min=False; max=True; mean=0.6946 |
| is_impact | min=0; max=1; mean=0.01966 |
| is_impact_off | min=0; max=1; mean=0.01966 |
### Low-cardinality value counts
| Column | Value counts |
| --- | --- |
| batting_order | 3.0 (1744); 1.0 (1743); 2.0 (1743); 4.0 (1742); 5.0 (1741); 6.0 (1741); 8.0 (1736); 9.0 (1736); 11.0 (1736); 7.0 (1735); 10.0 (1735); 12.0 (564); 13.0 (7); <NA> (8678) |
| is_played | True (19714); False (8667) |
| is_captain | False (18031); True (1683); <NA> (8667) |
| is_wk | False (18039); True (1675); <NA> (8667) |
| is_impact | 0 (27823); 1 (558) |
| is_impact_off | 0 (27823); 1 (558) |
### Candidate key check
| Column | Unique among non-null values | Basis |
| --- | --- | --- |
| match_id | no | 28,381 non-null values |
| team_id | no | 28,381 non-null values |
| player_id | no | 28,381 non-null values |
## teams.csv
- Path: `data_pack/teams.csv`
- File size: 0.007 MB
- Rows: 353
- Columns: 3
### Columns
| Column | Dtype | Null count | Null % | Unique | 3 examples |
| --- | --- | --- | --- | --- | --- |
| comp_id | int64 | 0 | 0.00% | 141 | 1331, 1331, 1335 |
| team_id | int64 | 0 | 0.00% | 38 | 22, 28, 18 |
| team_name | str | 0 | 0.00% | 38 | England, West Indies, India |
### First 5 rows
| comp_id | team_id | team_name |
| --- | --- | --- |
| 1331 | 22 | England |
| 1331 | 28 | West Indies |
| 1335 | 18 | India |
| 1335 | 28 | West Indies |
| 1345 | 20 | Australia |
### Numeric and date-like summaries
| Column | Summary |
| --- | --- |
| comp_id | min=1331; max=3787; mean=2466 |
| team_id | min=1; max=4444; mean=221.5 |
### Low-cardinality value counts
None.
### Candidate key check
| Column | Unique among non-null values | Basis |
| --- | --- | --- |
| comp_id | no | 353 non-null values |
| team_id | no | 353 non-null values |
## competitions.csv
- Path: `data_pack/competitions.csv`
- File size: 0.007 MB
- Rows: 141
- Columns: 4
### Columns
| Column | Dtype | Null count | Null % | Unique | 3 examples |
| --- | --- | --- | --- | --- | --- |
| comp_id | int64 | 0 | 0.00% | 141 | 3395, 3405, 3465 |
| comp_name | str | 0 | 0.00% | 141 | South Africa in New Zealand T20I Seri..., Afghanistan v Sri Lanka T20I Series 2026, India in Zimbabwe T20I Series 2026 |
| match_format | str | 0 | 0.00% | 2 | T20I, T20I, T20I |
| season | str | 0 | 0.00% | 8 | 2026, 2026, 2026 |
### First 5 rows
| comp_id | comp_name | match_format | season |
| --- | --- | --- | --- |
| 3395 | South Africa in New Zealand T20I Seri... | T20I | 2026 |
| 3405 | Afghanistan v Sri Lanka T20I Series 2026 | T20I | 2026 |
| 3465 | India in Zimbabwe T20I Series 2026 | T20I | 2026 |
| 3568 | Bangladesh in Zimbabwe T20I Series 2026 | T20I | 2026 |
| 3482 | Australia in Bangladesh T20I Series 2026 | T20I | 2026 |
### Numeric and date-like summaries
| Column | Summary |
| --- | --- |
| comp_id | min=1331; max=3787; mean=2483 |
| season | min=2022-01-01; max=2026-01-01 |
### Low-cardinality value counts
| Column | Value counts |
| --- | --- |
| match_format | T20I (134); T20 (7) |
| season | 2024 (33); 2025 (33); 2026 (25); 2022 (25); 2023 (20); 2022/23 (3); 2023/24 (1); 2024/25 (1) |
### Candidate key check
| Column | Unique among non-null values | Basis |
| --- | --- | --- |
| comp_id | yes | 141 non-null values |
## competition_team_player_mapping.csv
- Path: `data_pack/competition_team_player_mapping.csv`
- File size: 0.442 MB
- Rows: 6,413
- Columns: 6
### Columns
| Column | Dtype | Null count | Null % | Unique | 3 examples |
| --- | --- | --- | --- | --- | --- |
| comp_id | int64 | 0 | 0.00% | 140 | 1331, 1331, 1331 |
| comp_name | str | 0 | 0.00% | 140 | England in West Indies T20I Series 2022, England in West Indies T20I Series 2022, England in West Indies T20I Series 2022 |
| team_id | int64 | 0 | 0.00% | 38 | 22, 22, 22 |
| team_name | str | 0 | 0.00% | 38 | England, England, England |
| player_id | int64 | 0 | 0.00% | 1217 | 478, 479, 722 |
| player_name | str | 0 | 0.00% | 1210 | Eoin Morgan, Adil Rashid, Liam Dawson |
### First 5 rows
| comp_id | comp_name | team_id | team_name | player_id | player_name |
| --- | --- | --- | --- | --- | --- |
| 1331 | England in West Indies T20I Series 2022 | 22 | England | 478 | Eoin Morgan |
| 1331 | England in West Indies T20I Series 2022 | 22 | England | 479 | Adil Rashid |
| 1331 | England in West Indies T20I Series 2022 | 22 | England | 722 | Liam Dawson |
| 1331 | England in West Indies T20I Series 2022 | 22 | England | 786 | Chris Jordan |
| 1331 | England in West Indies T20I Series 2022 | 22 | England | 1187 | Jason Roy |
### Numeric and date-like summaries
| Column | Summary |
| --- | --- |
| comp_id | min=1331; max=3787; mean=2441 |
| team_id | min=1; max=4444; mean=262.2 |
| player_id | min=8; max=71727; mean=9523 |
### Low-cardinality value counts
None.
### Candidate key check
| Column | Unique among non-null values | Basis |
| --- | --- | --- |
| comp_id | no | 6,413 non-null values |
| team_id | no | 6,413 non-null values |
| player_id | no | 6,413 non-null values |
# CROSS-FILE CHECKS
## Shared columns
| Column | Dtype by file |
| --- | --- |
| batting_order | ball_by_ball.csv: int64; playing_eleven.csv: float64 |
| comp_id | matches.csv: int64; teams.csv: int64; competitions.csv: int64; competition_team_player_mapping.csv: int64 |
| comp_name | competitions.csv: str; competition_team_player_mapping.csv: str |
| match_id | ball_by_ball.csv: int64; matches.csv: int64; playing_eleven.csv: int64 |
| player_id | playing_eleven.csv: int64; competition_team_player_mapping.csv: int64 |
| team_id | playing_eleven.csv: int64; teams.csv: int64; competition_team_player_mapping.csv: int64 |
| team_name | teams.csv: str; competition_team_player_mapping.csv: str |
## Shared id-like columns: child values absent from smallest file
| Column | Child file | Comparison file | Child ids missing |
| --- | --- | --- | --- |
| comp_id | matches.csv | competitions.csv | 0 |
| comp_id | teams.csv | competitions.csv | 0 |
| comp_id | competition_team_player_mapping.csv | competitions.csv | 0 |
| match_id | ball_by_ball.csv | matches.csv | 0 |
| match_id | playing_eleven.csv | matches.csv | 0 |
| player_id | playing_eleven.csv | competition_team_player_mapping.csv | 0 |
| team_id | playing_eleven.csv | teams.csv | 0 |
| team_id | competition_team_player_mapping.csv | teams.csv | 0 |
## Matches per competition per season
| comp_id | Derived year | Matches |
| --- | --- | --- |
| 1331 | 2022 | 5 |
| 1335 | 2022 | 3 |
| 1345 | 2022 | 5 |
| 1358 | 2022 | 74 |
| 1435 | 2022 | 3 |
| 1439 | 2022 | 5 |
| 1452 | 2022 | 3 |
| 1458 | 2022 | 3 |
| 1474 | 2022 | 2 |
| 1494 | 2022 | 3 |
| 1499 | 2022 | 5 |
| 1512 | 2022 | 3 |
| 1517 | 2022 | 3 |
| 1523 | 2022 | 3 |
| 1531 | 2022 | 2 |
| 1533 | 2022 | 13 |
| 1534 | 2022 | 2 |
| 1537 | 2022 | 3 |
| 1543 | 2022 | 5 |
| 1551 | 2022 | 6 |
| 1584 | 2022 | 3 |
| 1595 | 2022 | 7 |
| 1599 | 2022 | 3 |
| 1601 | 2022 | 2 |
| 1603 | 2022 | 2 |
| 1608 | 2022 | 7 |
| 1611 | 2022 | 3 |
| 1646 | 2022 | 2 |
| 1698 | 2023 | 3 |
| 1700 | 2023 | 3 |
| 1709 | 2023 | 3 |
| 1715 | 2023 | 74 |
| 1718 | 2023 | 3 |
| 1719 | 2023 | 3 |
| 1742 | 2023 | 3 |
| 1769 | 2023 | 3 |
| 1792 | 2023 | 3 |
| 1799 | 2023 | 5 |
| 1885 | 2023 | 2 |
| 1913 | 2023 | 5 |
| 1997 | 2023 | 3 |
| 1998 | 2023 | 2 |
| 1999 | 2023 | 4 |
| 2000 | 2023 | 3 |
| 2046 | 2023 | 5 |
| 2047 | 2023 | 2 |
| 2048 | 2023 | 5 |
| 2058 | 2023 | 3 |
| 2059 | 2024 | 3 |
| 2060 | 2024 | 5 |
| 2061 | 2024 | 3 |
| 2062 | 2024 | 3 |
| 2188 | 2023 | 3 |
| 2193 | 2024 | 74 |
| 2229 | 2024 | 3 |
| 2267 | 2024 | 3 |
| 2269 | 2024 | 3 |
| 2305 | 2024 | 3 |
| 2350 | 2024 | 5 |
| 2354 | 2024 | 4 |
| 2371 | 2024 | 5 |
| 2372 | 2024 | 5 |
| 2387 | 2024 | 3 |
| 2395 | 2024 | 3 |
| 2398 | 2024 | 6 |
| 2442 | 2024 | 3 |
| 2452 | 2024 | 3 |
| 2453 | 2024 | 3 |
| 2455 | 2024 | 5 |
| 2457 | 2024 | 3 |
| 2512 | 2024 | 3 |
| 2513 | 2025 | 5 |
| 2542 | 2024 | 3 |
| 2548 | 2024 | 3 |
| 2561 | 2024 | 3 |
| 2562 | 2024 | 2 |
| 2605 | 2024 | 6 |
| 2626 | 2025 | 3 |
| 2628 | 2025 | 3 |
| 2670 | 2024 | 15 |
| 2692 | 2024 | 3 |
| 2716 | 2024 | 2 |
| 2718 | 2024 | 4 |
| 2722 | 2024 | 3 |
| 2725 | 2025 | 75 |
| 2753 | 2024 | 3 |
| 2755 | 2024 | 2 |
| 2755 | 2025 | 1 |
| 2793 | 2025 | 5 |
| 2801 | 2025 | 3 |
| 2873 | 2025 | 3 |
| 2874 | 2025 | 5 |
| 2875 | 2025 | 3 |
| 2906 | 2026 | 3 |
| 2912 | 2025 | 3 |
| 2915 | 2025 | 5 |
| 2921 | 2025 | 5 |
| 2973 | 2025 | 3 |
| 2975 | 2025 | 3 |
| 3020 | 2025 | 3 |
## Match and result checks
- Ball-by-ball match ids: 867; matches.csv match ids: 883
| Condition | Count |
| --- | --- |
| winner = null | 41 |
| tie | 0 |
| no result | 21 |
| D/L or revised target marker | 19 |
Winner source: `win_team_id`; result marker source: `result` in `matches.csv`.
## Ball-by-ball innings and over checks
| Metric | Value |
| --- | --- |
| Innings values | 1 (105727); 2 (95234); 3 (25); 4 (13) |
| Rows with innings > 2 | 38 |
| Over range | 1 to 20 |
| Ball-in-over range | 1 to 13 |
## Player names
| File | Name column |
| --- | --- |
| competition_team_player_mapping.csv | player_name |
## Team type and Pakistan team names
No team type column identified.
Distinct team names containing `Pakistan`: Pakistan, Pakistan A.
## Distinct team names (maximum 80)
| Team name | Source file(s) |
| --- | --- |
| Afghanistan | competition_team_player_mapping.csv, teams.csv |
| Afghanistan A | competition_team_player_mapping.csv, teams.csv |
| Australia | competition_team_player_mapping.csv, teams.csv |
| Bangladesh | competition_team_player_mapping.csv, teams.csv |
| Bangladesh A | competition_team_player_mapping.csv, teams.csv |
| Canada | competition_team_player_mapping.csv, teams.csv |
| Chennai Super Kings | competition_team_player_mapping.csv, teams.csv |
| Delhi Capitals | competition_team_player_mapping.csv, teams.csv |
| England | competition_team_player_mapping.csv, teams.csv |
| Gujarat Titans | competition_team_player_mapping.csv, teams.csv |
| Hong Kong | competition_team_player_mapping.csv, teams.csv |
| India | competition_team_player_mapping.csv, teams.csv |
| India A | competition_team_player_mapping.csv, teams.csv |
| Ireland | competition_team_player_mapping.csv, teams.csv |
| Japan | competition_team_player_mapping.csv, teams.csv |
| Kolkata Knight Riders | competition_team_player_mapping.csv, teams.csv |
| Kuwait | competition_team_player_mapping.csv, teams.csv |
| Lucknow Super Giants | competition_team_player_mapping.csv, teams.csv |
| Mumbai Indians | competition_team_player_mapping.csv, teams.csv |
| Nepal | competition_team_player_mapping.csv, teams.csv |
| Netherlands | competition_team_player_mapping.csv, teams.csv |
| New Zealand | competition_team_player_mapping.csv, teams.csv |
| Oman | competition_team_player_mapping.csv, teams.csv |
| Pakistan | competition_team_player_mapping.csv, teams.csv |
| Pakistan A | competition_team_player_mapping.csv, teams.csv |
| Punjab Kings | competition_team_player_mapping.csv, teams.csv |
| Rajasthan Royals | competition_team_player_mapping.csv, teams.csv |
| Royal Challengers Bengaluru | competition_team_player_mapping.csv, teams.csv |
| Scotland | competition_team_player_mapping.csv, teams.csv |
| Singapore | competition_team_player_mapping.csv, teams.csv |
| South Africa | competition_team_player_mapping.csv, teams.csv |
| Sri Lanka | competition_team_player_mapping.csv, teams.csv |
| Sri Lanka A | competition_team_player_mapping.csv, teams.csv |
| Sunrisers Hyderabad | competition_team_player_mapping.csv, teams.csv |
| United Arab Emirates | competition_team_player_mapping.csv, teams.csv |
| United States Of America | competition_team_player_mapping.csv, teams.csv |
| West Indies | competition_team_player_mapping.csv, teams.csv |
| Zimbabwe | competition_team_player_mapping.csv, teams.csv |
## OPEN QUESTIONS
- Cross-file parent selection for shared ids uses the smallest file containing that id column; confirm the intended relational parent if this heuristic is not correct.
- Date-like detection uses column names containing date, datetime, timestamp, or season, plus datetime dtypes; confirm any unlabeled date fields.
- Competition season grouping prefers a season column and otherwise derives calendar year from the first date-like match column.
