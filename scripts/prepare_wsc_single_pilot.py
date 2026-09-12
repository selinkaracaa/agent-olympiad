"""Prepare one fixed, non-cherry-picked WSC benchmark prompt without gold fields."""
import json
from pathlib import Path
import sys
from hashlib import sha256

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from artifacts.contest_delivery import _document_pdf
import pymupdf


def main():
    benchmark = ROOT / 'data/benchmarks/wsc_writing/benchmark.json'
    row = next(r for r in json.loads(benchmark.read_text(encoding='utf-8'))
               if r['problem_id'] == 'wsc_writing_gq_001')
    target = ROOT / 'results/wsc_writing_gq_001_otc_pilot/input'
    target.mkdir(parents=True, exist_ok=True)
    pdf = target / 'task.pdf'
    if pdf.exists():
        raise ValueError('Prepared input exists; preserve it rather than overwrite')
    text = ('WSC writing benchmark: ' + row['problem_id'] + '\n'
            'Collected discussion prompt; benchmark adaptation, not an original contest paper.\n\n'
            + row['problem_description'])
    (target / 'task.txt').write_text(text, encoding='utf-8')
    _document_pdf(text, pdf)
    provenance = dict(problem_id=row['problem_id'], benchmark=str(benchmark),
                      benchmark_sha256=sha256(benchmark.read_bytes()).hexdigest(),
                      task_pdf_sha256=sha256(pdf.read_bytes()).hexdigest(),
                      prompt_sha256=sha256(row['problem_description'].encode()).hexdigest(),
                      selection='first benchmark entry, chosen before evaluation',
                      input_fields=['problem_id', 'problem_description'], gold_included=False)
    (target / 'provenance.json').write_text(json.dumps(provenance, indent=2), encoding='utf-8')
    with pymupdf.open(pdf) as doc:
        for index, page in enumerate(doc):
            page.get_pixmap().save(str(target / f'task_page_{index + 1}.png'))
        print(json.dumps(dict(pdf=str(pdf), pages=len(doc), problem_id=row['problem_id'])))


if __name__ == '__main__':
    main()
