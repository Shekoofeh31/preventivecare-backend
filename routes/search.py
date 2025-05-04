from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# Models
class SearchResult(BaseModel):
    id: str
    title: str
    summary: str
    content_type: str  # article, resource, topic, etc.
    url: str
    relevance_score: float
    highlights: Optional[List[str]] = None

class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    total_results: int
    categories: Optional[Dict[str, int]] = None
    suggested_queries: Optional[List[str]] = None

# Mock search database with some sample content
search_content = [
    {
        "id": "article1",
        "title": "اهمیت غربالگری سرطان روده بزرگ",
        "summary": "بررسی اهمیت غربالگری منظم برای تشخیص زودهنگام سرطان روده بزرگ",
        "content": "غربالگری منظم سرطان روده بزرگ می‌تواند به تشخیص زودهنگام و افزایش شانس درمان کمک کند. توصیه می‌شود افراد بالای ۴۵ سال آزمایش‌های غربالگری را انجام دهند.",
        "content_type": "article",
        "url": "/articles/article1",
        "categories": ["سرطان", "غربالگری", "سلامت گوارش"],
        "tags": ["سرطان روده بزرگ", "کولونوسکوپی", "آزمایش مدفوع"]
    },
    {
        "id": "article2",
        "title": "راهنمای جامع فشار خون بالا",
        "summary": "همه چیز درباره پیشگیری و مدیریت فشار خون بالا",
        "content": "فشار خون بالا یکی از عوامل خطر اصلی برای بیماری‌های قلبی است. تغییرات سبک زندگی مانند ورزش منظم، کاهش مصرف نمک و حفظ وزن سالم می‌تواند به کنترل فشار خون کمک کند.",
        "content_type": "article",
        "url": "/articles/article2",
        "categories": ["قلب و عروق", "فشار خون"],
        "tags": ["فشار خون بالا", "سبک زندگی سالم", "رژیم غذایی"]
    },
    {
        "id": "resource1",
        "title": "ویدیو آموزشی: نحوه اندازه‌گیری صحیح فشار خون",
        "summary": "آموزش گام به گام اندازه‌گیری دقیق فشار خون در منزل",
        "content": "در این ویدیو آموزشی، نحوه صحیح اندازه‌گیری فشار خون در منزل را یاد می‌گیرید. اندازه‌گیری منظم فشار خون به شما کمک می‌کند تا از وضعیت سلامت خود آگاه باشید.",
        "content_type": "resource",
        "url": "/resources/resource1",
        "categories": ["آموزش", "فشار خون"],
        "tags": ["سنجش فشار خون", "خودمراقبتی"]
    },
    {
        "id": "topic1",
        "title": "پیشگیری از بیماری‌های قلبی",
        "summary": "اطلاعات جامع درباره پیشگیری از بیماری‌های قلبی",
        "content": "بیماری‌های قلبی یکی از علل اصلی مرگ‌ومیر در جهان هستند. با رعایت اصول پیشگیرانه می‌توان خطر ابتلا به این بیماری‌ها را کاهش داد.",
        "content_type": "topic",
        "url": "/health-topics/topic1",
        "categories": ["قلب و عروق"],
        "tags": ["پیشگیری", "بیماری قلبی", "سلامت قلب"]
    }
]

# Simple search function that checks for keyword matches
def search_content_by_query(query: str, content_type: Optional[str] = None, category: Optional[str] = None):
    """
    Search through content using a simple keyword matching algorithm.
    Returns a list of matching items with relevance scores.
    """
    results = []
    query = query.lower()
    
    for item in search_content:
        # Skip if content type filter is applied and doesn't match
        if content_type and item["content_type"] != content_type:
            continue
            
        # Skip if category filter is applied and doesn't match
        if category and category not in item.get("categories", []):
            continue
        
        # Calculate a simple relevance score
        relevance_score = 0
        highlights = []
        
        # Check title for query match
        if query in item["title"].lower():
            relevance_score += 10
            highlights.append(item["title"])
            
        # Check summary for query match
        if query in item["summary"].lower():
            relevance_score += 5
            highlights.append(item["summary"])
            
        # Check content for query match
        if query in item["content"].lower():
            relevance_score += 3
            # Extract a snippet around the match
            content_lower = item["content"].lower()
            start_idx = max(0, content_lower.find(query) - 20)
            end_idx = min(len(item["content"]), content_lower.find(query) + len(query) + 20)
            snippet = f"...{item['content'][start_idx:end_idx]}..."
            highlights.append(snippet)
            
        # Check tags for query match
        for tag in item.get("tags", []):
            if query in tag.lower():
                relevance_score += 3
                highlights.append(f"Tag: {tag}")
                
        # If we found any matches, add to results
        if relevance_score > 0:
            results.append({
                "id": item["id"],
                "title": item["title"],
                "summary": item["summary"],
                "content_type": item["content_type"],
                "url": item["url"],
                "relevance_score": relevance_score,
                "highlights": highlights
            })
    
    # Sort by relevance score (highest first)
    results.sort(key=lambda x: x["relevance_score"], reverse=True)
    return results

