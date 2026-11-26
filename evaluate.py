"""Reproduce the required-skill audit from two supplied CSV files.

Python 3, standard library only.
Run: python3 evaluate.py job-descriptions-tagged.csv skill-list.csv
Rule: only explicitly required skills count as gold; optional skills are excluded.
"""
import argparse
import csv
import json
import re
import sys
from pathlib import Path
from collections import Counter


ALIASES = {
    'Financial Modeling': 'Financial Modelling', 'Excel': 'Microsoft Excel',
    'Node': 'Node.js', 'JS': 'JavaScript', 'Postgres': 'PostgreSQL',
    'ML': 'Machine Learning', 'Social Media': 'Social Media Marketing',
}


# Bare 'API' is intentionally NOT mapped to REST APIs; it lacks the REST qualifier.
def tokens(text, vocabulary):
    matches = []
    for term in vocabulary:
        for m in re.finditer(r'(?<!\w)' + re.escape(term.strip()) + r'(?!\w)', text, re.I):
            matches.append((m.start(), m.end(), term))
    occupied, output = [], []
    for start, end, term in sorted(matches, key=lambda m: (-(m[1]-m[0]), m[0])):
        if not any(start < end2 and end > start2 for start2, end2 in occupied):
            occupied.append((start, end))
            output.append(term)
    return sorted(set(output))


def sections(description, vocabulary):
    intro = re.search(
        r'(?:We need someone who knows|You will use|You must be comfortable with|Required:)\s*',
        description,
        re.I,
    )
    if not intro:
        return [], [], '', 'Unrecognized requirement format'

    # End on sentence boundary, not at the period inside Node.js.
    remainder = description[intro.end():]
    requirement_sentence = re.split(r'\.(?=\s|$)', remainder, maxsplit=1)[0]
    optional = re.search(r'(?:Nice to have:|Bonus if you have used)\s*([^.]*)', description, re.I)
    optional_text = optional.group(1) if optional else ''
    plus_skills = [
        skill for skill in vocabulary
        if re.search(re.escape(skill) + r' is a plus, not a must', description, re.I)
    ]
    return (
        tokens(requirement_sentence, vocabulary),
        sorted(set(tokens(optional_text, vocabulary) + plus_skills)),
        requirement_sentence.strip(),
        '',
    )


def safe_ratio(numerator, denominator):
    return numerator / denominator if denominator else 0.0


def read_csv(path, required_fields):
    with open(path, encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        missing = [field for field in required_fields if field not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(
                f"{path} is missing required column(s): {', '.join(missing)}"
            )
        return list(reader)


def write_csv(path, fieldnames, rows):
    with open(path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def run(jd_csv, skills_csv, outdir):
    vocab = [
        row['skill'].strip()
        for row in read_csv(skills_csv, ['skill'])
        if row['skill'].strip()
    ]
    if not vocab:
        raise ValueError(f"{skills_csv} contains no skills")
    vocab = sorted(set(vocab))

    data = read_csv(jd_csv, ['jd_id', 'description', 'model_tags'])
    audit = []
    detail = []
    parse_warnings = []
    for row in data:
        required, optional, evidence, warning = sections(row['description'], vocab)
        if warning:
            parse_warnings.append({'jd_id': row['jd_id'], 'warning': warning})

        predictions = [tag.strip() for tag in row['model_tags'].split(';') if tag.strip()]
        correct = []
        wrong = []
        for tag in predictions:
            normalized = ALIASES.get(tag, tag)
            if normalized in required:
                status = 'CORRECT'
                correct.append(normalized)
            elif normalized in optional:
                status = 'WRONG_OPTIONAL'
                wrong.append(tag)
            elif normalized not in vocab:
                status = 'WRONG_OOV'
                wrong.append(tag)
            else:
                status = 'WRONG_UNSUPPORTED'
                wrong.append(tag)
            detail.append({
                'jd_id': row['jd_id'],
                'model_tag': tag,
                'normalized_to': normalized if normalized in vocab else '',
                'judgment': status,
                'required_skill_evidence': evidence,
            })

        missing = sorted(set(required) - set(correct))
        audit.append({
            **row,
            'required_skills': '; '.join(required),
            'optional_skills': '; '.join(optional),
            'correct_tags': '; '.join(correct),
            'wrong_tags': '; '.join(wrong),
            'missing_skills': '; '.join(missing),
            'tp': len(correct),
            'fp': len(wrong),
            'fn': len(missing),
            'required_phrase': evidence,
            'parse_warning': warning,
        })

    counts = Counter(item['judgment'] for item in detail)
    tp = counts['CORRECT']
    fp = len(detail) - tp
    fn = sum(row['fn'] for row in audit)
    summary = {
        'job_descriptions': len(data),
        'predicted_tags': len(detail),
        'required_skills': tp + fn,
        'true_positives': tp,
        'false_positives': fp,
        'false_negatives': fn,
        'precision': safe_ratio(tp, tp + fp),
        'recall': safe_ratio(tp, tp + fn),
        'miss_rate': safe_ratio(fn, tp + fn),
        'error_categories': {
            key: counts[key]
            for key in ['WRONG_OPTIONAL', 'WRONG_OOV', 'WRONG_UNSUPPORTED']
        },
        'parse_warnings': parse_warnings,
    }

    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    audit_fields = list(audit[0].keys()) if audit else [
        'jd_id', 'description', 'model_tags', 'required_skills', 'optional_skills',
        'correct_tags', 'wrong_tags', 'missing_skills', 'tp', 'fp', 'fn',
        'required_phrase', 'parse_warning',
    ]
    write_csv(outdir / 'audit_rows.csv', audit_fields, audit)

    judgment_fields = [
        'jd_id', 'model_tag', 'normalized_to', 'judgment',
        'required_skill_evidence',
    ]
    write_csv(outdir / 'tag_judgments.csv', judgment_fields, detail)

    (outdir / 'summary.json').write_text(
        json.dumps(summary, indent=2) + '\n',
        encoding='utf-8',
    )
    print(json.dumps(summary, indent=2))
    return summary


def main():
    parser = argparse.ArgumentParser(
        description='Audit model skill tags against required skills in job descriptions.'
    )
    parser.add_argument(
        'jd_csv',
        nargs='?',
        default=str(Path(__file__).with_name('job-descriptions-tagged.csv')),
    )
    parser.add_argument(
        'skills_csv',
        nargs='?',
        default=str(Path(__file__).with_name('skill-list.csv')),
    )
    parser.add_argument(
        '--outdir',
        default=str(Path(__file__).parent),
        help='Directory for audit_rows.csv, tag_judgments.csv, and summary.json',
    )
    args = parser.parse_args()

    try:
        run(args.jd_csv, args.skills_csv, args.outdir)
    except (OSError, csv.Error, ValueError) as exc:
        parser.exit(1, f'Error: {exc}\n')


if __name__ == '__main__':
    main()
