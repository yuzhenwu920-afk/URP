"""Verify four-year figures/designs and benchmark the connected original 2022 model."""
from pathlib import Path
import contextlib
import io
import json
import re
import sys
import unittest

import numpy as np
from SALib.sample import sobol
from docx import Document
from pypdf import PdfReader
from PIL import Image

import real_model_pipeline as p

ROOT = Path(__file__).resolve().parent


def verify():
    suite = unittest.defaultTestLoader.loadTestsFromName('test_pipeline')
    stream = io.StringIO()
    with contextlib.redirect_stdout(io.StringIO()):
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    software = {'scope': 'Analytic Ishigami and synthetic software fixtures only; no crop validation',
                'tests_run': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
                'skipped': len(result.skipped), 'passed': result.wasSuccessful(),
                'versions': p.versions(), 'details': stream.getvalue()}
    p.write(ROOT / 'SOFTWARE_VALIDATION.json', software)
    assert result.wasSuccessful() and result.testsRun == 10
    config = ROOT / 'study_config.json'
    manifest = p.read(ROOT / 'designs_N128/design_manifest.json')
    assert len(manifest['runs']) == 12
    rows = 0
    for r in manifest['runs']:
        case, run, x = p.load_design(config, ROOT / 'designs_N128', r['year'], r['seed'])
        assert p.sha(ROOT / 'designs_N128' / r['csv']) == r['csv_sha256']
        import pandas as pd
        csv = pd.read_csv(ROOT / 'designs_N128' / r['csv'], float_precision='round_trip')
        assert np.array_equal(csv[p.NAMES].values, x)
        assert csv.row_id.tolist() == list(range(len(x)))
        assert csv.saltelli_role.tolist() == p.saltelli_labels(128)
        # Check every hybrid row, not just the first block.
        blocks = x.reshape(128, 10, 8)
        for j in range(8):
            expected = blocks[:, 0].copy()
            expected[:, j] = blocks[:, 9, j]
            assert np.array_equal(blocks[:, j + 1], expected)
        expanded = sobol.sample(p.problem(case), 512, calc_second_order=False, seed=r['seed'])
        assert np.array_equal(x, expanded[:len(x)])
        rows += len(x)
    assert rows == 15360
    paper = ROOT / 'paper_framework_execution_ready.md'
    text = paper.read_text()
    refs = re.findall(r'!\[[^\]]*\]\(([^)]+)\)', text)
    assert len(refs) >= 9 and all((ROOT / ref).is_file() for ref in refs)
    word = Document(paper.with_suffix('.docx'))
    pdf = PdfReader(paper.with_suffix('.pdf'))
    assert len(word.inline_shapes) == len(refs) and len(pdf.pages) >= 5
    for name in ['F07_parameter_intervals', 'F13_yield_gate']:
        with Image.open(ROOT / f'figures/{name}.png') as im:
            assert min(im.size) >= 1400
        assert len(PdfReader(ROOT / f'figures/{name}.pdf').pages) == 1
    cases = p.read(config)['cases']
    assert cases['2022']['baseline_expected'] is not None
    with np.load(ROOT / 'verified_phase_specific_draws.npz', allow_pickle=False) as z:
        assert z['p2_2022'].shape == (58784, 3)
        with np.load(ROOT / 'source_data/phase2_2022_formal_checkpoint.npz', allow_pickle=False) as raw:
            assert np.array_equal(z['p2_2022'], raw['history'][163:].reshape(-1, 3))
    assert all(cases[str(y)]['baseline_expected'] for y in [2019, 2020, 2021])
    assert not list((ROOT / 'designs_N128').glob('*response*'))
    receipt = p.benchmark(config, ROOT/'real_model/adapter.py', 2022, ROOT/'baseline_receipt_2022.json')
    style = p.read(ROOT/'FIGURE_COVERAGE_AND_STYLE.json')
    assert style['current_figure_pairs']==18
    assert all(row['years']==[2019,2020,2021,2022] for row in style['figures'])
    status = {'status': '2022_REAL_ENGINE_VERIFIED_OTHER_YEARS_PENDING', 'date': '2026-10-18',
              'software_tests_passed': result.testsRun,
              'design_groups': 12, 'design_rows': rows, 'design_rows_are_not_model_outputs': True,
              'all_design_hashes_and_Saltelli_blocks_checked': True,
              'CSV_exactly_matches_NPY': True, 'N128_prefix_of_N512_checked': True,
              'paper_pages': len(pdf.pages), 'paper_embedded_figures': len(word.inline_shapes),
              'current_figure_pairs': len(list((ROOT / 'figures').glob('*.png'))),
              'real_2022_baseline_benchmark_passed': True, 'real_model_Sobol_executed': False,
              'real_model_NSGAIII_executed': False,
              'missing_2022_model_source': False, 'original_model_pending_years': [2019,2020,2021],
              'all_current_figures_include_four_years': True,
              'missing_2022_phase2_checkpoint': False, 'phase2_2022_retained_rows': 58784,
              'reference_PDF_absent': True}
    p.write(ROOT / 'DELIVERY_VALIDATION.json', status)
    print(json.dumps(status, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    verify()
