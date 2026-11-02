from ingestion.base import BaseConnector
from ingestion.openalex import OpenAlexConnector
from ingestion.dblp import DBLPConnector
from ingestion.arxiv import ArXivConnector
from ingestion.crossref import CrossrefConnector
from ingestion.faculty_scraper import FacultyScraper

__all__ = [
    "BaseConnector", 
    "OpenAlexConnector", 
    "DBLPConnector", 
    "ArXivConnector", 
    "CrossrefConnector",
    "FacultyScraper"
]
