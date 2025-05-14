from fastapi import APIRouter, HTTPException, Depends, Request, status, Response
from fastapi.responses import JSONResponse, FileResponse
from typing import List, Dict, Optional, Any
import logging
from datetime import datetime
from pydantic import BaseModel, Field

# Configure logging
logger = logging.getLogger(__name__)

# Create router with proper prefix
router = APIRouter(
    prefix="/api/health-exploration",  # Added prefix to match API path
    tags=["Health Exploration"]
)

# Define models
class PaperCategory(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    count: int = 0

class Paper(BaseModel):
    id: str
    title: str
    authors: List[str]
    publication_date: datetime
    journal: str
    abstract: str
    categories: List[str]
    keywords: List[str] = []
    is_featured: bool = False
    download_url: str
    views: int = 0
    downloads: int = 0

class PaperListResponse(BaseModel):
    papers: List[Paper]
    total: int
    page: int
    per_page: int
    total_pages: int

# Mock database (replace with actual database implementation)
# Sample paper categories
paper_categories = [
    PaperCategory(id="1", name="Cardiology", description="Studies related to heart and cardiovascular systems", count=5),
    PaperCategory(id="2", name="Neurology", description="Studies related to the nervous system", count=3),
    PaperCategory(id="3", name="Oncology", description="Studies related to cancer research", count=7),
    PaperCategory(id="4", name="Infectious Diseases", description="Studies related to infectious diseases", count=4),
    PaperCategory(id="5", name="Public Health", description="Studies related to public health initiatives", count=2),
]

# Sample papers
sample_papers = [
    Paper(
        id="1",
        title="Advances in Cardiovascular Disease Prevention",
        authors=["John Doe", "Jane Smith"],
        publication_date=datetime(2023, 5, 15),
        journal="Journal of Cardiology",
        abstract="This paper explores the latest advances in preventing cardiovascular diseases through lifestyle modifications and pharmacological interventions.",
        categories=["1"],  # Cardiology
        keywords=["cardiovascular", "prevention", "lifestyle", "pharmacology"],
        is_featured=True,
        download_url="/api/health-exploration/papers/1/download",
        views=250,
        downloads=120
    ),
    Paper(
        id="2",
        title="Understanding Alzheimer's Disease Progression",
        authors=["Emily Johnson", "Michael Brown"],
        publication_date=datetime(2023, 6, 22),
        journal="Neurology Today",
        abstract="A comprehensive review of the latest research on Alzheimer's disease progression and potential treatment approaches.",
        categories=["2"],  # Neurology
        keywords=["alzheimer's", "neurodegeneration", "cognitive decline", "treatment"],
        is_featured=True,
        download_url="/api/health-exploration/papers/2/download",
        views=180,
        downloads=95
    ),
    Paper(
        id="3",
        title="Impact of COVID-19 on Mental Health",
        authors=["Sarah Wilson", "Robert Davis"],
        publication_date=datetime(2023, 3, 10),
        journal="Journal of Public Health",
        abstract="This study examines the psychological impact of the COVID-19 pandemic on different population groups.",
        categories=["4", "5"],  # Infectious Diseases, Public Health
        keywords=["COVID-19", "mental health", "pandemic", "psychological impact"],
        is_featured=True,
        download_url="/api/health-exploration/papers/3/download",
        views=320,
        downloads=210
    ),
    Paper(
        id="4",
        title="Novel Approaches to Cancer Immunotherapy",
        authors=["David Lee", "Susan Miller"],
        publication_date=datetime(2023, 7, 5),
        journal="Cancer Research",
        abstract="This paper discusses innovative approaches to cancer immunotherapy that have shown promising results in clinical trials.",
        categories=["3"],  # Oncology
        keywords=["cancer", "immunotherapy", "clinical trials", "oncology"],
        is_featured=False,
        download_url="/api/health-exploration/papers/4/download",
        views=150,
        downloads=80
    ),
    Paper(
        id="5",
        title="Genetic Factors in Heart Disease",
        authors=["Linda Wilson", "Thomas Clark"],
        publication_date=datetime(2023, 4, 18),
        journal="Genetics in Medicine",
        abstract="An analysis of genetic factors that contribute to the development and progression of heart disease.",
        categories=["1"],  # Cardiology
        keywords=["genetics", "heart disease", "risk factors", "genomics"],
        is_featured=False,
        download_url="/api/health-exploration/papers/5/download",
        views=130,
        downloads=65
    )
]

# Cache dictionaries for faster lookups
paper_dict = {paper.id: paper for paper in sample_papers}

# API Endpoints

@router.get("/papers", response_model=PaperListResponse, tags=["Papers"])
async def get_papers(
    page: int = 1, 
    per_page: int = 10, 
    category: Optional[str] = None, 
    search: Optional[str] = None
):
    """
    Get a list of all papers, with optional filtering by category or search term.
    
    Parameters:
    - page: Current page number (default: 1)
    - per_page: Number of items per page (default: 10)
    - category: Filter by category ID
    - search: Search term for paper title or abstract
    """
    logger.info(f"Retrieving papers with page={page}, per_page={per_page}, category={category}, search={search}")
    
    # Filter papers based on query parameters
    filtered_papers = sample_papers
    
    # Filter by category if provided
    if category:
        filtered_papers = [p for p in filtered_papers if category in p.categories]
    
    # Filter by search term if provided
    if search:
        search_lower = search.lower()
        filtered_papers = [
            p for p in filtered_papers 
            if search_lower in p.title.lower() or search_lower in p.abstract.lower() or 
            any(search_lower in keyword.lower() for keyword in p.keywords)
        ]
    
    # Calculate pagination
    total = len(filtered_papers)
    total_pages = (total + per_page - 1) // per_page  # Ceiling division
    
    # Ensure valid page number
    if page < 1:
        page = 1
    elif page > total_pages and total_pages > 0:
        page = total_pages
    
    # Calculate slice indices for pagination
    start_idx = (page - 1) * per_page
    end_idx = min(start_idx + per_page, total)
    
    # Get paginated papers
    paginated_papers = filtered_papers[start_idx:end_idx]
    
    return PaperListResponse(
        papers=paginated_papers,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages
    )

@router.get("/papers/{paper_id}", response_model=Paper, tags=["Papers"])
async def get_paper_details(paper_id: str):
    """
    Get detailed information about a specific paper by ID.
    
    Parameters:
    - paper_id: The ID of the paper
    """
    logger.info(f"Retrieving details for paper ID: {paper_id}")
    
    # Check if paper exists
    if paper_id not in paper_dict:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paper with ID {paper_id} not found"
        )
    
    # Increment view count (in a real app, this would be a database update)
    paper = paper_dict[paper_id]
    paper.views += 1
    
    return paper

