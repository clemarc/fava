"""Summarize retained public request/result latency observations; no network."""
import argparse
from collections import Counter
import csv
import json
import math
from pathlib import Path
import statistics


def summarize(path):
    with Path(path).open(newline='') as stream:
        rows = list(csv.DictReader(stream))
    clean = [row for row in rows if row['included'] == 'true']
    values = sorted(int(row['seconds']) for row in clean)
    return dict(requests=len(rows), sample_size=len(values),
                sample_prs=len({row['pr'] for row in clean}),
                mean_seconds=statistics.mean(values), min_seconds=min(values),
                max_seconds=max(values), median_seconds=statistics.median(values),
                p95_nearest_rank_seconds=values[math.ceil(.95 * len(values)) - 1],
                exclusions=dict(Counter(row['exclusion_reason'] for row in rows
                                        if row['included'] != 'true')))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('csv', type=Path)
    print(json.dumps(summarize(parser.parse_args().csv), indent=2))
