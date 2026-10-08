import json
import os
import re
from typing import Any

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

from app.schemas.contract_extraction import ContractExtraction
from app.services.hybrid_search_service import HybridSearchService


load_dotenv()


class ContractExtractionService:
    """Extract structured contract information from indexed document chunks."""

    MAX_CONTEXT_CHARS = 18000

    SINGLE_FIELDS = (
        "contract_title",
        "effective_date",
        "expiry_date",
        "duration",
        "scope_of_work",
        "payment_terms",
        "dispute_resolution",
        "force_majeure",
        "governing_law",
    )

    LIST_FIELDS = (
        "parties",
        "termination_clauses",
        "obligations",
        "penalties",
        "important_dates",
    )

    def __init__(self) -> None:
        self.hybrid_search = HybridSearchService()

        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError(
                "GROQ_API_KEY is missing. Check your backend .env file."
            )

        self.llm = ChatGroq(
            model="openai/gpt-oss-120b",
            temperature=0,
            max_tokens=8192,
            api_key=api_key,
            model_kwargs={"response_format": {"type": "json_object"}},
        )

        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
You are a precise contract information extraction system.

Use ONLY the supplied contract context. Never invent, infer, or assume facts
that are not supported by the context. If a single-value field is not found,
return an object with value=null, evidence=null, and source_pages=[].
If a list field has no supported items, return [].

Preserve names, dates, amounts, durations, conditions, exceptions, and clause
distinctions. Do not merge distinct termination mechanisms. Source page numbers
must be supported by the supplied page labels.

Return exactly one valid JSON object, with no Markdown or explanatory text.

Required top-level fields:
contract_title, parties, effective_date, expiry_date, duration, scope_of_work,
payment_terms, termination_clauses, obligations, penalties, dispute_resolution,
force_majeure, governing_law, important_dates.

Each single-value field must be an object containing:
value, evidence, source_pages.

Each item in a list field must also be an object containing:
value, evidence, source_pages.

Use strings or null for value/evidence. Use an array of integer page numbers
for source_pages. Do not omit any required top-level field.
""",
                ),
                (
                    "human",
                    """
Extract the required contract information from the context below.

