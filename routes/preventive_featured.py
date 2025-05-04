from fastapi import APIRouter, HTTPException, Query, Path
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# Models
class Article(BaseModel):
    id: str
    title: str
    summary: str
    content: str
    author: str
    published_date: str
    image_url: Optional[str] = None
    categories: List[str]
    tags: List[str]
    read_time: int  # in minutes

class PreventiveResource(BaseModel):
    id: str
    title: str
    description: str
    resource_type: str  # article, video, infographic, etc.
    url: str
    categories: List[str]
    tags: List[str]

class Category(BaseModel):
    id: str
    name: str
    description: str
    parent_id: Optional[str] = None

# Mock database
articles_db = [
    {
        "id": "article1",
        "title": "اهمیت غربالگری سرطان روده بزرگ",
        "summary": "بررسی اهمیت غربالگری منظم برای تشخیص زودهنگام سرطان روده بزرگ",
        "content": "محتوای مقاله در مورد غربالگری سرطان روده بزرگ...",
        "author": "دکتر محمد حسینی",
        "published_date": "2023-10-15",
        "image_url": "/images/colon-cancer-screening.jpg",
        "categories": ["سرطان", "غربالگری", "سلامت گوارش"],
        "tags": ["سرطان روده بزرگ", "کولونوسکوپی", "آزمایش مدفوع"],
        "read_time": 8
    },
    {
        "id": "article2",
        "title": "راهنمای جامع فشار خون بالا",
        "summary": "همه چیز درباره پیشگیری و مدیریت فشار خون بالا",
        "content": "محتوای مقاله در مورد فشار خون بالا...",
        "author": "دکتر زهرا کریمی",
        "published_date": "2023-09-22",
        "image_url": "/images/hypertension-guide.jpg",
        "categories": ["قلب و عروق", "فشار خون"],
        "tags": ["فشار خون بالا", "سبک زندگی سالم", "رژیم غذایی"],
        "read_time": 12
    }
]

resources_db = [
    {
        "id": "resource1",
        "title": "ویدیو آموزشی: نحوه اندازه‌گیری صحیح فشار خون",
        "description": "آموزش گام به گام اندازه‌گیری دقیق فشار خون در منزل",
        "resource_type": "video",
        "url": "/resources/blood-pressure-measurement-video",
        "categories": ["آموزش", "فشار خون"],
        "tags": ["سنجش فشار خون", "خودمراقبتی"]
    },
    {
        "id": "resource2",
        "title": "اینفوگرافیک: علائم هشدار دهنده سکته مغزی",
        "description": "تشخیص سریع علائم سکته مغزی می‌تواند زندگی‌بخش باشد",
        "resource_type": "infographic",
        "url": "/resources/stroke-warning-signs-infographic",
        "categories": ["مغز و اعصاب", "اورژانس"],
        "tags": ["سکته مغزی", "علائم هشدار"]
    }
]

categories_db = [
    {
        "id": "cat1",
        "name": "قلب و عروق",
        "description": "مطالب مرتبط با سلامت قلب و سیستم گردش خون",
        "parent_id": None
    },
    {
        "id": "cat2",
        "name": "فشار خون",
        "description": "مطالب مرتبط با پیشگیری و مدیریت فشار خون",
        "parent_id": "cat1"
    },
    {
        "id": "cat3",
        "name": "سرطان",
        "description": "مطالب مرتبط با پیشگیری، تشخیص زودهنگام و درمان سرطان",
        "parent_id": None
    },
    {
        "id": "cat4",
        "name": "تغذیه",
        "description": "مطالب مرتبط با تغذیه سالم و رژیم غذایی",
        "parent_id": None
    }
]

