# LAGOS-AND v2.0 BLOCK-TRIMMED: dataset quality report

Rows: 1,476,550 (0 malformed). Blocks: 80,294. (block, ORCID) groups: 244,564. Distinct ORCIDs: 244,564.

## Missing values

| column | missing | fraction |
|---|---:|---:|
| block_fullname | 0 | 0.0 |
| orcid | 0 | 0.0 |
| doi | 0 | 0.0 |
| pid | 0 | 0.0 |
| author_position | 0 | 0.0 |
| author_name | 0 | 0.0 |
| author_affiliation | 208,199 | 0.141004 |
| coauthors | 0 | 0.0 |
| coauthor_affliations | 0 | 0.0 |
| venue | 34,061 | 0.023068 |
| pub_year | 0 | 0.0 |
| paper_title | 0 | 0.0 |
| paper_abstract | 149,912 | 0.101529 |
| train1_test0_val2 | 0 | 0.0 |

## Counters

- affiliation_tab_marker_rows: 34,837
- coauthors_self_name_rows: 1,476,550
- dois_shared_by_multiple_orcids: 0
- dois_with_multiple_pids: 14,546
- duplicate_doi_rows_within_group: 15,279
- orcids_in_multiple_blocks: 0
- rows_total: 1,476,550

Duplicate-DOI row fraction within groups: 0.010348
Row split distribution: {'0': 370194, '1': 739750, '2': 366606}; block split distribution: {'0': 20081, '1': 40253, '2': 19960}; blocks with mixed split: 0
Groups per block: {2: 54231, 3: 12840, 4: 5079, 5: 2647, 6: 1533, 7: 933, 8: 640, 9: 428, 10: 347, 11: 242, 12: 183, 13: 161, 14: 123, 15: 104, 16: 68, 17: 94, 18: 53, 19: 36, 20: 46, 21: 33, 22: 33, 23: 24, 24: 30, 25: 25, 26: 15, 27: 17, 28: 14, 29: 20, 30: 13, 31: 15, 32: 16, 33: 11, 34: 15, 35: 5, 36: 13, 37: 7, 38: 11, 39: 14, 40: 9, 41: 7, 42: 7, 43: 7, 44: 8, 45: 6, 46: 5, 47: 5, 48: 5, 49: 8, 50: 4, 51: 3, 52: 6, 53: 4, 54: 1, 55: 2, 57: 3, 58: 3, 59: 2, 60: 2, 61: 5, 62: 1, 63: 6, 64: 2, 65: 4, 66: 2, 67: 4, 68: 2, 69: 2, 70: 3, 71: 2, 72: 2, 73: 2, 74: 5, 76: 2, 77: 1, 78: 2, 79: 3, 80: 3, 82: 1, 83: 2, 88: 1, 90: 1, 91: 1, 93: 1, 95: 1, 97: 1, 99: 1, 101: 1, 102: 1, 104: 1, 115: 1, 116: 1, 122: 1, 124: 1, 125: 1, 126: 1, 129: 1, 138: 1, 144: 1, 165: 1, 174: 1, 188: 1}
Rows per group: {'min': 1, 'median': 2, 'max': 591}
Publication years: [1870, 2022]

## Sampling frame

Eligible blocks by stratum: {'S': 32188, 'M': 33698, 'L': 4423, 'XL': 42}
Exclusions: {'no_group_with_two_unique_dois': 7552, 'more_groups_than_cap': 2391}
