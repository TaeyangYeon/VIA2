"""Export router — SVG, PDF, and parameter sheet export from execution results."""
from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from backend.services.execution_manager import get_manager

router = APIRouter()


class SVGExportRequest(BaseModel):
    execution_id: str


class ParameterExportRequest(BaseModel):
    execution_id: str


async def _get_result_data(execution_id: str) -> dict:
    status = await get_manager().get_status(execution_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Execution not found")
    result_data = status.get("result")
    if result_data is None:
        raise HTTPException(status_code=404, detail="Execution result not available")
    return result_data


def _extract_svg(result_data: dict) -> str:
    svg = result_data.get("blueprint_svg")
    if not svg:
        bp = result_data.get("blueprint")
        if isinstance(bp, dict):
            svg = bp.get("svg_content")
    return svg or ""


@router.post("/svg")
async def export_svg(request: SVGExportRequest) -> Response:
    result_data = await _get_result_data(request.execution_id)
    svg_content = _extract_svg(result_data)
    if not svg_content:
        raise HTTPException(status_code=404, detail="No blueprint SVG in execution result")
    return Response(
        content=svg_content.encode("utf-8"),
        media_type="image/svg+xml",
        headers={"Content-Disposition": 'attachment; filename="blueprint.svg"'},
    )


@router.post("/pdf")
async def export_pdf(request: SVGExportRequest) -> Response:
    result_data = await _get_result_data(request.execution_id)
    svg_content = _extract_svg(result_data)
    if not svg_content:
        raise HTTPException(status_code=404, detail="No blueprint SVG in execution result")
    pdf_bytes = _svg_to_pdf(svg_content)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="blueprint.pdf"'},
    )


def _svg_to_pdf(svg_content: str) -> bytes:
    """Convert SVG to PDF, falling back to text-embedded PDF if svglib unavailable."""
    try:
        import os
        import tempfile

        from svglib.svglib import svg2rlg  # type: ignore
        from reportlab.graphics import renderPDF

        with tempfile.NamedTemporaryFile(suffix=".svg", delete=False, mode="w") as f:
            f.write(svg_content)
            tmp = f.name
        try:
            drawing = svg2rlg(tmp)
            if drawing is None:
                raise ValueError("svg2rlg returned None")
            buf = BytesIO()
            renderPDF.drawToFile(drawing, buf)
            return buf.getvalue()
        finally:
            os.unlink(tmp)
    except Exception:
        return _svg_to_pdf_fallback(svg_content)


def _svg_to_pdf_fallback(svg_content: str) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, Preformatted, SimpleDocTemplate

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("VIA2 Blueprint", styles["Title"]),
        Paragraph("SVG Blueprint Content:", styles["Heading2"]),
        Preformatted(svg_content[:3000], styles["Code"]),
    ]
    doc.build(story)
    return buf.getvalue()


@router.post("/parameters")
async def export_parameters(request: ParameterExportRequest) -> dict[str, Any]:
    result_data = await _get_result_data(request.execution_id)

    parameter_sheets = result_data.get("parameter_sheets")
    if parameter_sheets is None:
        parameter_sheets = result_data.get("parameter_sheet")
    if parameter_sheets is None:
        raise HTTPException(status_code=404, detail="No parameter sheets in execution result")

    return {
        "execution_id": request.execution_id,
        "parameter_sheets": parameter_sheets,
        "exported_at": datetime.now(timezone.utc).isoformat(),
    }
