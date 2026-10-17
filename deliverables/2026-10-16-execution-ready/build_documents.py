"""Render the delivered current Markdown and referenced scientific figures."""
from pathlib import Path
import document_renderer as renderer
ROOT=Path(__file__).resolve().parent
if __name__=='__main__':
    for name in ['paper_framework_execution_ready','review_update_20261017']:
        text=(ROOT/(name+'.md')).read_text(encoding='utf-8')
        renderer.pdf_report(text,ROOT/(name+'.pdf'))
        renderer.word_report(name+'.md')
    print('Rendered current Word/PDF from included Markdown and figures.')