# Endpoints for Articles
@router.get("/articles", response_model=List[Article])
async def get_articles(
    category: Optional[str] = Query(None, description="Filter by category"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    limit: int = Query(10, ge=1, le=50, description="Number of articles to return"),
    offset: int = Query(0, ge=0, description="Number of articles to skip")
):
    """Get a list of preventive healthcare articles with optional filtering."""
    filtered_articles = articles_db
    
    # Apply category filter if provided
    if category:
        filtered_articles = [
            article for article in filtered_articles
            if category in article["categories"]
        ]
    
    # Apply tag filter if provided
    if tag:
        filtered_articles = [
            article for article in filtered_articles
            if tag in article["tags"]
        ]
    
    # Sort by published date (newest first)
    filtered_articles.sort(key=lambda x: x["published_date"], reverse=True)
    
    # Apply pagination
    paginated_articles = filtered_articles[offset:offset + limit]
    
    return paginated_articles

@router.get("/articles/{article_id}", response_model=Article)
async def get_article(article_id: str = Path(..., description="The ID of the article to get")):
    """Get a specific article by its ID."""
    for article in articles_db:
        if article["id"] == article_id:
            return article
    
    raise HTTPException(status_code=404, detail=f"Article with ID {article_id} not found")

@router.get("/featured-articles", response_model=List[Article])
async def get_featured_articles(limit: int = Query(3, ge=1, le=10)):
    """Get a list of featured articles for homepage display."""
    # In a real application, this might have specific criteria for "featured" status
    # Here we'll just return the most recent articles
    sorted_articles = sorted(articles_db, key=lambda x: x["published_date"], reverse=True)
    return sorted_articles[:limit]

# Endpoints for Resources
@router.get("/resources", response_model=List[PreventiveResource])
async def get_resources(
    category: Optional[str] = Query(None, description="Filter by category"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    limit: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0)
):
    """Get a list of preventive healthcare resources with optional filtering."""
    filtered_resources = resources_db
    
    # Apply category filter if provided
    if category:
        filtered_resources = [
            resource for resource in filtered_resources
            if category in resource["categories"]
        ]
    
    # Apply resource type filter if provided
    if resource_type:
        filtered_resources = [
            resource for resource in filtered_resources
            if resource["resource_type"] == resource_type
        ]
    
    # Apply pagination
    paginated_resources = filtered_resources[offset:offset + limit]
    
    return paginated_resources

@router.get("/resources/{resource_id}", response_model=PreventiveResource)
async def get_resource(resource_id: str = Path(..., description="The ID of the resource to get")):
    """Get a specific resource by its ID."""
    for resource in resources_db:
        if resource["id"] == resource_id:
            return resource
    
    raise HTTPException(status_code=404, detail=f"Resource with ID {resource_id} not found")

# Endpoints for Categories
@router.get("/categories", response_model=List[Category])
async def get_categories(parent_id: Optional[str] = Query(None, description="Filter by parent category ID")):
    """Get a list of content categories with optional parent filtering."""
    if parent_id:
        filtered_categories = [
            category for category in categories_db
            if category["parent_id"] == parent_id
        ]
        return filtered_categories
    
    return categories_db

@router.get("/categories/{category_id}", response_model=Category)
async def get_category(category_id: str = Path(..., description="The ID of the category to get")):
    """Get a specific category by its ID."""
    for category in categories_db:
        if category["id"] == category_id:
            return category
    
    raise HTTPException(status_code=404, detail=f"Category with ID {category_id} not found")

@router.get("/categories/{category_id}/subcategories", response_model=List[Category])
async def get_subcategories(category_id: str = Path(..., description="The parent category ID")):
    """Get all subcategories for a specific parent category."""
    filtered_subcategories = [
        category for category in categories_db
        if category["parent_id"] == category_id
    ]
    
    return filtered_subcategories

# Health knowledge base endpoints
@router.get("/health-topics")
async def get_health_topics():
    """Get a list of common health topics for preventive care."""
    topics = [
        {
            "id": "topic1",
            "name": "پیشگیری از بیماری‌های قلبی",
            "description": "اطلاعات جامع درباره پیشگیری از بیماری‌های قلبی",
            "related_categories": ["cat1"]
        },
        {
            "id": "topic2",
            "name": "سبک زندگی سالم",
            "description": "راهنمای جامع برای داشتن سبک زندگی سالم",
            "related_categories": ["cat4"]
        },
        {
            "id": "topic3",
            "name": "غربالگری‌های ضروری",
            "description": "آشنایی با آزمایشات غربالگری مهم در سنین مختلف",
            "related_categories": ["cat3"]
        }
    ]
    
    return {"topics": topics}

@router.get("/health-calendar")
async def get_health_calendar():
    """Get a calendar of recommended health screenings by age and gender."""
    calendar = {
        "screenings": [
            {
                "name": "فشار خون",
                "frequency": "سالانه",
                "recommended_ages": "۱۸ سال به بالا",
                "gender": "همه"
            },
            {
                "name": "کلسترول",
                "frequency": "هر ۴-۶ سال",
                "recommended_ages": "۲۰ سال به بالا",
                "gender": "همه"
            },
            {
                "name": "ماموگرافی",
                "frequency": "هر ۱-۲ سال",
                "recommended_ages": "۴۰-۷۵ سال",
                "gender": "زنان"
            },
            {
                "name": "کولونوسکوپی",
                "frequency": "هر ۱۰ سال",
                "recommended_ages": "۴۵-۷۵ سال",
                "gender": "همه"
            }
        ]
    }
    
    return calendar

@router.get("/preventive-tips")
async def get_preventive_tips(category: Optional[str] = None):
    """Get daily preventive health tips, optionally filtered by category."""
    tips = [
        {
            "id": "tip1",
            "title": "کاهش مصرف نمک",
            "content": "محدود کردن مصرف نمک به کمتر از ۵ گرم در روز می‌تواند به کاهش فشار خون کمک کند.",
            "category": "فشار خون"
        },
        {
            "id": "tip2",
            "title": "ورزش منظم",
            "content": "حداقل ۱۵۰ دقیقه فعالیت بدنی متوسط در هفته برای سلامت قلب مفید است.",
            "category": "قلب"
        },
        {
            "id": "tip3",
            "title": "مصرف میوه و سبزیجات",
            "content": "روزانه حداقل ۵ وعده میوه و سبزیجات مصرف کنید.",
            "category": "تغذیه"
        }
    ]
    
    if category:
        filtered_tips = [tip for tip in tips if tip["category"] == category]
        return {"tips": filtered_tips}
    
    return {"tips": tips}