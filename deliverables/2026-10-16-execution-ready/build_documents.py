from pathlib import Path
import document_renderer as renderer
ROOT=Path(__file__).resolve().parent
if __name__=='__main__':
    for name in ['paper_framework_execution_ready','review_update_20261018']:
        renderer.pdf_report((ROOT/(name+'.md')).read_text(),ROOT/(name+'.pdf'))
        renderer.word_report(name+'.md')
