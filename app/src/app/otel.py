# OTel config
import json
import time
from typing import Sequence

from opentelemetry import trace
from opentelemetry.sdk.trace import ReadableSpan, TracerProvider
from opentelemetry.sdk.trace.export import (
    ConsoleSpanExporter,
    SimpleSpanProcessor,
    SpanExporter,
    SpanExportResult,
)
from pydantic_ai import Agent

SHOW_COMPLETIONS = True
SHOW_TOOL_RESULTS = True


def short(value, max_len=500):
    """Pretty-print a value but never let it take over the terminal."""
    if value is None:
        return None

    if not isinstance(value, str):
        value = json.dumps(value, ensure_ascii=False, default=str)

    if len(value) > max_len:
        return value[:max_len] + f"... ({len(value)} chars)"

    return value


class PrettySpanExporter(SpanExporter):
    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        for span in spans:
            self._print_span(span)

        return SpanExportResult.SUCCESS

    def _print_span(self, span: ReadableSpan):
        attrs = dict(span.attributes or {})

        duration_ms = (
            (span.end_time - span.start_time) / 1_000_000
            if span.end_time and span.start_time
            else 0
        )

        name = span.name

        # ---- identify the kind of operation ----------------------------

        is_tool = "tool" in name.lower()
        is_model = (
            "model" in name.lower()
            or "chat" in name.lower()
            or "generation" in name.lower()
        )

        # ---- duration ---------------------------------------------------

        if duration_ms >= 1000:
            duration = f"{duration_ms / 1000:.2f}s"
        else:
            duration = f"{duration_ms:.0f}ms"

        # ---- tool -------------------------------------------------------

        if is_tool:
            print(f"  🔧 {name}  [{duration}]")

            # Attribute names can vary somewhat between instrumentation
            # versions, so check the useful candidates.
            args = first(
                attrs,
                "gen_ai.tool.call.arguments",
                "gen_ai.tool.arguments",
                "tool.arguments",
            )

            if args is not None:
                print(f"     args: {short(args)}")

            if SHOW_TOOL_RESULTS:
                result = first(
                    attrs,
                    "gen_ai.tool.call.result",
                    "gen_ai.tool.result",
                    "tool.result",
                )

                if result is not None:
                    print(f"     result: {short(result, max_len=2000)}")

        # ---- model ------------------------------------------------------

        elif is_model:
            model = first(
                attrs,
                "gen_ai.request.model",
                "gen_ai.response.model",
            )

            print(
                f"  🤖 {name}"
                + (f" ({model})" if model else "")
                + f"  [{duration}]"
            )

            # Token usage
            input_tokens = first(
                attrs,
                "gen_ai.usage.input_tokens",
                "gen_ai.usage.prompt_tokens",
            )

            output_tokens = first(
                attrs,
                "gen_ai.usage.output_tokens",
                "gen_ai.usage.completion_tokens",
            )

            total_tokens = first(
                attrs,
                "gen_ai.usage.total_tokens",
            )

            if input_tokens is not None or output_tokens is not None:
                parts = []

                if input_tokens is not None:
                    parts.append(f"in={input_tokens}")

                if output_tokens is not None:
                    parts.append(f"out={output_tokens}")

                if total_tokens is not None:
                    parts.append(f"total={total_tokens}")

                print(f"     tokens: {' '.join(parts)}")

            if SHOW_COMPLETIONS:
                output = first(
                    attrs,
                    "gen_ai.output.messages",
                )
                if output is not None:
                    print(output)

                reasoning = first(
                    attrs,
                    "gen_ai.response.reasoning",
                    "gen_ai.reasoning",
                    "gen_ai.response.reasoning_content",
                )

                if reasoning is not None:
                    print(f"     reasoning: {short(reasoning, max_len=1000)}")

                completion = first(
                    attrs,
                    "gen_ai.response.content",
                    "gen_ai.completion",
                    "gen_ai.response.text",
                )

                if completion is not None:
                    print(f"     completion: {short(completion, max_len=1000)}")


        # ---- everything else -------------------------------------------

        else:
            print(f"  ▶ {name}  [{duration}]")

    def shutdown(self):
        pass


def first(attrs, *keys):
    for key in keys:
        if key in attrs:
            return attrs[key]
    return None


def instrument_all():
    # Send every finished span to stdout
    provider = TracerProvider()
    provider.add_span_processor(
        SimpleSpanProcessor(PrettySpanExporter())
    )
    trace.set_tracer_provider(provider)

    # Instrument all Pydantic AI agents
    Agent.instrument_all()


#class PrettySpanExporter(SpanExporter):
#    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
#        for span in spans:
#            attrs = dict(span.attributes or {})
#            name = span.name
#
#            # Print only the interesting attributes
#            interesting = {
#                k: v
#                for k, v in attrs.items()
#                if any(x in k.lower() for x in (
#                    "tool",
#                    "gen_ai",
#                    "model",
#                ))
#            }
#
#            print(f"\n  {name}")
#
#            for key, value in interesting.items():
#                # Keep tool arguments/results readable
#                if isinstance(value, (dict, list)):
#                    value = json.dumps(value, ensure_ascii=False)
#
#                print(f"    {key}: {value}")
#
#        return SpanExportResult.SUCCESS
#
#    def shutdown(self) -> None:
#        pass
