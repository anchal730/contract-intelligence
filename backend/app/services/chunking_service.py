from langchain_text_splitters import RecursiveCharacterTextSplitter


def chunk_document_pages(
    pages: list[tuple[int, str]],
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> list[dict]:

    if not pages:
        return []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=[
            "\n\n",
            "\n",
            ". ",
            " ",
            "",
        ],
    )

    chunks = []

    for page_number, text in pages:

        if not text or not text.strip():
            continue

        page_chunks = splitter.split_text(text)

        for chunk_text in page_chunks:

            if not chunk_text.strip():
                continue

            chunks.append(
                {
                    "text": chunk_text.strip(),
                    "start_page": page_number,
                    "end_page": page_number,
                }
            )

    return chunks