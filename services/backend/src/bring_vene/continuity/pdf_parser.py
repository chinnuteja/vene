"""A bounded, secret-free subprocess for machine-readable synthetic PDFs."""
import io,json,logging,sys

def main():
    try:
        logging.getLogger('pypdf').setLevel(logging.CRITICAL)
        from pypdf import PdfReader,overwrite_configuration
        overwrite_configuration(maximum_declared_stream_length=1_000_000,array_based_stream_maximum_output_length=262144,
            zlib_maximum_output_length=262144,lzw_maximum_output_length=262144,run_length_maximum_output_length=262144,
            stream_decoding_work_maximum_length=1_000_000,page_tree_maximum_entries=200,page_tree_maximum_depth=20,
            xform_maximum_invocations_per_extraction=100,disable_legacy_handling=True)
        raw=sys.stdin.buffer.read(250001)
        if len(raw)>250000 or not raw.startswith(b'%PDF-'):raise ValueError()
        reader=PdfReader(io.BytesIO(raw),strict=True)
        if reader.is_encrypted or len(reader.pages)>10:raise ValueError()
        pages=[];total=0
        for index,page in enumerate(reader.pages):
            text=page.extract_text() or '';total+=len(text)
            if total>12000:raise ValueError()
            pages.append({'page':index+1,'text':text})
        if not any(len(p['text'].strip())>=3 for p in pages):raise ValueError()
        print(json.dumps({'pages':pages},ensure_ascii=True))
    except Exception:
        print('{"error":"unsupported_pdf"}');return 1
    return 0

if __name__=='__main__':sys.exit(main())