CONTRACT CONTEXT:
{context}
""",
                ),
            ]
        )

    @staticmethod
    def _optional_text(value: Any) -> str | None:
        
        """Normalize empty placeholders to None."""
        if value is None:
            
            return None

        if isinstance(value, str):
            
            value = value.strip()

            if value.casefold() in {"", "[]", "{}", "null", "none"}:
                
                return None

            return value

        if isinstance(value, (int, float, bool)):
            
            return str(value)
   
        if isinstance(value, (dict, list)):
            
            return json.dumps(value, ensure_ascii=False)

        return str(value)

    @staticmethod
    def _normalize_pages(pages: Any) -> list[int]:
        """Convert page references such as 3, '3', '3-5', or '3, 5' to integers."""
        if pages is None:
            return []
        if not isinstance(pages, list):
            pages = [pages]

        normalized: list[int] = []
        for page in pages:
            if isinstance(page, int) and not isinstance(page, bool):
                if page > 0:
                    normalized.append(page)
            elif isinstance(page, str):
                # Extract each number from labels such as "Pages 3-5".
                normalized.extend(
                    int(number)
                    for number in re.findall(r"\d+", page)
                    if int(number) > 0
                )

        # Remove duplicates while preserving order.
        return list(dict.fromkeys(normalized))

    @classmethod
    def _normalize_item(cls, item: Any) -> dict[str, Any]:
        """Normalize one extraction item to the Pydantic schema shape."""
        if isinstance(item, str):
            item = {"value": item}
        elif not isinstance(item, dict):
            item = {}

        return {
            "value": cls._optional_text(item.get("value")),
            "evidence": cls._optional_text(item.get("evidence")),
            "source_pages": cls._normalize_pages(item.get("source_pages", [])),
        }

    @classmethod
    def _parse_response(cls, response_text: str) -> dict[str, Any]:
        """Parse model JSON, normalize inconsistent fields, and validate it."""
        if not isinstance(response_text, str) or not response_text.strip():
            raise ValueError("The model returned an empty response.")

        cleaned = response_text.strip()
        cleaned = re.sub(
            r"\A```(?:json)?\s*",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )
        cleaned = re.sub(r"\s*```\Z", "", cleaned)

        # If the model accidentally adds text around the JSON, isolate the
        # outermost JSON object before parsing.
        if not cleaned.startswith("{"):
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start >= 0 and end > start:
                cleaned = cleaned[start : end + 1]

        data = json.loads(cleaned)
        if not isinstance(data, dict):
            raise ValueError("The model response must be a JSON object.")

        # Add missing fields so validation can report a consistent structure.
        for field in cls.SINGLE_FIELDS:
            data.setdefault(
                field,
                {"value": None, "evidence": None, "source_pages": []},
            )
        
        
        # Normalize list fields and remove empty placeholder items.
        for field in cls.LIST_FIELDS:
            value = data.get(field)

            if value is None:
                value = []
            elif not isinstance(value, list):
                value = [value]

            normalized_items: list[dict[str, Any]] = []
            for raw_item in value:
                item = cls._normalize_item(raw_item)
                item_value = item["value"]

                # Some model responses incorrectly encode a list of values as
                # a JSON array inside one item's value string. Expand it.
                if isinstance(item_value, str) and item_value.startswith("["):
                    try:
                        decoded_value = json.loads(item_value)
                    except (json.JSONDecodeError, TypeError):
                        decoded_value = None

                    if isinstance(decoded_value, list):
                        for entry in decoded_value:
                            clean_entry = cls._optional_text(entry)
                            if clean_entry is not None:
                                normalized_items.append({
                                    "value": clean_entry,
                                    "evidence": item["evidence"],
                                    "source_pages": item["source_pages"],
                                })
                        continue

                if item_value is not None:
                    normalized_items.append(item)

            # List items must have an actual extracted value.
            data[field] = normalized_items

        # Normalize single-value fields. If the model returned multiple items
        # for a single field, combine them rather than silently dropping data.
        for field in cls.SINGLE_FIELDS:
            value = data.get(field)

            if isinstance(value, list):
                items = [cls._normalize_item(item) for item in value]
                values = [
                    item["value"] for item in items
                    if item["value"]
                ]
                evidence = [
                    item["evidence"] for item in items
                    if item["evidence"]
                ]
                pages = [
                    page for item in items for page in item["source_pages"]
                ]
                data[field] = {
                    "value": "\n".join(values) or None,
                    "evidence": "\n".join(evidence) or None,
                    "source_pages": cls._normalize_pages(pages),
                }
            else:
                data[field] = cls._normalize_item(value)

        extraction = ContractExtraction.model_validate(data)
        return extraction.model_dump()

    @staticmethod
    def _response_text(response: Any) -> str:
        """Read the textual response returned by LangChain."""
        content = getattr(response, "content", response)
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            # Some chat model integrations return a list of content blocks.
            text_parts = []
            for block in content:
                if isinstance(block, str):
                    text_parts.append(block)
                elif isinstance(block, dict) and isinstance(block.get("text"), str):
                    text_parts.append(block["text"])
            return "\n".join(text_parts)
        return str(content) if content is not None else ""

    def _build_context(self, document_version_id: str) -> str:
        """Retrieve relevant chunks and build a context within the size limit."""
        queries = [
            "contract title parties client consultant agreement",
            "effective date commencement date contract duration expiry",
            "scope of work services responsibilities deliverables",
            "payment terms fees invoices milestones payment schedule",
            "termination clauses notice period breach non-performance",
            "obligations duties responsibilities reporting deadlines",
            "penalties damages deductions fines",
            "dispute resolution arbitration jurisdiction court",
            "force majeure events circumstances",
            "governing law applicable law",
            "important dates deadlines milestones contract period",
        ]

        chunks_by_index: dict[Any, dict[str, Any]] = {}
        for query in queries:
            results = self.hybrid_search.search(
                document_version_id=document_version_id,
                query=query,
                top_k=2,
            ) or []

            for result in results:
                chunk_index = result.get("chunk_index")
                if chunk_index is not None:
                    chunks_by_index.setdefault(chunk_index, result)

        if not chunks_by_index:
            raise ValueError(
                "No contract chunks were found for this document version. "
                "Confirm that document processing completed successfully."
            )

        try:
            ordered_chunks = sorted(
                chunks_by_index.values(),
                key=lambda item: int(item.get("chunk_index", 0)),
            )
        except (TypeError, ValueError):
            ordered_chunks = list(chunks_by_index.values())

        context_parts: list[str] = []
        context_length = 0

        for chunk in ordered_chunks:
            chunk_text = str(chunk.get("text") or "").strip()
            if not chunk_text:
                continue

            start_page = chunk.get("start_page", "?")
            end_page = chunk.get("end_page", start_page)
            formatted_chunk = (
                f"Chunk: {chunk.get('chunk_index', '?')}\n"
                f"Pages: {start_page}-{end_page}\n\n"
                f"{chunk_text}\n"
            )

            remaining = self.MAX_CONTEXT_CHARS - context_length
            if remaining <= 0:
                break
            if len(formatted_chunk) > remaining:
                formatted_chunk = formatted_chunk[:remaining]

            context_parts.append(formatted_chunk)
            context_length += len(formatted_chunk)

        context = "\n\n".join(context_parts).strip()
        if not context:
            raise ValueError(
                "Retrieved chunks did not contain any readable contract text."
            )
        return context

    def extract_contract(self, document_version_id: str) -> dict[str, Any]:
        """Retrieve contract text and return validated structured extraction."""
        if not document_version_id or not document_version_id.strip():
            raise ValueError("document_version_id must not be empty.")

        context = self._build_context(document_version_id.strip())
        messages = self.prompt.format_messages(context=context)
        response = self.llm.invoke(messages)
        response_text = self._response_text(response)

        try:
            return self._parse_response(response_text)
        except Exception as first_error:
            # One repair attempt handles malformed/truncated JSON and minor
            # schema-shape mistakes without hiding the original error.
            repair_prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        """
Correct the previous contract extraction response and return a complete,
valid JSON object only. Use exactly these top-level fields:
contract_title, parties, effective_date, expiry_date, duration, scope_of_work,
payment_terms, termination_clauses, obligations, penalties, dispute_resolution,
force_majeure, governing_law, important_dates.

Single-value fields must be objects with value, evidence, source_pages.
List fields must be arrays of such objects. source_pages must be an array of
integer page numbers. Use null for unknown single values and [] for unknown
lists. Preserve the information supported by the context; do not invent facts.
""",
                    ),
                    (
                        "human",
                        """
Original contract context:
{context}

Previous response that failed validation:
{bad_response}

Return the corrected JSON object now.
""",
                    ),
                ]
            )

            repair_messages = repair_prompt.format_messages(
                context=context,
                bad_response=response_text[:12000],
            )

            try:
                repaired_response = self.llm.invoke(repair_messages)
                repaired_text = self._response_text(repaired_response)
                return self._parse_response(repaired_text)
            except Exception as second_error:
                raise ValueError(
                    "Contract extraction failed validation after one repair "
                    f"attempt. Initial error: {first_error}. "
                    f"Repair error: {second_error}"
                ) from second_error
