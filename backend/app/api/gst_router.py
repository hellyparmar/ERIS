"""
GST (Goods and Services Tax) REST API Endpoints

Provides endpoints for:
- GSTR-1 return generation (outward supplies)
- GSTR-3B return generation (monthly returns)
- GST report downloads
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from io import StringIO

from app.services.gst_service import GSTService
from app.core.security import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/gst",
    tags=["gst"]
)


# Pydantic models
class GSTCalculationRequest(BaseModel):
    """Request to calculate GST"""
    amount: float = Field(..., gt=0, description="Amount before GST in INR")
    category: str = Field(..., description="Product category")
    is_interstate: bool = Field(default=False, description="True for inter-state sales")


class GSTCalculationResponse(BaseModel):
    """GST calculation response"""
    base_amount: float
    gst_rate_percent: str
    cgst_amount: float
    sgst_amount: float
    igst_amount: float
    total_gst: float
    total_with_gst: float


class GSTR1ReportResponse(BaseModel):
    """GSTR-1 report response"""
    return_type: str
    outlet_id: str
    period: str
    summary_by_rate: Dict[str, Any]
    total_summary: Dict[str, Any]
    invoice_count: int


class GSTR3BReportResponse(BaseModel):
    """GSTR-3B report response"""
    return_type: str
    outlet_id: str
    period: str
    outward_supplies: Dict[str, float]
    tax_liability: Dict[str, float]
    net_payable: Dict[str, float]


# Dependency
def get_gst_service() -> GSTService:
    """Get GST service instance"""
    return GSTService()


@router.post(
    "/calculate",
    response_model=GSTCalculationResponse,
    summary="Calculate GST Amount",
    description="Calculate CGST, SGST, or IGST amount for a given product and amount"
)
async def calculate_gst(
    request: GSTCalculationRequest,
    gst_service: GSTService = Depends(get_gst_service),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Calculate GST amount for a product.
    
    Returns CGST/SGST for intra-state or IGST for inter-state sales.
    
    Example:
    ```
    POST /api/v1/gst/calculate
    {
        "amount": 1000,
        "category": "Beverages",
        "is_interstate": false
    }
    ```
    
    Response:
    ```
    {
        "base_amount": 1000,
        "gst_rate_percent": "12%",
        "cgst_amount": 60,
        "sgst_amount": 60,
        "igst_amount": 0,
        "total_gst": 120,
        "total_with_gst": 1120
    }
    ```
    """
    try:
        result = gst_service.calculate_gst(
            request.amount,
            request.category,
            request.is_interstate
        )
        
        return {
            'base_amount': result['base_amount'],
            'gst_rate_percent': result['gst_rate_percent'],
            'cgst_amount': result['cgst_amount'],
            'sgst_amount': result['sgst_amount'],
            'igst_amount': result['igst_amount'],
            'total_gst': result['total_gst'],
            'total_with_gst': result['total_with_gst'],
        }
    except Exception as e:
        logger.error(f"Error calculating GST: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating GST: {str(e)}"
        )


