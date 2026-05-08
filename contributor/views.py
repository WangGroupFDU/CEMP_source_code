from django.shortcuts import render
from django.http import JsonResponse 
import os
from django.conf import settings 
import logging



logger = logging.getLogger(__name__)

def contributor_view(request) -> str:
    try:
        
        logger.info(f"Received request for contributor display: {request}")
        
        
        response = render(request, "contributor/contributor_display.html")
        
        
        logger.info("Contributor display page rendered successfully.")
        
        return response
    
    except Exception as e:
        
        logger.error(f"Error rendering contributor display page: {e}")
        
        
        
        return render(request, "error.html", {"message": "Failed to load the contributor display page."})