@router.get("/papers/{paper_id}/download", tags=["Papers"])
async def download_paper(paper_id: str):
    """
    Download a specific paper by ID.
    
    Parameters:
    - paper_id: The ID of the paper
    """
    logger.info(f"Processing download request for paper ID: {paper_id}")
    
    # Check if paper exists
    if paper_id not in paper_dict:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paper with ID {paper_id} not found"
        )
    
    # Increment download count (in a real app, this would be a database update)
    paper = paper_dict[paper_id]
    paper.downloads += 1
    
    # In a real implementation, you would return the actual file
    # For this example, we'll return a JSON response
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "message": f"Download initiated for paper: {paper.title}",
            "paper_id": paper_id,
            "downloads": paper.downloads,
            "note": "In a real implementation, this would return a file download."
        }
    )
    
    # Real implementation would be something like:
    # file_path = f"path/to/papers/{paper_id}.pdf"
    # return FileResponse(
    #     path=file_path,
    #     media_type="application/pdf",
    #     filename=f"{paper.title.replace(' ', '_')}.pdf"
    # )

@router.get("/papers/categories", response_model=List[PaperCategory], tags=["Categories"])
async def get_paper_categories():
    """
    Get a list of all paper categories.
    """
    logger.info("Retrieving all paper categories")
    return paper_categories

@router.get("/papers/featured", response_model=List[Paper], tags=["Featured"])
async def get_featured_papers(limit: int = 3):
    """
    Get a list of featured papers.
    
    Parameters:
    - limit: Maximum number of featured papers to return (default: 3)
    """
    logger.info(f"Retrieving featured papers with limit={limit}")
    
    featured_papers = [p for p in sample_papers if p.is_featured]
    
    # Return only the specified number of featured papers
    return featured_papers[:limit]