@router.get(
    "/gstr1",
    summary="Get GSTR-1 Report",
    description="Generate GSTR-1 return (outward supplies) for a month"
)
async def get_gstr1_report(
    outlet_id: str = Query(..., description="Outlet ID"),
    month: int = Query(..., ge=1, le=12, description="Month (1-12)"),
    year: int = Query(..., ge=2000, description="Year (YYYY)"),
    gst_service: GSTService = Depends(get_gst_service),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get GSTR-1 return summary for a specific month.
    
    GSTR-1 shows:
    - Outward supplies (sales) details
    - Breakdown by GST rate slab
    - Total taxable value and taxes
    - Invoice-wise details
    
    Query Parameters:
    - outlet_id: Outlet identifier (required)
    - month: Month number 1-12 (required)
    - year: Year in YYYY format (required)
    
    Example:
    ```
    GET /api/v1/gst/gstr1?outlet_id=OUT001&month=4&year=2024
    ```
    
    Response includes:
    - Summary grouped by GST rate slab (5%, 12%, 18%, 28%)
    - Total taxable value, CGST, SGST totals
    - Individual invoice details
    """
    try:
        report = gst_service.generate_gstr1_summary(outlet_id, month, year)
        return report
    except Exception as e:
        logger.error(f"Error generating GSTR-1: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating GSTR-1 report: {str(e)}"
        )


@router.get(
    "/gstr3b",
    summary="Get GSTR-3B Report",
    description="Generate GSTR-3B return (monthly return) for a month"
)
async def get_gstr3b_report(
    outlet_id: str = Query(..., description="Outlet ID"),
    month: int = Query(..., ge=1, le=12, description="Month (1-12)"),
    year: int = Query(..., ge=2000, description="Year (YYYY)"),
    gst_service: GSTService = Depends(get_gst_service),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get GSTR-3B return summary for a specific month.
    
    GSTR-3B shows:
    - Outward supplies (from GSTR-1)
    - Tax liability
    - Input Tax Credit (ITC) eligibility
    - Net tax payable
    
    Query Parameters:
    - outlet_id: Outlet identifier (required)
    - month: Month number 1-12 (required)
    - year: Year in YYYY format (required)
    
    Example:
    ```
    GET /api/v1/gst/gstr3b?outlet_id=OUT001&month=4&year=2024
    ```
    
    Response includes:
    - Outward supplies summary
    - Tax liability (CGST, SGST, IGST)
    - ITC eligibility (input tax credit)
    - Net payable amount
    - Summary by GST rate slab
    """
    try:
        report = gst_service.generate_gstr3b_summary(outlet_id, month, year)
        return report
    except Exception as e:
        logger.error(f"Error generating GSTR-3B: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating GSTR-3B report: {str(e)}"
        )


@router.get(
    "/gstr1/download",
    summary="Download GSTR-1 Report as CSV",
    description="Download GSTR-1 report in CSV format"
)
async def download_gstr1_csv(
    outlet_id: str = Query(..., description="Outlet ID"),
    month: int = Query(..., ge=1, le=12, description="Month (1-12)"),
    year: int = Query(..., ge=2000, description="Year (YYYY)"),
    gst_service: GSTService = Depends(get_gst_service),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Download GSTR-1 report as CSV file.
    
    Query Parameters:
    - outlet_id: Outlet identifier (required)
    - month: Month number 1-12 (required)
    - year: Year in YYYY format (required)
    """
    try:
        report = gst_service.generate_gstr1_summary(outlet_id, month, year)
        csv_content = gst_service.export_to_csv(report, 'GSTR-1')
        
        return {
            'filename': f'GSTR-1_{outlet_id}_{year}-{month:02d}.csv',
            'content': csv_content,
            'content_type': 'text/csv',
        }
    except Exception as e:
        logger.error(f"Error downloading GSTR-1: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error downloading GSTR-1 report: {str(e)}"
        )


@router.get(
    "/gstr3b/download",
    summary="Download GSTR-3B Report as CSV",
    description="Download GSTR-3B report in CSV format"
)
async def download_gstr3b_csv(
    outlet_id: str = Query(..., description="Outlet ID"),
    month: int = Query(..., ge=1, le=12, description="Month (1-12)"),
    year: int = Query(..., ge=2000, description="Year (YYYY)"),
    gst_service: GSTService = Depends(get_gst_service),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Download GSTR-3B report as CSV file.
    
    Query Parameters:
    - outlet_id: Outlet identifier (required)
    - month: Month number 1-12 (required)
    - year: Year in YYYY format (required)
    """
    try:
        report = gst_service.generate_gstr3b_summary(outlet_id, month, year)
        csv_content = gst_service.export_to_csv(report, 'GSTR-3B')
        
        return {
            'filename': f'GSTR-3B_{outlet_id}_{year}-{month:02d}.csv',
            'content': csv_content,
            'content_type': 'text/csv',
        }
    except Exception as e:
        logger.error(f"Error downloading GSTR-3B: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error downloading GSTR-3B report: {str(e)}"
        )


@router.get(
    "/categories",
    summary="Get GST Rate Categories",
    description="Get all available product categories and their GST rates"
)
async def get_gst_categories(
    gst_service: GSTService = Depends(get_gst_service),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get all product categories and their GST rates.
    
    Returns a dictionary mapping category names to GST rates.
    
    Example Response:
    ```
    {
        "Beverages": "12%",
        "Snacks": "12%",
        "Dairy": "5%",
        "Bakery": "5%",
        "Personal Care": "18%",
        "Cleaning": "18%",
        "Frozen Foods": "12%",
        "Staples": "5%"
    }
    ```
    """
    try:
        categories = {
            cat: f"{int(rate*100)}%"
            for cat, rate in gst_service.GST_RATES.items()
        }
        return categories
    except Exception as e:
        logger.error(f"Error retrieving GST categories: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving GST categories: {str(e)}"
        )