def get_suggested_queries(query: str) -> List[str]:
    """Generate suggested related queries based on the original query."""
    suggestions = []
    
    # Add some hardcoded suggestions based on common keywords
    if "فشار خون" in query:
        suggestions.extend(["کاهش فشار خون", "داروهای فشار خون", "رژیم غذایی فشار خون"])
    elif "سرطان" in query:
        suggestions.extend(["غربالگری سرطان", "پیشگیری از سرطان", "علائم هشدار سرطان"])
    elif "قلب" in query:
        suggestions.extend(["سلامت قلب", "بیماری های قلبی", "ورزش برای قلب"])
    
    # Add some general health suggestions
    suggestions.extend(["پیشگیری", "سبک زندگی سالم", "تغذیه سالم"])
    
    # Return only unique suggestions (up to 5)
    unique_suggestions = list(set(suggestions))[:5]
    return unique_suggestions

def count_results_by_category(results: List[Dict[str, Any]]) -> Dict[str, int]:
    """Count the number of search results by category."""
    category_counts = {}
    
    for item in search_content:
        for category in item.get("categories", []):
            if category not in category_counts:
                category_counts[category] = 0
    
    for result in results:
        item_id = result["id"]
        original_item = next((item for item in search_content if item["id"] == item_id), None)
        if original_item:
            for category in original_item.get("categories", []):
                if category in category_counts:
                    category_counts[category] += 1
    
    return category_counts

@router.get("/", response_model=SearchResponse)
async def search(
    q: str = Query(..., min_length=1, description="Search query"),
    content_type: Optional[str] = Query(None, description="Filter by content type"),
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(10, ge=1, le=50, description="Number of results to return")
):
    """
    Search the website for content matching the given query.
    Optionally filter results by content type or category.
    """
    if not q:
        raise HTTPException(status_code=400, detail="Search query cannot be empty")
    
    # Log the search query for analytics
    logger.info(f"Search query: {q}, filters: type={content_type}, category={category}")
    
    # Perform the search
    results = search_content_by_query(q, content_type, category)
    
    # Count results by category
    category_counts = count_results_by_category(results)
    
    # Generate suggested queries
    suggested_queries = get_suggested_queries(q)
    
    # Apply limit to results
    paginated_results = results[:limit]
    
    # Build the response
    response = SearchResponse(
        query=q,
        results=paginated_results,
        total_results=len(results),
        categories=category_counts,
        suggested_queries=suggested_queries
    )
    
    return response

@router.get("/popular")
async def get_popular_searches():
    """Get a list of popular search terms."""
    # In a real application, this would be based on analytics data
    popular_searches = [
        "فشار خون",
        "دیابت",
        "کلسترول",
        "سرطان سینه",
        "کرونا",
        "واکسن آنفولانزا",
        "ویتامین دی",
        "خواب سالم",
        "کاهش وزن",
        "استرس"
    ]
    
    return {"popular_searches": popular_searches}

@router.get("/autocomplete")
async def get_search_autocomplete(
    q: str = Query(..., min_length=1, description="Partial search query")
):
    """
    Get autocomplete suggestions for a partial search query.
    Returns a list of suggested search terms that start with the given query.
    """
    if not q:
        return {"suggestions": []}
    
    # In a real application, these would come from a database or search engine
    all_terms = [
        "فشار خون بالا",
        "فشار خون پایین",
        "فشار خون در بارداری",
        "سرطان سینه",
        "سرطان روده بزرگ",
        "سرطان پوست",
        "دیابت نوع ۱",
        "دیابت نوع ۲",
        "دیابت بارداری",
        "کلسترول بالا",
        "کلسترول خوب و بد",
        "کمبود ویتامین دی",
        "ویتامین دی در بارداری",
        "خواب کافی",
        "اختلالات خواب",
        "کاهش وزن سالم",
        "کاهش وزن سریع",
        "استرس و اضطراب",
        "مدیریت استرس"
    ]
    
    # Filter terms that start with the query (case-insensitive)
    q_lower = q.lower()
    matching_terms = [term for term in all_terms if term.lower().startswith(q_lower)]
    
    # Sort by length (shorter first) and limit to 10 suggestions
    matching_terms.sort(key=len)
    return {"suggestions": matching_terms[:10]}